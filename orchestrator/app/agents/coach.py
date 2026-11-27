"""CoachAgent: acompaña al usuario con el siguiente paso concreto.

Usa el LLM (si existe) solo para redactar un mensaje breve y amable; los datos
(qué tarea sigue y a qué hora) los calcula de forma determinista.
"""
from __future__ import annotations

from datetime import datetime

from app.agents.base import Agent
from app.domain.models import AgentEvent, Task, TaskStatus
from app.infrastructure.llm import LLMProvider, LLMUnavailable

SYSTEM = ("Eres el CoachAgent de Kairos. Escribe UNA o DOS frases en español, cálidas y concretas, "
          "para motivar al usuario a ejecutar su siguiente tarea. No uses emojis ni listas.")


class CoachAgent(Agent):
    name = "CoachAgent"

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    @staticmethod
    def _template(current: Task | None, nxt: Task | None, remaining_today: int, replanned: bool) -> str:
        parts = []
        if replanned:
            parts.append("Reorganicé tu día para absorber el retraso; no pasa nada, seguimos.")
        if current:
            parts.append(f"Estás en «{current.title}» hasta las {current.scheduled_end:%H:%M}.")
        if nxt:
            parts.append(f"Lo siguiente es «{nxt.title}» a las {nxt.scheduled_start:%H:%M} ({nxt.estimated_minutes} min).")
        if remaining_today:
            parts.append(f"Te quedan {remaining_today} bloque(s) hoy.")
        return " ".join(parts) or "No tienes tareas pendientes. ¡Buen trabajo!"

    def run(self, tasks: list[Task], now: datetime, replanned: bool = False) -> list[AgentEvent]:
        current = next((t for t in tasks if t.status == TaskStatus.IN_PROGRESS), None)
        upcoming = sorted((t for t in tasks if t.status == TaskStatus.SCHEDULED and t.scheduled_start),
                          key=lambda t: t.scheduled_start)
        nxt = upcoming[0] if upcoming else None
        remaining_today = sum(1 for t in upcoming if t.scheduled_start.date() == now.date())
        message = self._template(current, nxt, remaining_today, replanned)
        if self.llm.enabled and nxt:
            try:
                message = self.llm.complete_text(SYSTEM, f"Datos: {message}\nHora actual: {now:%H:%M}.")[:400]
            except LLMUnavailable:
                pass
        return [self.event(message, "info", {"next_task_id": nxt.id if nxt else None})]
