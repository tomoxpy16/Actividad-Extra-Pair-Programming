"""Reloj inyectable.

El desfase (offset) permite "viajar en el tiempo" durante una demo para provocar
retrasos sin esperar horas reales. Se guarda en la base de datos para que la API
y el worker del monitor vean la misma hora simulada.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


class Clock:
    def __init__(self, tz: str = "America/Bogota", offset_minutes: int = 0) -> None:
        self.tz = ZoneInfo(tz)
        self.offset_minutes = offset_minutes

    def now(self) -> datetime:
        return datetime.now(self.tz).replace(second=0, microsecond=0) + timedelta(minutes=self.offset_minutes)


class FixedClock(Clock):
    """Reloj fijo para pruebas."""

    def __init__(self, fixed: datetime) -> None:
        super().__init__(str(fixed.tzinfo) if fixed.tzinfo else "America/Bogota")
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed
