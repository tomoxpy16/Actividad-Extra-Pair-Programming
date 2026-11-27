"""Repositorios (patrón Repository + Data Mapper): traducen filas <-> objetos de dominio.

Implementan el "estado compartido" (pizarra / blackboard) que leen y escriben la API
y el worker del monitor.
"""
from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.domain.models import AgentEvent, Task, TaskStatus, WorkSettings
from app.infrastructure.db import EventRow, SettingRow, TaskRow

DATE_FIELDS = ("deadline", "fixed_start", "scheduled_start", "scheduled_end", "started_at", "completed_at", "created_at")
LOCK_KEY = 4242  # clave del advisory lock de PostgreSQL


def _to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _to_local(dt: datetime | None, tz: ZoneInfo) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:  # SQLite no guarda zona horaria
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


class Repository:
    def __init__(self, session: Session, tz: str) -> None:
        self.s = session
        self.tz = ZoneInfo(tz)

    # ------------------------------------------------------------- concurrencia
    def lock(self) -> None:
        """Exclusión mutua entre API y worker mientras corre un grafo (consistencia)."""
        if self.s.bind.dialect.name == "postgresql":
            self.s.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": LOCK_KEY})

    # ------------------------------------------------------------- tareas
    def _row_to_task(self, row: TaskRow) -> Task:
        data = {f.name: getattr(row, f.name) for f in fields(Task)}
        for name in DATE_FIELDS:
            data[name] = _to_local(data[name], self.tz)
        data["status"] = TaskStatus(row.status)
        return Task(**data)

    def list_tasks(self) -> list[Task]:
        rows = self.s.scalars(select(TaskRow).order_by(TaskRow.scheduled_start.is_(None), TaskRow.scheduled_start)).all()
        return [self._row_to_task(r) for r in rows]

    def get_task(self, task_id: str) -> Task | None:
        row = self.s.get(TaskRow, task_id)
        return self._row_to_task(row) if row else None

    def save_tasks(self, tasks: list[Task]) -> None:
        for t in tasks:
            data = {f.name: getattr(t, f.name) for f in fields(Task)}
            for name in DATE_FIELDS:
                data[name] = _to_utc(data[name])
            data["status"] = t.status.value
            self.s.merge(TaskRow(**data))

    def delete_task(self, task_id: str) -> bool:
        return self.s.execute(delete(TaskRow).where(TaskRow.id == task_id)).rowcount > 0

    # ------------------------------------------------------------- eventos
    def add_events(self, events: list[AgentEvent], now: datetime) -> None:
        for e in events:
            self.s.add(EventRow(ts=_to_utc(e.ts or now), agent=e.agent, kind=e.kind, message=e.message,
                                payload=e.payload))

    def list_events(self, limit: int = 60) -> list[dict]:
        rows = self.s.scalars(select(EventRow).order_by(EventRow.id.desc()).limit(limit)).all()
        return [{"id": r.id, "ts": _to_local(r.ts, self.tz), "agent": r.agent, "kind": r.kind,
                 "message": r.message, "payload": r.payload} for r in rows]

    # ------------------------------------------------------------- ajustes
    def get_setting(self, key: str, default: str) -> str:
        row = self.s.get(SettingRow, key)
        return row.value if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.s.merge(SettingRow(key=key, value=str(value)))

    def work_settings(self) -> WorkSettings:
        d = WorkSettings()
        return WorkSettings(
            work_start=self.get_setting("work_start", d.work_start),
            work_end=self.get_setting("work_end", d.work_end),
            break_minutes=int(self.get_setting("break_minutes", str(d.break_minutes))),
        )

    def clock_offset(self) -> int:
        return int(self.get_setting("clock_offset_minutes", "0"))

    # ------------------------------------------------------------- reinicio
    def reset(self) -> None:
        self.s.execute(delete(TaskRow))
        self.s.execute(delete(EventRow))
        self.s.execute(delete(SettingRow).where(SettingRow.key == "clock_offset_minutes"))
