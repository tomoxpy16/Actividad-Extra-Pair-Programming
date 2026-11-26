"""Pruebas de los agentes de planificación: Prioritizer, Scheduler y Monitor (sin BD ni LLM)."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.agents.monitor import MonitorAgent
from app.agents.prioritizer import PrioritizerAgent
from app.agents.scheduler import SchedulerAgent
from app.domain.models import Quadrant, Task, TaskStatus, WorkSettings

TZ = ZoneInfo("America/Bogota")
NOW = datetime(2026, 11, 25, 9, 0, tzinfo=TZ)  # miércoles
SETTINGS = WorkSettings(work_start="08:00", work_end="20:00", break_minutes=10)


# ------------------------------------------------------------------ PrioritizerAgent
def test_prioriza_examen_cercano_sobre_tarea_sin_fecha():
    exam = Task("Estudiar", importance=5, deadline=NOW + timedelta(hours=6), estimated_minutes=120)
    movie = Task("Ver película", importance=1)
    tasks, _ = PrioritizerAgent().run([movie, exam], NOW)
    assert exam.priority_score > movie.priority_score
    assert exam.quadrant == Quadrant.Q1.value
    assert movie.quadrant == Quadrant.Q4.value


# ------------------------------------------------------------------ SchedulerAgent
def test_agenda_sin_solapamientos_y_respeta_hora_fija():
    meeting = Task("Reunión", estimated_minutes=60, fixed_start=NOW.replace(hour=10))
    a = Task("A", estimated_minutes=50, priority_score=90)
    b = Task("B", estimated_minutes=30, priority_score=50)
    tasks, _ = SchedulerAgent(SETTINGS).run([meeting, a, b], NOW)
    assert meeting.scheduled_start == NOW.replace(hour=10)
    blocks = sorted((t.scheduled_start, t.scheduled_end) for t in tasks)
    for (s1, e1), (s2, _) in zip(blocks, blocks[1:]):
        assert e1 <= s2
    assert all(t.status == TaskStatus.SCHEDULED for t in tasks)


def test_pasa_al_dia_siguiente_si_no_cabe():
    late = NOW.replace(hour=19, minute=30)
    t = Task("Largo", estimated_minutes=90, priority_score=50)
    SchedulerAgent(SETTINGS).run([t], late)
    assert t.scheduled_start == (late + timedelta(days=1)).replace(hour=8, minute=0)


def test_marca_riesgo_si_termina_despues_del_limite():
    t = Task("Informe", estimated_minutes=120, deadline=NOW + timedelta(hours=1), priority_score=80)
    _, events = SchedulerAgent(SETTINGS).run([t], NOW)
    assert t.at_risk
    assert any(e.kind == "warning" for e in events)


# ------------------------------------------------------------------ MonitorAgent
def test_detecta_tarea_no_iniciada_y_sobrecosto():
    pending = Task("No iniciada", status=TaskStatus.SCHEDULED, scheduled_start=NOW - timedelta(minutes=20),
                   scheduled_end=NOW + timedelta(minutes=20))
    running = Task("En curso", status=TaskStatus.IN_PROGRESS, scheduled_start=NOW - timedelta(hours=1),
                   scheduled_end=NOW - timedelta(minutes=10))
    _, delays, _ = MonitorAgent().run([pending, running], NOW)
    assert {d["type"] for d in delays} == {"not_started", "overrun"}
    assert pending.delay_count == running.delay_count == 1
