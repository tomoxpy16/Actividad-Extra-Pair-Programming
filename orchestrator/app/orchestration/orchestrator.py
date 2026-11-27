"""Orquestador (fachada): punto único de entrada para la API y el worker.

Responsabilidades:
- Cargar el estado compartido desde el repositorio y fijar la hora (reloj inyectable).
- Elegir la ruta del grafo (plan / replan / monitor) y ejecutarlo.
- Persistir tareas y eventos en una sola transacción, con exclusión mutua.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import timedelta
from typing import Any, Iterator

from sqlalchemy.orm import sessionmaker

from app.agents.coach import CoachAgent
from app.agents.intake import IntakeAgent
from app.agents.monitor import MonitorAgent
from app.agents.prioritizer import PrioritizerAgent
from app.agents.scheduler import SchedulerAgent
from app.domain.clock import Clock
from app.domain.models import AgentEvent, TaskStatus, WorkSettings
from app.infrastructure.llm import LLMProvider
from app.infrastructure.repository import Repository
from app.orchestration.graph import build_graph

log = logging.getLogger("kairos.orchestrator")
ORCH = "Orchestrator"
ROUTES = {
    "plan": "intake → prioritize → schedule → coach",
    "replan": "prioritize → schedule → coach",
    "monitor": "monitor → (si hay retrasos) prioritize → schedule → coach",
}


class TaskNotFound(LookupError):
    pass


class Orchestrator:
    def __init__(self, session_factory: sessionmaker, llm: LLMProvider, tz: str) -> None:
        self.session_factory = session_factory
        self.llm = llm
        self.tz = tz

    # ------------------------------------------------------------ infraestructura
    @contextmanager
    def _unit_of_work(self) -> Iterator[tuple[Repository, Clock]]:
        """Unidad de trabajo: transacción + bloqueo + reloj compartido."""
        with self.session_factory() as session, session.begin():
            repo = Repository(session, self.tz)
            repo.lock()
            yield repo, Clock(self.tz, repo.clock_offset())

    def _graph(self, settings: WorkSettings):
        return build_graph(
            IntakeAgent(self.llm, settings), PrioritizerAgent(), SchedulerAgent(settings),
            MonitorAgent(), CoachAgent(self.llm),
        )

    def _run(self, repo: Repository, clock: Clock, mode: str, text: str = "",
             pre_events: list[AgentEvent] | None = None, announce: bool = True) -> dict[str, Any]:
        now = clock.now()
        tasks = repo.list_tasks()
        result = self._graph(repo.work_settings()).invoke({
            "mode": mode, "now": now, "input_text": text, "tasks": tasks, "events": [],
        })
        events = list(pre_events or [])
        if announce or result.get("delays"):
            events.append(AgentEvent(ORCH, f"Ruta ejecutada ({mode}): {ROUTES[mode]}.", "info", {"mode": mode}))
        events += result.get("events", [])
        for i, e in enumerate(events):  # orden estable en la bitácora
            e.ts = now + timedelta(microseconds=i)
        repo.save_tasks(result.get("tasks", tasks))
        repo.add_events(events, now)
        return {"mode": mode, "new_task_ids": result.get("new_task_ids", []), "delays": result.get("delays", []),
                "events": [e.__dict__ for e in events]}

    # ------------------------------------------------------------ casos de uso
    def plan(self, text: str) -> dict[str, Any]:
        with self._unit_of_work() as (repo, clock):
            return self._run(repo, clock, "plan", text)

    def replan(self, reason: str = "solicitud del usuario") -> dict[str, Any]:
        with self._unit_of_work() as (repo, clock):
            pre = [AgentEvent(ORCH, f"Replanificación por {reason}.", "replan")]
            return self._run(repo, clock, "replan", pre_events=pre)

    def monitor_tick(self) -> dict[str, Any]:
        with self._unit_of_work() as (repo, clock):
            return self._run(repo, clock, "monitor", announce=False)

    def task_action(self, task_id: str, action: str) -> dict[str, Any]:
        with self._unit_of_work() as (repo, clock):
            task = repo.get_task(task_id)
            if task is None:
                raise TaskNotFound(task_id)
            now = clock.now()
            if action == "start":
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = now
                if not task.scheduled_start or task.scheduled_start > now or (task.scheduled_end or now) <= now:
                    task.scheduled_start = now
                    task.scheduled_end = now + timedelta(minutes=task.estimated_minutes)
                msg = f"Iniciaste «{task.title}»."
            elif action == "complete":
                task.status = TaskStatus.DONE
                task.completed_at = now
                task.started_at = task.started_at or now
                task.scheduled_end = now
                task.at_risk = False
                msg = f"Terminaste «{task.title}». ¡Bien!"
            else:
                raise ValueError(action)
            repo.save_tasks([task])
            repo.s.flush()
            return self._run(repo, clock, "replan", pre_events=[AgentEvent(ORCH, msg, "success")])

    def delete_task(self, task_id: str) -> None:
        with self._unit_of_work() as (repo, _):
            if not repo.delete_task(task_id):
                raise TaskNotFound(task_id)

    def advance_clock(self, minutes: int) -> dict[str, Any]:
        with self._unit_of_work() as (repo, _):
            offset = repo.clock_offset() + minutes
            repo.set_setting("clock_offset_minutes", str(offset))
        # el worker detectará los retrasos en su siguiente ciclo; aquí lo forzamos para la demo
        return self.monitor_tick() | {"clock_offset_minutes": offset}

    def update_settings(self, work_start: str, work_end: str, break_minutes: int) -> dict[str, Any]:
        with self._unit_of_work() as (repo, _):
            repo.set_setting("work_start", work_start)
            repo.set_setting("work_end", work_end)
            repo.set_setting("break_minutes", str(break_minutes))
        return self.replan("cambio de jornada")

    def reset(self) -> None:
        with self._unit_of_work() as (repo, _):
            repo.reset()

    def snapshot(self) -> dict[str, Any]:
        with self.session_factory() as session:
            repo = Repository(session, self.tz)
            clock = Clock(self.tz, repo.clock_offset())
            tasks = repo.list_tasks()
            settings = repo.work_settings()
            done = sum(1 for t in tasks if t.status == TaskStatus.DONE)
            return {
                "now": clock.now(),
                "clock_offset_minutes": clock.offset_minutes,
                "llm_provider": self.llm.name,
                "settings": settings.__dict__,
                "tasks": [t.__dict__ | {"status": t.status.value} for t in tasks],
                "events": repo.list_events(),
                "stats": {
                    "total": len(tasks),
                    "done": done,
                    "in_progress": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
                    "at_risk": sum(1 for t in tasks if t.at_risk and t.status != TaskStatus.DONE),
                    "delays": sum(t.delay_count for t in tasks),
                },
            }
