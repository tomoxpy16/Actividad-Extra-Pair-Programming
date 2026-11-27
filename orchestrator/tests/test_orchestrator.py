"""Prueba de integración: grafo completo + repositorio sobre SQLite en memoria."""
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from app.infrastructure.db import Base, make_session_factory
from app.infrastructure.llm import NullProvider
from app.orchestration.orchestrator import Orchestrator


def make_orchestrator() -> Orchestrator:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Orchestrator(make_session_factory(engine), NullProvider(), "America/Bogota")


def test_flujo_plan_retraso_y_replanificacion():
    orch = make_orchestrator()
    result = orch.plan("estudiar cálculo 2 horas, ir al gimnasio y llamar a mi mamá")
    assert len(result["new_task_ids"]) == 3
    agents = [e["agent"] for e in result["events"]]
    assert agents[:1] == ["Orchestrator"]
    assert {"IntakeAgent", "PrioritizerAgent", "SchedulerAgent", "CoachAgent"} <= set(agents)

    state = orch.snapshot()
    assert all(t["status"] == "scheduled" for t in state["tasks"])

    # Simulamos que pasan 5 horas sin que el usuario haga nada -> el monitor replanifica
    after = orch.advance_clock(5 * 60)
    assert after["delays"], "el monitor debió detectar retrasos"
    state = orch.snapshot()
    assert state["clock_offset_minutes"] == 300
    assert all(t["scheduled_start"] >= state["now"] for t in state["tasks"])
    assert state["stats"]["delays"] >= 1


def test_iniciar_y_completar_tarea():
    orch = make_orchestrator()
    task_id = orch.plan("leer 30 minutos")["new_task_ids"][0]
    orch.task_action(task_id, "start")
    assert orch.snapshot()["tasks"][0]["status"] == "in_progress"
    orch.task_action(task_id, "complete")
    assert orch.snapshot()["stats"]["done"] == 1
