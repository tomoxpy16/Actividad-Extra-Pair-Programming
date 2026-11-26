"""Pruebas del IntakeAgent: lenguaje natural -> tareas (sin LLM).

Escritas en modo ping-pong: una persona (o la IA) escribe la prueba que falla y la
otra escribe el código mínimo para pasarla.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.agents.intake import IntakeAgent, RuleBasedParser
from app.domain.models import WorkSettings
from app.infrastructure.llm import NullProvider

TZ = ZoneInfo("America/Bogota")
NOW = datetime(2026, 11, 25, 9, 0, tzinfo=TZ)  # miércoles
SETTINGS = WorkSettings(work_start="08:00", work_end="20:00", break_minutes=10)


@pytest.fixture
def parser():
    return RuleBasedParser(SETTINGS)


# ------------------------------------------------------------------ IntakeAgent
def test_split_en_varias_tareas(parser):
    text = "Tengo que estudiar cálculo 2 horas para el parcial del viernes, ir al gimnasio y llamar a mi mamá"
    tasks = parser.parse(text, NOW)
    assert [t.title for t in tasks] == ["Estudiar cálculo para el parcial", "Ir al gimnasio", "Llamar a mi mamá"]


def test_duracion_y_fecha_limite(parser):
    t = parser.parse("estudiar cálculo 2 horas para el viernes", NOW)[0]
    assert t.estimated_minutes == 120
    assert t.deadline == datetime(2026, 11, 27, 20, 0, tzinfo=TZ)
    assert t.category == "estudio"


def test_hora_fija(parser):
    t = parser.parse("reunión con el cliente a las 3 pm", NOW)[0]
    assert t.fixed_start == datetime(2026, 11, 25, 15, 0, tzinfo=TZ)
    assert t.importance >= 4
    assert t.estimated_minutes == 60


def test_media_hora_y_urgente(parser):
    t = parser.parse("responder correos media hora, es urgente", NOW)[0]
    assert t.estimated_minutes == 30
    assert t.urgent_hint
    assert t.deadline is not None


def test_baja_importancia(parser):
    t = parser.parse("ver una película si me da tiempo", NOW)[0]
    assert t.importance <= 2


@pytest.mark.parametrize("text, expected", [
    ("Tengo que estudiar 2 horas, luego ir al banco, después almorzar con Ana y por último revisar correos",
     ["Estudiar", "Ir al banco", "Almorzar con Ana", "Revisar correos"]),
    ("primero desayunar, luego hacer ejercicio y finalmente bañarme", ["Desayunar", "Hacer ejercicio", "Bañarme"]),
    ("ir al gimnasio, pero antes desayunar", ["Ir al gimnasio", "Desayunar"]),
    ("tengo reunión a las 10, luego el almuerzo con el equipo y en la tarde estudiar inglés",
     ["Reunión", "Almuerzo con el equipo", "Estudiar inglés"]),
    ("hacer la tarea de inglés e ir a la biblioteca", ["Hacer la tarea de inglés", "Ir a la biblioteca"]),
    ("escribir el ensayo, el cual es para el viernes, y enviarlo al profesor", ["Escribir el ensayo", "Enviarlo al profesor"]),
    ("Reunión con el cliente a las 9 am, presentación del proyecto a las 11 y almuerzo a la 1",
     ["Reunión con el cliente", "Presentación del proyecto", "Almuerzo"]),
])
def test_separa_con_comas_y_conectores(parser, text, expected):
    assert [t.title for t in parser.parse(text, NOW)] == expected


def test_condicion_entre_comas_queda_en_la_tarea_siguiente(parser):
    tasks = parser.parse("estudiar para el parcial y después, si me da tiempo, ver una película", NOW)
    assert [t.title for t in tasks] == ["Estudiar para el parcial", "Ver una película"]
    assert tasks[1].importance == 1


@pytest.mark.parametrize("text", [
    "comprar pan, leche y huevos",
    "pagar el arriendo, la luz y el agua antes del viernes",
    "llamar al banco y a la EPS",
    "hacer ejercicio y estiramientos",
    "estudiar cálculo, pero no mucho",
])
def test_no_separa_listas_de_una_misma_tarea(parser, text):
    assert len(parser.parse(text, NOW)) == 1


def test_intake_sin_llm_usa_reglas():
    tasks, events = IntakeAgent(NullProvider(), SETTINGS).run("lavar la ropa y cocinar", NOW)
    assert len(tasks) == 2
    assert "reglas" in events[-1].message
