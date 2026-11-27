"""SchedulerAgent: construye el cronograma.

Algoritmo voraz (greedy):
1. Las tareas en curso conservan su franja (se extienden si ya se pasaron).
2. Las citas con hora fija se fijan primero.
3. El resto se ordena por prioridad (y fecha límite) y se ubica en el primer hueco
   libre dentro de la jornada, dejando un descanso entre bloques.
4. Marca en riesgo las tareas que terminarían después de su fecha límite.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.agents.base import Agent
from app.domain.models import AgentEvent, Task, TaskStatus, WorkSettings

FAR_FUTURE = datetime.max.replace(year=9000)
DAYS_ES = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")


def fmt_day(dt: datetime) -> str:
    """'mié 15:00'. No usa %a porque depende del locale (en el contenedor sale en inglés)."""
    return f"{DAYS_ES[dt.weekday()]} {dt:%H:%M}"


def ceil_to_5(dt: datetime) -> datetime:
    extra = (-dt.minute) % 5
    return (dt + timedelta(minutes=extra)).replace(second=0, microsecond=0)


class SchedulerAgent(Agent):
    name = "SchedulerAgent"

    def __init__(self, settings: WorkSettings) -> None:
        self.settings = settings

    # ----------------------------------------------------------- utilidades
    def _day_window(self, day: datetime) -> tuple[datetime, datetime]:
        sh, sm = self.settings.start_hm()
        eh, em = self.settings.end_hm()
        return day.replace(hour=sh, minute=sm), day.replace(hour=eh, minute=em)

    def _find_slot(self, cursor: datetime, minutes: int, busy: list[tuple[datetime, datetime]]) -> datetime | None:
        brk = timedelta(minutes=self.settings.break_minutes)
        dur = timedelta(minutes=minutes)
        candidate = cursor
        limit = cursor + timedelta(days=self.settings.horizon_days)
        while candidate < limit:
            start_w, end_w = self._day_window(candidate)
            window_len = end_w - start_w
            if candidate < start_w:
                candidate = start_w
            if dur <= window_len and candidate + dur > end_w:
                candidate = self._day_window(candidate + timedelta(days=1))[0]
                continue
            if candidate >= end_w:
                candidate = self._day_window(candidate + timedelta(days=1))[0]
                continue
            clash = next(((s, e) for s, e in busy if candidate < e + brk and candidate + dur + brk > s), None)
            if clash is None:
                return candidate
            candidate = ceil_to_5(clash[1] + brk)
        return None

    # ----------------------------------------------------------- ejecución
    def run(self, tasks: list[Task], now: datetime) -> tuple[list[Task], list[AgentEvent]]:
        events: list[AgentEvent] = []
        before = {t.id: t.scheduled_start for t in tasks}
        risk_before = {t.id: t.at_risk for t in tasks}
        busy: list[tuple[datetime, datetime]] = []
        anchored: list[tuple[datetime, datetime, Task]] = []  # en curso y hora fija, para detectar cruces
        cursor = ceil_to_5(now)

        # 1) en curso
        for t in tasks:
            if t.status == TaskStatus.IN_PROGRESS:
                start = t.started_at or t.scheduled_start or now
                end = t.scheduled_end or start + timedelta(minutes=t.estimated_minutes)
                if end <= now:
                    end = cursor + timedelta(minutes=max(10, min(30, t.estimated_minutes // 4)))
                t.scheduled_start, t.scheduled_end = start, end
                busy.append((start, end))
                anchored.append((start, end, t))

        # 2) hora fija
        flexible: list[Task] = []
        for t in tasks:
            if t.status in (TaskStatus.DONE, TaskStatus.IN_PROGRESS):
                continue
            if t.fixed_start is not None:
                if t.fixed_start + timedelta(minutes=5) >= now:
                    t.scheduled_start = t.fixed_start
                    t.scheduled_end = t.fixed_start + timedelta(minutes=t.estimated_minutes)
                    t.status = TaskStatus.SCHEDULED
                    other = next((o for s, e, o in anchored if t.scheduled_start < e and t.scheduled_end > s), None)
                    if other is not None:
                        events.append(self.event(
                            f"«{t.title}» ({fmt_day(t.scheduled_start)}) se cruza con «{other.title}». "
                            "Las dos tienen hora fija o están en curso: revisa cuál mover.",
                            "warning", {"task_id": t.id, "clash_with": other.id}))
                    busy.append((t.scheduled_start, t.scheduled_end))
                    anchored.append((t.scheduled_start, t.scheduled_end, t))
                    continue
                events.append(self.event(f"La hora fija de «{t.title}» ya pasó; la trato como tarea flexible.", "warning"))
                t.fixed_start = None
            flexible.append(t)

        # 3) flexibles por prioridad
        flexible.sort(key=lambda t: (-t.priority_score, t.deadline or FAR_FUTURE.replace(tzinfo=now.tzinfo),
                                     t.created_at or now))
        unscheduled = []
        for t in flexible:
            busy.sort()
            start = self._find_slot(cursor, t.estimated_minutes, busy)
            if start is None:
                t.status = TaskStatus.UNSCHEDULED
                t.scheduled_start = t.scheduled_end = None
                unscheduled.append(t)
                continue
            t.scheduled_start = start
            t.scheduled_end = start + timedelta(minutes=t.estimated_minutes)
            t.status = TaskStatus.SCHEDULED
            busy.append((t.scheduled_start, t.scheduled_end))

        # 4) riesgo de incumplimiento
        for t in tasks:
            if t.status == TaskStatus.DONE:
                continue
            t.at_risk = bool(t.deadline and t.scheduled_end and t.scheduled_end > t.deadline)
            if t.at_risk and not risk_before.get(t.id):
                events.append(self.event(
                    f"«{t.title}» terminaría {fmt_day(t.scheduled_end)} y vence {fmt_day(t.deadline)}: "
                    "está en riesgo. Considera recortarla o mover otra tarea.", "warning", {"task_id": t.id}))

        planned = [t for t in tasks if t.status in (TaskStatus.SCHEDULED, TaskStatus.IN_PROGRESS) and t.scheduled_start]
        moved = [t for t in planned if before.get(t.id) and before[t.id] != t.scheduled_start]
        if planned:
            first = min(t.scheduled_start for t in planned)
            last = max(t.scheduled_end for t in planned)
            msg = f"Cronograma listo: {len(planned)} bloque(s) entre {fmt_day(first)} y {fmt_day(last)}."
            if moved:
                msg += f" Moví {len(moved)} tarea(s) respecto al plan anterior."
            events.append(self.event(msg, "success", {"moved": [t.id for t in moved]}))
        if unscheduled:
            events.append(self.event(f"No me cupieron {len(unscheduled)} tarea(s) en los próximos "
                                     f"{self.settings.horizon_days} días.", "warning"))
        return tasks, events
