# Instrucciones para GitHub Copilot — Kairos

Sigue las reglas completas de [`AGENTS.md`](../AGENTS.md). Resumen:

- Eres el compañero de pair programming del equipo. Explica cada cambio y propón pruebas primero (TDD).
- Capas: `domain` (puro) ← `agents` ← `orchestration` ← `api`. `infrastructure` se conecta en `main.py`.
- Los agentes no acceden a la BD ni a HTTP. El LLM solo se usa para lenguaje, con degradación a reglas.
- Python 3.12 con type hints. Mensajes al usuario en español.
- En la revisión de PR, busca: condiciones de carrera (API vs. monitor), HTML sin escapar en `web/app.js`, secretos en el código y violaciones de la regla de dependencias.
- Pruebas: `cd orchestrator && python -m pytest -q`.
