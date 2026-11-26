"""IntakeAgent: convierte lenguaje natural en tareas estructuradas.

Estrategia híbrida:
1. Si hay LLM configurado, le pide un JSON con esquema estricto y lo valida.
2. Si el LLM no está o falla, usa un analizador de reglas en español (determinista).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any

from app.agents.base import Agent
from app.domain.models import AgentEvent, Category, Task, TaskStatus, WorkSettings
from app.infrastructure.llm import LLMProvider, LLMUnavailable

# ---------------------------------------------------------------- vocabulario
WEEKDAYS = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}
WORD_NUMBERS = {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6}

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    Category.ESTUDIO.value: ["estudiar", "examen", "parcial", "tarea", "taller", "curso", "clase", "repasar",
                             "investigar", "ensayo", "sustentacion", "quiz", "universidad", "tesis", "leer el capitulo"],
    Category.TRABAJO.value: ["reunion", "informe", "correo", "correos", "email", "cliente", "jefe", "presentacion",
                             "programar", "codigo", "desplegar", "deploy", "pull request", "oficina", "daily", "sprint"],
    Category.SALUD.value: ["gimnasio", "gym", "correr", "medico", "odontologo", "meditar", "ejercicio", "yoga",
                           "entrenar", "terapia", "caminar"],
    Category.HOGAR.value: ["lavar", "limpiar", "cocinar", "mercado", "comprar", "ropa", "arreglar", "pagar",
                           "factura", "servicios", "aspirar", "planchar"],
    Category.PERSONAL.value: ["llamar a mi", "mama", "papa", "amigo", "amiga", "cumpleanos", "regalo", "cine",
                              "novia", "novio", "familia", "abuela", "abuelo"],
}

DEFAULT_DURATIONS: list[tuple[str, int]] = [
    ("examen", 120), ("parcial", 120), ("estudiar", 90), ("repasar", 60), ("reunion", 60), ("presentacion", 60),
    ("informe", 90), ("gimnasio", 60), ("gym", 60), ("entrenar", 60), ("correr", 40), ("llamar", 15),
    ("llamada", 20), ("correo", 20), ("email", 20), ("comprar", 45), ("mercado", 60), ("limpiar", 40),
    ("lavar", 30), ("cocinar", 45), ("leer", 45), ("pagar", 15), ("meditar", 15),
]

HIGH_IMPORTANCE = ["importante", "prioridad", "critico", "clave", "obligatorio"]
DOMAIN_IMPORTANCE = ["examen", "parcial", "entrega", "entregar", "sustentacion", "cliente", "jefe", "pagar",
                     "factura", "medico", "cita", "tesis", "proyecto"]
LOW_IMPORTANCE = ["si puedo", "si me da tiempo", "si alcanzo", "opcional", "quizas", "tal vez", "si sobra tiempo"]
URGENT_WORDS = ["urgente", "ya mismo", "cuanto antes", "lo antes posible", "asap", "inmediato"]

# ------------------------------------------------------------------ división en frases
# Conectores que, después de una coma o de "y", siempre abren una actividad nueva.
STRONG_CONNECTORS = (r"(?:luego|despues|ademas|tambien|por ultimo|finalmente|al final|mas tarde"
                     r"|(?:en|por) la (?:manana|tarde|noche))")
# Conectores que pueden ir antes del verbo de la actividad ("pero antes desayunar", "entonces estudiar").
_WEAK = (r"(?:(?:y|e|pero|entonces|antes|primero|segundo|tercero|igualmente|aparte|tambien|ademas|luego"
         r"|despues|finalmente|por ultimo)\s+)*")
_COND = r"(?:si (?:me da tiempo|puedo|alcanzo|sobra tiempo)\s+)?"
_MODAL = r"(?:(?:tengo que|tengo|debo|necesito|quiero|hay que|voy a|me toca)\s+)?"
INFINITIVE = r"(?:ir|ver|ser|dar|[a-záéíóúñ]{2,}(?:ar|er|ir))(?:me|le|lo|la|les|los|las|se)?\b"
# Actividades que se nombran con un sustantivo ("reunión a las 3, almuerzo a la 1").
ACTIVITY_NOUN = (r"(?:reunion|presentacion|almuerzo|desayuno|cena|cita|clase|examen|parcial|entrega|llamada|junta"
                 r"|sustentacion|entrenamiento|consulta|quiz|turno|vuelo|partido|practica|charla|conferencia|daily)\b")
_ARTICLE = r"(?:(?:el|la|los|las|un|una|mi|mis|otra|otro)\s+)?"
REFLEXIVE = r"me\s+[a-z]{3,}o\b"  # "me ducho", "me acuesto"
_STARTS_ACTIVITY = rf"{_WEAK}{_COND}{_MODAL}(?:{INFINITIVE}|{REFLEXIVE})"
SPLIT_RE = re.compile(
    r"(?:[\n;•:]+|(?<=[.!?])\s+"
    rf"|,\s*(?=(?:y\s+|e\s+)?{STRONG_CONNECTORS}\b)"            # ", luego el almuerzo"
    rf"|\s+[ye]\s+(?={STRONG_CONNECTORS}\b)"                    # " y por último revisar"
    rf"|,\s*(?={_STARTS_ACTIVITY}|{_WEAK}{_MODAL}{_ARTICLE}{ACTIVITY_NOUN})"  # ", pero antes desayunar", ", presentación…"
    rf"|\s+[ye]\s+(?={_STARTS_ACTIVITY}|{_MODAL}{ACTIVITY_NOUN}))",     # " e ir", " y almuerzo a la 1"
    re.IGNORECASE,
)
# Comas que siguen a un conector o a una condición ("después, si me da tiempo, ver…"): no separan actividades.
SOFT_COMMA_RE = re.compile(r"\b(?:si me da tiempo|si puedo|si alcanzo|si sobra tiempo|luego|despues|ademas|tambien"
                           r"|entonces|finalmente|por ultimo|al final|primero|mas tarde|pero antes)\s*(,)", re.IGNORECASE)

_FILLER_CONNECT = (r"(?:y|e|pero|entonces|antes|tambien|ademas|luego|despues(?: de eso)?|primero|segundo|tercero"
                   r"|finalmente|por ultimo|al final|mas tarde|igualmente|aparte|(?:en|por|a) la (?:manana|tarde|noche))")
FILLER_RE = re.compile(
    rf"^(?:{_FILLER_CONNECT}[\s,]+)*"
    r"(?:(?:yo\s+)?(?:tengo que|tengo|debo|necesito|quiero|me toca|hay que|voy a|toca|pienso|deberia|quisiera)\s+)?",
    re.IGNORECASE,
)

HOUR = r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.\s?m\.?|p\.\s?m\.?|de la manana|de la tarde|de la noche)?"
FIXED_RE = re.compile(rf"\b(?:a las|a la)\s+{HOUR}", re.IGNORECASE)
DEADLINE_HOUR_RE = re.compile(rf"\b(?:antes de las|antes de la|para las|hasta las|maximo a las)\s+{HOUR}", re.IGNORECASE)
NOON_RE = re.compile(r"\b(?:a|antes del|para el)\s+mediodia\b", re.IGNORECASE)
LEADING_DAY_RE = re.compile(r"^\s*(?:para\s+)?(?:hoy|manana|pasado manana|el (?:lunes|martes|miercoles|jueves|viernes|sabado|domingo))\b", re.IGNORECASE)
DAY_OF_MONTH_RE =re.compile(r"\b(?:el|para el|antes del)\s+(\d{1,2})(?:\s+de\s+\w+)?\b", re.IGNORECASE)

DURATION_PATTERNS: list[tuple[re.Pattern[str], Any]] = [
    (re.compile(r"(\d+)\s*horas?\s*y\s*media", re.I), lambda m: int(m.group(1)) * 60 + 30),
    (re.compile(r"\b(un|una|dos|tres|cuatro|cinco)\s+horas?\s+y\s+media\b", re.I), lambda m: WORD_NUMBERS[m.group(1).lower()] * 60 + 30),
    (re.compile(r"\bhora y media\b", re.I), lambda m: 90),
    (re.compile(r"\bmedia hora\b", re.I), lambda m: 30),
    (re.compile(r"\bun cuarto de hora\b", re.I), lambda m: 15),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:h|hr|hrs|horas?)\b", re.I), lambda m: round(float(m.group(1).replace(",", ".")) * 60)),
    (re.compile(r"\b(un|una|dos|tres|cuatro|cinco|seis)\s+horas?\b", re.I), lambda m: WORD_NUMBERS[m.group(1).lower()] * 60),
    (re.compile(r"(\d+)\s*(?:m|min|mins|minutos?)\b", re.I), lambda m: int(m.group(1))),
]
DURATION_PREFIX = r"(?:durante|por|como|unos|unas|aprox(?:imadamente)?|mas o menos)\s+"


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _hour_to_24(h: int, mins: int, suffix: str | None) -> tuple[int, int]:
    s = (suffix or "").lower().replace(" ", "").replace(".", "")
    if s in ("pm", "delatarde", "delanoche") and h < 12:
        h += 12
    elif s in ("am", "delamanana") and h == 12:
        h = 0
    elif not s and 1 <= h <= 6:  # "a las 3" casi siempre significa 3 p. m.
        h += 12
    return min(h, 23), min(mins, 59)


class _Fragment:
    """Texto original + copia sin tildes en minúscula con las mismas posiciones.

    Las expresiones regulares se aplican sobre `plain`; los recortes se hacen en ambas
    copias (rellenando con espacios) para que el título final conserve las tildes.
    """

    def __init__(self, original: str) -> None:
        original = unicodedata.normalize("NFC", original)
        plain = strip_accents(original).lower()
        if len(plain) != len(original):  # caracteres raros: degradamos a texto sin tildes
            original = plain
        self.orig = original
        self.plain = plain

    def cut(self, start: int, end: int) -> None:
        pad = " " * (end - start)
        self.orig = self.orig[:start] + pad + self.orig[end:]
        self.plain = self.plain[:start] + pad + self.plain[end:]

    def cut_all(self, pattern: str) -> None:
        for m in list(re.finditer(pattern, self.plain)):
            self.cut(m.start(), m.end())


class RuleBasedParser:
    """Analizador determinista de español coloquial."""

    def __init__(self, settings: WorkSettings) -> None:
        self.settings = settings

    # -------------------------------------------------------------- división
    def split(self, text: str) -> list[str]:
        text = unicodedata.normalize("NFC", text)
        plain = strip_accents(text)
        if len(plain) != len(text):
            text = plain
        # Neutraliza las comas que solo acompañan a un conector (se reemplazan por espacios para
        # conservar las posiciones entre el texto original y la copia sin tildes).
        for m in SOFT_COMMA_RE.finditer(plain):
            i = m.start(1)
            plain, text = plain[:i] + " " + plain[i + 1:], text[:i] + " " + text[i + 1:]
        parts, last = [], 0
        for m in SPLIT_RE.finditer(plain):
            parts.append(text[last:m.start()])
            last = m.end()
        parts.append(text[last:])
        cleaned = [p.strip(" .,-*\t") for p in parts]
        return [p for p in cleaned if len(p) > 2]

    # -------------------------------------------------------------- campos
    @staticmethod
    def _duration(f: _Fragment) -> int | None:
        for pattern, fn in DURATION_PATTERNS:
            m = pattern.search(f.plain)
            if m:
                minutes = fn(m)
                f.cut(m.start(), m.end())
                pm = re.search(rf"\b{DURATION_PREFIX}\s*$", f.plain[: m.start()])
                if pm:
                    f.cut(pm.start(), pm.end())
                return max(5, min(minutes, 8 * 60))
        return None

    @staticmethod
    def _day(f: _Fragment, now: datetime) -> datetime | None:
        today = now.replace(hour=0, minute=0)
        patterns: list[tuple[str, Any]] = [
            (r"\b(?:para |de )?pasado manana\b", lambda m: today + timedelta(days=2)),
            (r"\b(?:para |de )?manana\b(?!\s+por la)", lambda m: today + timedelta(days=1)),
            (r"\b(?:para |de )?hoy\b", lambda m: today),
            (r"\b(?:para |durante )?esta semana\b", lambda m: today + timedelta(days=(6 - today.weekday()))),
            (r"\b(?:el |este |para el |antes del |del |hasta el )?(lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b",
             lambda m: today + timedelta(days=((WEEKDAYS[m.group(1)] - today.weekday()) % 7) or 7)),
        ]
        for pat, fn in patterns:
            m = re.search(pat, f.plain)
            if m:
                f.cut(m.start(), m.end())
                return fn(m)
        m = DAY_OF_MONTH_RE.search(f.plain)
        if m and 1 <= int(m.group(1)) <= 31:
            day = int(m.group(1))
            candidate = today
            for _ in range(62):
                if candidate.day == day:
                    f.cut(m.start(), m.end())
                    return candidate
                candidate += timedelta(days=1)
        return None

    @staticmethod
    def _clock_time(f: _Fragment, regex: re.Pattern[str]) -> tuple[int, int] | None:
        m = regex.search(f.plain)
        if not m:
            return None
        f.cut(m.start(), m.end())
        return _hour_to_24(int(m.group(1)), int(m.group(2) or 0), m.group(3))

    @staticmethod
    def _category(low: str) -> str:
        best, hits = Category.OTRO.value, 0
        for cat, words in CATEGORY_KEYWORDS.items():
            n = sum(1 for w in words if re.search(rf"\b{w}", low))
            if n > hits:
                best, hits = cat, n
        return best

    @staticmethod
    def _importance(low: str) -> int:
        score = 3
        if "muy importante" in low or "super importante" in low:
            score = 5
        elif any(w in low for w in HIGH_IMPORTANCE):
            score += 1
        if any(re.search(rf"\b{w}", low) for w in DOMAIN_IMPORTANCE):
            score += 1
        if any(w in low for w in LOW_IMPORTANCE):
            score = 1 if score <= 3 else 2
        return max(1, min(5, score))

    @staticmethod
    def _default_duration(low: str) -> int:
        for word, minutes in DEFAULT_DURATIONS:
            if word in low:
                return minutes
        return 45

    @staticmethod
    def _clean_title(f: _Fragment) -> str:
        noise = URGENT_WORDS + LOW_IMPORTANCE + ["muy importante", "super importante", "es importante", "importante",
                                                "urgentemente", "sin falta", "porque es", "lo cual es", "que es"]
        for w in sorted(noise, key=len, reverse=True):
            f.cut_all(rf"\b{re.escape(w)}\b")
        f.cut_all(rf"\b{DURATION_PREFIX}(?=\s*$)")
        m = FILLER_RE.match(f.plain.lstrip())
        if m and m.end() > 0:
            offset = len(f.plain) - len(f.plain.lstrip())
            f.cut(offset, offset + m.end())
        # Artículo inicial sobrante: "el almuerzo con el equipo" -> "Almuerzo con el equipo".
        art = re.match(r"\s*(?:el|la|los|las|un|una)\s+(?=\w+\s+\w)", f.plain)
        if art:
            f.cut(art.start(), art.end())
        trailing = (r"\b(?:(?:el|la|lo|los|las) cual(?:es)?|en la|en el|por la|por el|de la|para la|para el|para"
                    r"|el|la|y|a|que|es|,)\s*$")
        for _ in range(3):
            stripped_len = len(f.plain.rstrip(" ,.;:-"))
            f.plain, f.orig = f.plain[:stripped_len], f.orig[:stripped_len]
            m = re.search(trailing, f.plain)
            if not m:
                break
            f.cut(m.start(), m.end())
        title = re.sub(r"\s{2,}", " ", f.orig).strip(" ,.;:-")
        title = re.sub(r"\s+([,.;:])", r"\1", title)
        return (title[:1].upper() + title[1:]) if title else ""

    # -------------------------------------------------------------- tarea
    def parse_fragment(self, text: str, now: datetime, context_day: datetime | None = None) -> Task | None:
        f = _Fragment(text)
        low = f.plain
        minutes = self._duration(f)
        fixed_hm = self._clock_time(f, FIXED_RE)
        deadline_hm = self._clock_time(f, DEADLINE_HOUR_RE)
        noon = NOON_RE.search(f.plain)
        if noon:
            deadline_hm = deadline_hm or (12, 0)
            f.cut(noon.start(), noon.end())
        day = self._day(f, now) or context_day
        urgent = any(w in low for w in URGENT_WORDS)

        end_h, end_m = self.settings.end_hm()
        fixed_start = deadline = None
        if fixed_hm:
            base = day or now.replace(hour=0, minute=0)
            fixed_start = base.replace(hour=fixed_hm[0], minute=fixed_hm[1])
            if day is None and fixed_start < now:
                fixed_start += timedelta(days=1)
        if deadline_hm:
            base = day or now.replace(hour=0, minute=0)
            deadline = base.replace(hour=deadline_hm[0], minute=deadline_hm[1])
            if day is None and deadline < now:
                deadline += timedelta(days=1)
        elif day is not None and not fixed_hm:
            deadline = day.replace(hour=end_h, minute=end_m)
        if urgent and deadline is None and fixed_start is None:
            deadline = now.replace(hour=end_h, minute=end_m)
            if deadline <= now:
                deadline = now + timedelta(hours=3)

        title = self._clean_title(f)
        if not title:
            return None
        return Task(
            title=title,
            estimated_minutes=minutes or self._default_duration(low),
            category=self._category(low),
            importance=self._importance(low),
            deadline=deadline,
            fixed_start=fixed_start,
            urgent_hint=urgent,
            source_text=text.strip(),
            created_at=now,
        )

    def parse(self, text: str, now: datetime) -> list[Task]:
        """Un día al inicio de una oración ("Mañana: ...", "Hoy tengo ...") aplica a las tareas siguientes."""
        tasks: list[Task] = []
        context_day: datetime | None = None
        for frag in self.split(text):
            if LEADING_DAY_RE.match(strip_accents(frag)):
                context_day = self._day(_Fragment(frag), now)
            task = self.parse_fragment(frag, now, context_day)
            if task is not None:
                tasks.append(task)
        return tasks


# ------------------------------------------------------------------ esquema LLM
TASKS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["tasks"],
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "estimated_minutes", "category", "importance", "deadline", "fixed_start", "urgent"],
                "properties": {
                    "title": {"type": "string"},
                    "estimated_minutes": {"type": "integer"},
                    "category": {"type": "string", "enum": [c.value for c in Category]},
                    "importance": {"type": "integer"},
                    "deadline": {"type": ["string", "null"]},
                    "fixed_start": {"type": ["string", "null"]},
                    "urgent": {"type": "boolean"},
                },
            },
        }
    },
}

SYSTEM_PROMPT = """Eres el IntakeAgent de Kairos, un asistente de productividad.
Convierte lo que el usuario escribe en una lista de tareas accionables, una por actividad.
- title: verbo en infinitivo + objeto, corto (máx. 8 palabras), en español.
- estimated_minutes: la duración que dice el usuario o una estimación realista.
- importance: 1 (trivial) a 5 (crítico). Exámenes, entregas, clientes, salud y pagos suelen ser 4-5.
- deadline: fecha-hora ISO 8601 con zona horaria si el usuario menciona un límite ("para el viernes", "antes de las 5"); si no, null.
- fixed_start: fecha-hora ISO 8601 si la actividad tiene hora fija ("reunión a las 3"); si no, null.
- urgent: true si el usuario expresa urgencia.
No inventes tareas que el usuario no mencionó."""


class IntakeAgent(Agent):
    name = "IntakeAgent"

    def __init__(self, llm: LLMProvider, settings: WorkSettings) -> None:
        self.llm = llm
        self.rules = RuleBasedParser(settings)

    def _from_llm(self, text: str, now: datetime) -> list[Task]:
        user = f"Fecha y hora actual: {now.isoformat()} ({now.strftime('%A')}).\nTexto del usuario:\n{text}"
        data = self.llm.complete_json(SYSTEM_PROMPT, user, TASKS_SCHEMA)
        tasks: list[Task] = []
        for item in data.get("tasks", []):
            def _dt(value: str | None) -> datetime | None:
                if not value:
                    return None
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=now.tzinfo)
            tasks.append(Task(
                title=item["title"].strip()[:120],
                estimated_minutes=max(5, min(int(item["estimated_minutes"]), 480)),
                category=item["category"] if item["category"] in {c.value for c in Category} else Category.OTRO.value,
                importance=max(1, min(5, int(item["importance"]))),
                deadline=_dt(item.get("deadline")),
                fixed_start=_dt(item.get("fixed_start")),
                urgent_hint=bool(item.get("urgent")),
                source_text=text.strip()[:500],
                created_at=now,
            ))
        if not tasks:
            raise LLMUnavailable("el LLM no devolvió tareas")
        return tasks

    def run(self, text: str, now: datetime) -> tuple[list[Task], list[AgentEvent]]:
        events: list[AgentEvent] = []
        engine = "reglas"
        tasks: list[Task] = []
        if self.llm.enabled:
            try:
                tasks = self._from_llm(text, now)
                engine = f"LLM ({self.llm.name})"
            except (LLMUnavailable, ValueError, KeyError, TypeError) as exc:
                events.append(self.event(f"El LLM no respondió bien ({exc}); uso el analizador de reglas.", "warning"))
        if not tasks:
            tasks = self.rules.parse(text, now)
        for t in tasks:
            t.status = TaskStatus.PENDING
        if tasks:
            listing = "; ".join(f"«{t.title}» ({t.estimated_minutes} min)" for t in tasks)
            events.append(self.event(f"Entendí {len(tasks)} tarea(s) con {engine}: {listing}.", "success",
                                     {"task_ids": [t.id for t in tasks]}))
        else:
            events.append(self.event("No encontré actividades en el texto. Prueba con frases como "
                                     "«estudiar cálculo 2 horas para el viernes».", "warning"))
        return tasks, events
