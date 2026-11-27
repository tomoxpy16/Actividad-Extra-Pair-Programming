"""Grafo de orquestación (LangGraph).

El estado compartido (`KairosState`) viaja por los nodos; cada nodo delega en un
agente especializado y devuelve solo lo que cambió. Los eventos se acumulan con un
reductor (`operator.add`), formando la bitácora de la ejecución.

            ┌──────── plan ───────► intake ──┐
  START ──► router ── replan ──────────────► prioritize ─► schedule ─► coach ─► END
            └──────── monitor ─► monitor ──┘ (solo si hay retrasos; si no, END)
"""
from __future__ import annotations

import operator
from datetime import datetime
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.coach import CoachAgent
from app.agents.intake import IntakeAgent
from app.agents.monitor import MonitorAgent
from app.agents.prioritizer import PrioritizerAgent
from app.agents.scheduler import SchedulerAgent
from app.domain.models import AgentEvent, Task


class KairosState(TypedDict, total=False):
    mode: str                     # plan | replan | monitor
    now: datetime
    input_text: str
    tasks: list[Task]
    new_task_ids: list[str]
    delays: list[dict[str, Any]]
    events: Annotated[list[AgentEvent], operator.add]


def build_graph(intake: IntakeAgent, prioritizer: PrioritizerAgent, scheduler: SchedulerAgent,
                monitor: MonitorAgent, coach: CoachAgent):
    def intake_node(state: KairosState) -> dict:
        new_tasks, events = intake.run(state["input_text"], state["now"])
        return {"tasks": state.get("tasks", []) + new_tasks, "new_task_ids": [t.id for t in new_tasks],
                "events": events}

    def monitor_node(state: KairosState) -> dict:
        tasks, delays, events = monitor.run(state["tasks"], state["now"])
        return {"tasks": tasks, "delays": delays, "events": events}

    def prioritize_node(state: KairosState) -> dict:
        tasks, events = prioritizer.run(state["tasks"], state["now"])
        return {"tasks": tasks, "events": events}

    def schedule_node(state: KairosState) -> dict:
        tasks, events = scheduler.run(state["tasks"], state["now"])
        return {"tasks": tasks, "events": events}

    def coach_node(state: KairosState) -> dict:
        replanned = state.get("mode") in ("monitor", "replan")
        return {"events": coach.run(state["tasks"], state["now"], replanned=replanned)}

    def route_entry(state: KairosState) -> str:
        return state.get("mode", "plan")

    def after_intake(state: KairosState) -> str:
        return "prioritize" if state.get("new_task_ids") else END

    def after_monitor(state: KairosState) -> str:
        return "prioritize" if state.get("delays") else END

    g = StateGraph(KairosState)
    g.add_node("intake", intake_node)
    g.add_node("monitor", monitor_node)
    g.add_node("prioritize", prioritize_node)
    g.add_node("schedule", schedule_node)
    g.add_node("coach", coach_node)

    g.add_conditional_edges(START, route_entry, {"plan": "intake", "replan": "prioritize", "monitor": "monitor"})
    g.add_conditional_edges("intake", after_intake, {"prioritize": "prioritize", END: END})
    g.add_conditional_edges("monitor", after_monitor, {"prioritize": "prioritize", END: END})
    g.add_edge("prioritize", "schedule")
    g.add_edge("schedule", "coach")
    g.add_edge("coach", END)
    return g.compile()
