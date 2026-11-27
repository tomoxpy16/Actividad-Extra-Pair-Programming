"""MonitorAgent: vigila la ejecución y detecta retrasos.

Lo invoca periódicamente el worker `monitor` (contenedor aparte). Si detecta
retrasos, el orquestador dispara la replanificación (Prioritizer -> Scheduler -> Coach).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.agents.base import Agent
from app.domain.models import AgentEvent, Task, TaskStatus

GRACE_MINUTES = 5


class MonitorAgent(Agent):
    name = "MonitorAgent"

    def run(self, tasks: list[Task], now: datetime) -> tuple[list[Task], list[dict], list[AgentEvent]]:
        delays: list[dict] = []
        events: list[AgentEvent] = []
        grace = timedelta(minutes=GRACE_MINUTES)
        for t in tasks:
            if t.status == TaskStatus.SCHEDULED and t.scheduled_start and now > t.scheduled_start + grace:
                late = int((now - t.scheduled_start).total_seconds() // 60)
                delays.append({"task_id": t.id, "type": "not_started", "minutes": late})
                events.append(self.event(
                    f"«{t.title}» debía empezar a las {t.scheduled_start:%H:%M} y no ha iniciado ({late} min de retraso).",
                    "warning", {"task_id": t.id}))
            elif t.status == TaskStatus.IN_PROGRESS and t.scheduled_end and now > t.scheduled_end:
                over = int((now - t.scheduled_end).total_seconds() // 60)
                delays.append({"task_id": t.id, "type": "overrun", "minutes": over})
                events.append(self.event(
                    f"«{t.title}» se pasó {over} min de lo estimado ({t.estimated_minutes} min).",
                    "warning", {"task_id": t.id}))
        for d in delays:
            task = next(t for t in tasks if t.id == d["task_id"])
            task.delay_count += 1
        return tasks, delays, events
