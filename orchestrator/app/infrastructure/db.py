"""Esquema relacional (SQLAlchemy 2.0). PostgreSQL en Docker, SQLite en desarrollo/pruebas."""
from __future__ import annotations

import logging
import time
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

log = logging.getLogger("kairos.db")


class Base(DeclarativeBase):
    pass


class TaskRow(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(20))
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    importance: Mapped[int] = mapped_column(Integer)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fixed_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    urgent_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), index=True)
    priority_score: Mapped[float] = mapped_column(Float, default=0)
    quadrant: Mapped[str | None] = mapped_column(String(30), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, default="")
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delay_count: Mapped[int] = mapped_column(Integer, default=0)
    at_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    source_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EventRow(Base):
    __tablename__ = "agent_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    agent: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class SettingRow(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))


def make_engine(url: str, retries: int = 30) -> Engine:
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **kwargs)
    for attempt in range(1, retries + 1):  # táctica de reintento: la BD puede tardar en arrancar
        try:
            Base.metadata.create_all(engine)
            return engine
        except Exception as exc:
            log.warning("BD no disponible (intento %s/%s): %s", attempt, retries, exc)
            time.sleep(2)
    raise RuntimeError("No fue posible conectar con la base de datos")


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)
