"""Modelo de dominio de Kairos.

Objetos puros (sin dependencias de framework) que comparten todos los agentes.
Esto permite probar los agentes de forma aislada (núcleo funcional, cáscara imperativa).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"          # recién creada, sin agendar
    SCHEDULED = "scheduled"      # tiene franja asignada
    IN_PROGRESS = "in_progress"  # el usuario la inició
    DONE = "done"                # terminada
    UNSCHEDULED = "unscheduled"  # no cupo en el horizonte de planeación


class Category(str, Enum):
    ESTUDIO = "estudio"
    TRABAJO = "trabajo"
    SALUD = "salud"
    HOGAR = "hogar"
    PERSONAL = "personal"
    OTRO = "otro"


class Quadrant(str, Enum):
    """Cuadrantes de la matriz de Eisenhower."""
    Q1 = "Hacer ahora"        # importante + urgente
    Q2 = "Planificar"         # importante, no urgente
    Q3 = "Hacer rápido"       # urgente, no importante
    Q4 = "Si sobra tiempo"    # ni urgente ni importante


@dataclass
class Task:
    title: str
    estimated_minutes: int = 45
    category: str = Category.OTRO.value
    importance: int = 3                       # 1..5
    deadline: datetime | None = None
    fixed_start: datetime | None = None       # cita con hora fija ("a las 3 pm")
    urgent_hint: bool = False                 # el usuario dijo "urgente", "ya", ...
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    priority_score: float = 0.0
    quadrant: str | None = None
    rationale: str = ""
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    delay_count: int = 0
    at_risk: bool = False
    source_text: str = ""
    created_at: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.status != TaskStatus.DONE


@dataclass
class AgentEvent:
    """Mensaje publicado por un agente en el estado compartido (pizarra)."""
    agent: str
    message: str
    kind: str = "info"   # info | success | warning | replan
    payload: dict[str, Any] = field(default_factory=dict)
    ts: datetime | None = None


@dataclass
class WorkSettings:
    work_start: str = "07:00"   # HH:MM
    work_end: str = "22:00"
    break_minutes: int = 10
    horizon_days: int = 14

    def start_hm(self) -> tuple[int, int]:
        h, m = self.work_start.split(":")
        return int(h), int(m)

    def end_hm(self) -> tuple[int, int]:
        h, m = self.work_end.split(":")
        return int(h), int(m)
