"""Configuración por variables de entorno (12-Factor App)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./kairos.db")
    timezone: str = os.getenv("KAIROS_TZ", "America/Bogota")
    llm_provider: str = os.getenv("LLM_PROVIDER", "rules")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://ollama:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    monitor_interval_seconds: int = int(os.getenv("MONITOR_INTERVAL_SECONDS", "15"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")


config = Config()
