"""API REST (adaptador de entrada). Solo traduce HTTP <-> casos de uso del orquestador."""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.orchestration.orchestrator import Orchestrator, TaskNotFound

router = APIRouter(prefix="/api")
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class PlanRequest(BaseModel):
    text: str = Field(min_length=3, max_length=4000, examples=[
        "Mañana tengo que estudiar cálculo 2 horas para el parcial del viernes, ir al gimnasio y llamar a mi mamá"])


class AdvanceRequest(BaseModel):
    minutes: int = Field(ge=1, le=24 * 60)


class SettingsRequest(BaseModel):
    work_start: str = "07:00"
    work_end: str = "22:00"
    break_minutes: int = Field(default=10, ge=0, le=60)

    @field_validator("work_start", "work_end")
    @classmethod
    def _hhmm(cls, v: str) -> str:
        if not HHMM.match(v):
            raise ValueError("Formato HH:MM")
        return v


def _orch(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


@router.get("/health")
def health(request: Request) -> dict:
    return {"status": "ok", "llm_provider": _orch(request).llm.name}


@router.get("/state")
def state(request: Request) -> dict:
    return _orch(request).snapshot()


@router.post("/plan")
def plan(body: PlanRequest, request: Request) -> dict:
    return _orch(request).plan(body.text)


@router.post("/replan")
def replan(request: Request) -> dict:
    return _orch(request).replan()


@router.post("/tasks/{task_id}/{action}")
def task_action(task_id: str, action: str, request: Request) -> dict:
    if action not in ("start", "complete"):
        raise HTTPException(404, "Acción no soportada")
    try:
        return _orch(request).task_action(task_id, action)
    except TaskNotFound:
        raise HTTPException(404, "Tarea no encontrada")


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, request: Request) -> None:
    try:
        _orch(request).delete_task(task_id)
    except TaskNotFound:
        raise HTTPException(404, "Tarea no encontrada")


@router.post("/clock/advance")
def advance_clock(body: AdvanceRequest, request: Request) -> dict:
    """Simulación para demos: adelanta el reloj compartido y fuerza un ciclo del monitor."""
    return _orch(request).advance_clock(body.minutes)


@router.put("/settings")
def update_settings(body: SettingsRequest, request: Request) -> dict:
    if body.work_start >= body.work_end:
        raise HTTPException(422, "La jornada debe terminar después de empezar")
    return _orch(request).update_settings(body.work_start, body.work_end, body.break_minutes)


@router.post("/reset", status_code=204)
def reset(request: Request) -> None:
    _orch(request).reset()
