# 5. Guion de la demostración (en vivo o en video, ~9 minutos)

## Preparación (antes de empezar)
```powershell
docker compose up -d --build
docker compose ps          # db, orchestrator, monitor y web deben estar "Up"/"healthy"
```
Abrir dos pestañas: **http://localhost:8080** (UI) y **http://localhost:8000/docs** (Swagger). Para empezar limpio, pulsar el botón de **papelera** de la esquina superior derecha (Reiniciar) y confirmar. El cronograma debe mostrar el logo y el mensaje "Tu día todavía está en blanco".

Para grabar video en Windows: `Win + Alt + R` (Xbox Game Bar) u OBS Studio.

## Mapa rápido de la interfaz

| Zona | Qué hay |
|---|---|
| Encabezado | Logo y lema ("Tu día, en el momento oportuno"), **reloj compartido** (se pone ámbar y dice "simulado +2 h" cuando se adelanta), motor activo ("Motor: reglas" o "Motor: Claude"), grupo **Simular** (+30 min, +2 h), **Replanificar** y papelera (Reiniciar) |
| "¿Qué tienes que hacer?" | Campo de texto libre, ejemplos con nombre (**Día de trabajo**, **Semana de parciales**, **Entrega de proyecto**) y botón **Planificar** (o `Ctrl + Enter`) |
| Métricas | Tareas, Completadas (con barra de avance), En curso, En riesgo y Retrasos detectados (en rojo cuando hay) |
| Cronograma | Línea de tiempo por día. El punto de cada tarea tiene el color de su cuadrante y la línea ámbar marca **ahora**. Cada tarea tiene botones con ícono: ▶ iniciar, ✓ completar y papelera eliminar |
| Actividad de los agentes | Burbujas por agente, cada uno con su color e ícono (leyenda arriba). Las más recientes van arriba; ámbar = advertencia, azul = replanificación |

## Guion

| Min | Acción | Qué decir |
|---|---|---|
| 0:00 | Mostrar `docker compose ps` | "Kairos corre en 4 contenedores: la web, la API orquestadora, el worker del monitor y PostgreSQL como estado compartido." |
| 0:40 | Mostrar el logo en el encabezado | "El nombre viene de *kairós*, el momento oportuno. La K tiene una aguja de reloj que apunta al punto ámbar: el sistema no solo mide el tiempo, decide qué conviene hacer ahora." |
| 1:00 | Pulsar el ejemplo **Día de trabajo** y luego **Planificar** (o `Ctrl + Enter`) | "Escribo como hablo. El IntakeAgent convierte el texto en tareas estructuradas: duración, categoría, importancia, fecha límite y hora fija." |
| 1:45 | Leer la **Actividad de los agentes** de abajo hacia arriba | "El Orquestador eligió la ruta *plan*. Intake entendió 4 tareas, Prioritizer las puntuó con la matriz de Eisenhower, Scheduler armó la agenda y Coach me dice qué sigue." |
| 2:45 | Señalar el cronograma | "La reunión quedó a su hora fija. El informe va antes porque es muy importante y vence hoy. Cada tarea muestra su cuadrante, su barra de prioridad y una línea que explica por qué." |
| 3:30 | Escribir una frase propia con comas y conectores, por ejemplo: *"Tengo que estudiar 2 horas, luego ir al banco, después almorzar con Ana y por último revisar correos, pero antes desayunar"*, y planificar | "Aunque escriba con comas y conectores como *luego*, *por último* o *pero antes*, Intake separa bien las 5 actividades. Y no parte listas como *comprar pan, leche y huevos*." |
| 4:15 | Pulsar ▶ en la primera tarea | "Ahora estoy ejecutando: el punto pulsa y la tarea dice *en curso*. El plan se recalcula alrededor de ella." |
| 4:45 | En **Simular**, pulsar **+2 h** y ver cómo las tareas se deslizan a su nueva hora | "Simulo que pasaron 2 horas y no terminé. El reloj se pone ámbar. El MonitorAgent, que corre en otro contenedor, detecta el sobrecosto y las tareas que no empezaron." |
| 5:30 | Mostrar las burbujas ámbar del Monitor, las etiquetas "reprogramada ×1" / "en riesgo" y la métrica **Retrasos detectados** | "El orquestador disparó la replanificación: volvió a priorizar con un bono por retraso, movió los bloques y avisa qué tareas corren riesgo de no cumplirse." |
| 6:30 | Pulsar ✓ en una tarea | "Al completar, la barra de avance sube, el plan se compacta y lo siguiente se adelanta." |
| 7:00 | Swagger `/docs` → `GET /api/state` | "Todo es una API REST documentada. El estado compartido tiene tareas, eventos y la hora simulada." |
| 7:40 | (Opcional) `LLM_PROVIDER=anthropic` u `ollama`; el encabezado pasa a "Motor: Claude" | "Con un LLM, Intake entiende frases todavía más libres. Sin LLM, el sistema usa reglas y la demo sigue funcionando." |
| 8:15 | Mostrar `AGENTS.md` y `docs/04-pair-programming-ia.md` | "Así trabajamos con la IA como compañera: reglas versionadas, roles explícitos y TDD." |

## Activar un LLM (opcional)
```powershell
# Claude (requiere API key)
$env:LLM_PROVIDER = "anthropic"; $env:ANTHROPIC_API_KEY = "<tu llave>"; docker compose up -d
# Ollama local (descarga ~2 GB la primera vez)
$env:LLM_PROVIDER = "ollama"; docker compose --profile llm up -d
docker compose exec ollama ollama pull qwen2.5:3b
```
