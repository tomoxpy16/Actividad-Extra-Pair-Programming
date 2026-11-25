# AGENTS.md — instrucciones para asistentes de IA (Copilot, Cursor, Claude Code, Codex)

Trabajas como **compañero de pair programming** en Kairos, un orquestador multiagente de productividad. El humano siempre revisa y aprueba tus cambios: explica lo que haces y por qué.

## Arquitectura (respétala)
- `orchestrator/app/domain/`: objetos de dominio puros. **No importa nada** de `api`, `infrastructure` ni frameworks.
- `orchestrator/app/agents/`: un agente = una responsabilidad. Los agentes reciben `list[Task]` y `now`, y devuelven tareas y `AgentEvent`. **Nunca** acceden a la BD ni a HTTP.
- `orchestrator/app/orchestration/`: `graph.py` (LangGraph) define las rutas y `orchestrator.py` es la fachada con la unidad de trabajo (transacción + `advisory lock`).
- `orchestrator/app/infrastructure/`: BD (SQLAlchemy), repositorio y proveedores de LLM (`LLMProvider`).
- `orchestrator/app/api/`: solo traduce HTTP ↔ casos de uso.
- `web/`: HTML/CSS/JS sin framework. Escapa siempre el texto con `esc()`.

## Reglas
- El LLM solo se usa para **lenguaje** (entender o redactar). Prioridades y agenda son **deterministas**.
- Todo agente que use LLM debe tener un camino de **degradación** sin LLM.
- Cada agente debe publicar un evento explicando su decisión.
- Usa type hints, funciones cortas y nombres en inglés para el código. Los mensajes al usuario van en español.
- No agregues dependencias sin justificarlo.
- No escribas secretos en el código. La configuración va por variables de entorno (`app/config.py`).

## Comandos
```bash
# pruebas (local)
cd orchestrator && python -m pytest -q
# pruebas (Docker)
docker compose run --rm --no-deps orchestrator pytest -q
# levantar todo
docker compose up -d --build   # UI http://localhost:8080 · API http://localhost:8000/docs
```

## Definición de terminado
1. Prueba nueva o actualizada que cubra el cambio.
2. `pytest` en verde.
3. `docker compose up -d --build` levanta los 4 servicios sanos.
4. Diff pequeño y explicado.
