"""PrioritizerAgent: puntúa cada tarea abierta y la ubica en la matriz de Eisenhower.

Es determinista a propósito: la aritmética de prioridades debe ser explicable y
reproducible (el LLM se reserva para entender lenguaje, no para hacer cuentas).
"""
from __future__ import annotations

from datetime import datetime

from app.agents.base import Agent
from app.domain.models import AgentEvent, Quadrant, Task, TaskStatus

W_IMPORTANCE = 0.5
W_URGENCY = 0.4


def urgency_of(task: Task, now: datetime) -> tuple[float, str]:
    """Urgencia 0..1 a partir de la holgura (tiempo restante - duración)."""
    target = task.fixed_start or task.deadline
    if target is None:
        return (0.6, "sin fecha pero marcada urgente") if task.urgent_hint else (0.1, "sin fecha límite")
    hours_left = (target - now).total_seconds() / 3600
    slack = hours_left - (0 if task.fixed_start else task.estimated_minutes / 60)
    if slack <= 0:
        value = 1.0
    else:
        value = 1 / (1 + slack / 12)  # 0 h -> 1.0 · 12 h -> 0.5 · 48 h -> 0.2
    if task.urgent_hint:
        value = max(value, 0.6)
    label = "hora fija" if task.fixed_start else "vence"
    when = f"en {hours_left:.1f} h" if hours_left >= 0 else f"hace {-hours_left:.1f} h"
    return value, f"{label} {when}"


class PrioritizerAgent(Agent):
    name = "PrioritizerAgent"

    def score(self, task: Task, now: datetime) -> Task:
        importance = (task.importance - 1) / 4
        urgency, why = urgency_of(task, now)
        delay_boost = min(0.3, 0.1 * task.delay_count)
        quick_win = 0.05 if task.estimated_minutes <= 15 else 0.0
        task.priority_score = round(100 * (W_IMPORTANCE * importance + W_URGENCY * urgency + delay_boost + quick_win), 1)

        is_important = task.importance >= 4
        is_urgent = urgency >= 0.5
        task.quadrant = (
            Quadrant.Q1 if is_important and is_urgent else
            Quadrant.Q2 if is_important else
            Quadrant.Q3 if is_urgent else
            Quadrant.Q4
        ).value
        parts = [f"importancia {task.importance}/5", why]
        if task.delay_count:
            parts.append(f"reprogramada {task.delay_count} {'vez' if task.delay_count == 1 else 'veces'}")
        if quick_win:
            parts.append("victoria rápida")
        task.rationale = " · ".join(parts)
        return task

    def run(self, tasks: list[Task], now: datetime) -> tuple[list[Task], list[AgentEvent]]:
        open_tasks = [t for t in tasks if t.status != TaskStatus.DONE]
        for t in open_tasks:
            self.score(t, now)
        if not open_tasks:
            return tasks, []
        ranked = sorted(open_tasks, key=lambda t: -t.priority_score)
        top = ", ".join(f"«{t.title}» ({t.priority_score:.0f}, {t.quadrant})" for t in ranked[:3])
        q1 = sum(1 for t in open_tasks if t.quadrant == Quadrant.Q1.value)
        msg = f"Prioricé {len(open_tasks)} tarea(s). Top: {top}."
        if q1:
            msg += f" {q1} en el cuadrante «Hacer ahora»."
        return tasks, [self.event(msg, "info", {"ranking": [t.id for t in ranked]})]
