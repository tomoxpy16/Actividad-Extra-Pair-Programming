"""Contrato común de los agentes."""
from __future__ import annotations

from abc import ABC
from typing import Any

from app.domain.models import AgentEvent


class Agent(ABC):
    """Un agente es una unidad con una sola responsabilidad (SRP) que lee del estado
    compartido y publica eventos explicando lo que hizo (explicabilidad)."""

    name: str = "Agent"

    def event(self, message: str, kind: str = "info", payload: dict[str, Any] | None = None) -> AgentEvent:
        return AgentEvent(agent=self.name, message=message, kind=kind, payload=payload or {})
