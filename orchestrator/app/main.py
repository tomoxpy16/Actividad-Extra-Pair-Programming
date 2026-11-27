"""Punto de entrada de la API (composition root: aquí se ensamblan las dependencias)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import config
from app.infrastructure.db import make_engine, make_session_factory
from app.infrastructure.llm import build_provider
from app.orchestration.orchestrator import Orchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def build_orchestrator() -> Orchestrator:
    engine = make_engine(config.database_url)
    llm = build_provider(config.llm_provider, ollama_url=config.ollama_url, ollama_model=config.ollama_model,
                         anthropic_model=config.anthropic_model, anthropic_api_key=config.anthropic_api_key)
    return Orchestrator(make_session_factory(engine), llm, config.timezone)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.orchestrator = build_orchestrator()
    yield


app = FastAPI(
    title="Kairos — Orquestador multiagente de productividad",
    version="1.0.0",
    description="Convierte lenguaje natural en tareas, las prioriza, las agenda y replanifica ante retrasos.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=config.cors_origins.split(","), allow_methods=["*"],
                   allow_headers=["*"])
app.include_router(router)
