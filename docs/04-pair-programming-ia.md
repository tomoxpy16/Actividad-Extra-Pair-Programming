# 4. Cómo construimos Kairos con pair programming con IA

Este documento une la teoría (Tema 2) con la práctica: cómo se reparten los roles humano–IA en el flujo de desarrollo de Kairos, qué configuración versionamos para que la IA sea un buen compañero, y un ejercicio para mostrar en vivo.

---

## 4.1 Reglas del juego

1. **El humano siempre responde por el código.** Nada entra a `main` sin que una persona del equipo lo haya leído y entendido. Esa es la diferencia con el vibe coding.
2. **Los roles se nombran en voz alta** al empezar cada bloque: "IA conduce, yo navego" o "yo conduzco, la IA navega".
3. **Rotación cada 25 minutos** (un pomodoro) o en cada ciclo rojo→verde de TDD.
4. **La definición de terminado es verificable**: `pytest` en verde y la app levanta con `docker compose up`.
5. **El contexto está versionado**, no se repite en cada prompt: `AGENTS.md`, `.github/copilot-instructions.md` y `.cursor/rules/kairos.mdc`.

---

## 4.2 Configuración de la IA como compañero

| Archivo | Lo lee | Para qué |
|---|---|---|
| [`AGENTS.md`](../AGENTS.md) | Claude Code, Codex, Cursor, Copilot (estándar abierto) | Arquitectura, comandos, convenciones y límites ("no hagas X") |
| [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) | GitHub Copilot (chat, agent mode, code review) | Las mismas reglas resumidas para Copilot |
| [`.cursor/rules/kairos.mdc`](../.cursor/rules/kairos.mdc) | Cursor | Regla aplicada a los archivos de Python del orquestador |

> Sin estas reglas, la IA "conduce" bien en lo local y mal en lo global: mete SQL en los agentes, deja que el LLM calcule prioridades o rompe la regla de dependencias. Con ellas, la IA hace de **navegante que conoce la arquitectura**.

---

## 4.3 Sesiones de trabajo y reparto de roles

| # | Bloque | Driver | Navigator | Herramienta | Resultado |
|---|---|---|---|---|---|
| 1 | Visión y requisitos | Humano | IA (crítica: "¿qué falta?, ¿qué es ambiguo?") | Chat (Copilot Chat / Claude) | Requisitos RF1–RF8 y alcance |
| 2 | Arquitectura y ADR | Humano | IA (propone alternativas y trade-offs) | Chat | Agentes en proceso, pizarra en PostgreSQL, LLM opcional (ADR 001–007) |
| 3 | Modelo de dominio | IA | Humano (revisa nombres y estados) | Agent mode | `domain/models.py`, `clock.py` |
| 4 | Agentes con TDD ping-pong | Alternan | Alternan | Cursor Agent / Copilot agent mode + terminal | `tests/test_agents.py` → agentes en verde |
| 5 | Orquestación (LangGraph) | IA | Humano (valida rutas y estado compartido) | Agente en terminal (Claude Code) | `orchestration/graph.py`, `orchestrator.py` |
| 6 | Persistencia y concurrencia | Humano | IA (detecta la condición de carrera API ↔ monitor) | Chat + revisión | `advisory lock` + Unit of Work |
| 7 | Docker y despliegue | IA | Humano (verifica puertos, redes, mínimo privilegio) | Agent mode | `Dockerfile`, `docker-compose.yml` |
| 8 | UI | IA | Humano (UX, textos en español) | Agent mode + navegador | `web/` |
| 9 | Revisión final | Humano | IA como revisora de PR | Copilot code review | Correcciones de seguridad y estilo |

> **Transparencia:** la versión inicial de este repositorio se generó con **Claude Code (IA conduciendo)**, a partir de la especificación del equipo (el humano navegando). El equipo debe completar la bitácora de la sección 4.6 con sus propias sesiones de revisión y ajuste con Copilot o Cursor. Esa evidencia es parte de la entrega.

### Hallazgos de la IA como navegante durante la construcción
- **Condición de carrera**: la API y el worker del monitor escriben las mismas tareas. Solución: `pg_advisory_xact_lock` dentro de una unidad de trabajo.
- **Zona horaria**: el navegador del cliente puede tener otra zona que el servidor. Solución: la UI muestra la hora en la zona del servidor (`KAIROS_TZ`).
- **Tildes**: el analizador de reglas trabaja sin tildes, pero los títulos deben conservarlas. Solución: dos copias alineadas del texto (`_Fragment`).
- **LLM para cálculos**: se descartó que el LLM calculara prioridades (no es reproducible). Queda solo para lenguaje (ADR 004).

### Hallazgos del humano como navegante
- Pedir que **cada agente explique su decisión** (`rationale` y eventos): es requisito de UX y de explicabilidad.
- Exigir un **reloj simulado** para poder demostrar retrasos en vivo.
- Exigir que la demo funcione **sin internet ni API keys** (proveedor `rules` por defecto).

---

## 4.4 Prompts que funcionaron (patrones)

| Situación | Prompt (resumen) | Rol de la IA |
|---|---|---|
| Diseño | "Propón 3 arquitecturas para un orquestador multiagente con estado compartido. Compara disponibilidad, complejidad operativa y costo. No escribas código." | Navegante |
| TDD | "Aquí está la prueba que falla (`test_pasa_al_dia_siguiente_si_no_cabe`). Implementa lo mínimo en `SchedulerAgent` para que pase, sin tocar otras pruebas." | Conductora (ping-pong) |
| Revisión | "Revisa este diff buscando condiciones de carrera, inyección de HTML y violaciones de la regla de dependencias de `AGENTS.md`." | Navegante / revisora |
| Refactor | "Extrae el proveedor de LLM a una interfaz `LLMProvider` con implementación nula. No cambies el comportamiento: las pruebas deben seguir en verde." | Conductora |
| Explicación | "Explícame qué hace `SPLIT_RE` con un ejemplo de entrada y salida." | Tutora |

**Antipatrones que evitamos:** "hazme la app completa" (vibe coding), aceptar diffs de más de ~300 líneas sin dividirlos, pegar llaves de API en el chat y pedirle a la IA que "arregle" una prueba cambiando la prueba.

---

## 4.5 Ejercicio en vivo (kata de 10 minutos para la sustentación)

**Objetivo:** mostrar en vivo los dos roles con Copilot o Cursor sobre el código real.

**Historia:** *"Como usuario, si escribo una tarea de más de 2 horas quiero que se divida en bloques de máximo 90 minutos, para no agotarme."*

| Paso | Driver | Navigator | Acción |
|---|---|---|---|
| 1 | Humano | IA | El humano escribe la prueba que falla en `tests/test_agents.py` (abajo). La IA sugiere casos límite: ¿qué pasa con exactamente 90 min? |
| 2 | IA | Humano | Agent mode: *"Haz pasar `test_divide_tareas_largas` modificando solo `SchedulerAgent`. Respeta `AGENTS.md`."* El humano revisa el diff en voz alta. |
| 3 | Humano | IA | El humano ejecuta `pytest`. Si algo falla, pide a la IA que **explique** el error antes de corregir. |
| 4 | Ambos | — | `docker compose up -d --build` y demostración en la UI. |

```python
def test_divide_tareas_largas():
    t = Task("Estudiar", estimated_minutes=200, priority_score=80)
    tasks, _ = SchedulerAgent(SETTINGS).run([t], NOW)
    bloques = [x for x in tasks if x.title.startswith("Estudiar")]
    assert len(bloques) == 3
    assert all(b.estimated_minutes <= 90 for b in bloques)
    assert sum(b.estimated_minutes for b in bloques) == 200
```

**Qué señalar al público:**
- Cuando la IA conduce, el humano **no está pasivo**: lee, pregunta y rechaza.
- La prueba es la "definición de terminado" que vuelve verificable el trabajo de la IA.
- La regla en `AGENTS.md` evita que la IA mezcle responsabilidades.

---

## 4.6 Bitácora de pair programming

| Fecha | Integrantes | Herramienta / modelo | Driver | Navigator | Tarea | Sugerencias aceptadas / rechazadas | Defectos encontrados por el navegante | Minutos |
|---|---|---|---|---|---|---|---|---|
| 2026-11-25 | Equipo + Claude Code | Claude (Opus) | IA | Humano | Versión inicial completa (agentes, API, Docker, docs) | — | Zona horaria en UI; división de frases con "ir" | — |
| 2026-11-25 | Tomás + Claude Code | Claude (Opus) | IA | Tomás | Rediseño de la interfaz y logo | Aceptados: logo (K con aguja de reloj), reloj simulado en ámbar, métricas con íconos, modo oscuro | Plural mal formado: "reprogramada 1 veces" | — |
| 2026-11-25 | Tomás + Claude Code | Claude (Opus) | IA (TDD) | Tomás | División de frases con comas y conectores en `IntakeAgent` | Primero 13 casos nuevos en rojo, después la corrección (de 13 a 26 pruebas). Se exigió que las listas no se partan ("pan, leche y huevos") | Frases con comas y conectores ("…, luego …") se partían mal | — |
| 2026-11-25 | Tomás + Claude Code | Claude (Opus) | IA | Tomás | Tipografía Inter, íconos Lucide y animación del replanificado (View Transitions) | Se pidió servir fuentes e íconos desde el contenedor, sin CDN, para que la demo funcione sin internet | — | — |
| 2026-11-26 | Tomás + Claude Code | Claude (Opus) | IA (TDD) | Tomás | Revisión del PR #5 de Gustavo y mejoras del `SchedulerAgent` | La IA, como revisora, señaló dos detalles y Tomás decidió corregirlos: 2 pruebas en rojo y luego la corrección (de 26 a 28 pruebas) | Días en inglés ("Thu") en los mensajes por usar `%a`; citas de hora fija que se cruzaban sin aviso | — |
| | Santiago + Copilot o Cursor | | | | | | | |
| | Gustavo + Copilot o Cursor | | | | | | | |

**Métricas sugeridas:** porcentaje de sugerencias aceptadas, defectos detectados antes del merge, tiempo hasta verde en TDD y número de rotaciones de rol por sesión.
