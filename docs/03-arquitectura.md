# 3. Ejemplo práctico: Kairos — arquitectura

> **Kairos** (del griego *kairós*, "el momento oportuno") es un orquestador inteligente multiagente que funciona como asistente personal de productividad. El usuario escribe sus actividades en lenguaje natural. El sistema las convierte en tareas estructuradas, las prioriza, arma un cronograma y lo acompaña durante la ejecución: detecta retrasos y reorganiza las actividades cuando hace falta.

**Fuente principal de los diagramas C4:** [`docs/diagrams/kairos.dsl`](diagrams/kairos.dsl), en **Structurizr DSL**. Un solo modelo genera las 6 vistas: contexto, contenedores, componentes, dos dinámicas y despliegue. Para verlas o exportarlas a PNG/SVG, pega el archivo en [playground.structurizr.com](https://playground.structurizr.com), pulsa ▶ y elige la vista en la lista desplegable.

**Vistas exportadas a PNG** (desde el DSL, fondo blanco y alta resolución, listas para diapositivas) en [`docs/diagrams/png/`](diagrams/png/):

| Vista | Archivo |
|---|---|
| C1 — Contexto | [kairos-C1-Contexto.png](diagrams/png/kairos-C1-Contexto.png) |
| C2 — Contenedores | [kairos-C2-Contenedores.png](diagrams/png/kairos-C2-Contenedores.png) |
| C3 — Componentes del Orchestrator API | [kairos-C3-Componentes.png](diagrams/png/kairos-C3-Componentes.png) |
| Dinámico 1 — Planificar | [kairos-D1-Planificar.png](diagrams/png/kairos-D1-Planificar.png) |
| Dinámico 2 — Retraso y replanificación | [kairos-D2-Replanificar.png](diagrams/png/kairos-D2-Replanificar.png) |
| Despliegue — Docker Compose | [kairos-Despliegue.png](diagrams/png/kairos-Despliegue.png) |

![C2 — Contenedores de Kairos](diagrams/png/kairos-C2-Contenedores.png)

Los diagramas de abajo están en **Mermaid**, que GitHub dibuja automáticamente. También hay versiones en **C4-PlantUML** y UML en [`docs/diagrams/`](diagrams/), que se renderizan con `scripts/render-diagrams.ps1`.

---

## 3.1 Vista de alto nivel

```mermaid
flowchart LR
    U(["👤 Usuario"]) -- "«Mañana estudiar cálculo 2 h,<br/>reunión a las 3 pm…»" --> UI["Interfaz web"]
    UI --> O{{"🎯 Orquestador<br/>(estado compartido)"}}
    O --> I["🧾 IntakeAgent<br/>lenguaje natural → tareas"]
    O --> P["⚖️ PrioritizerAgent<br/>puntaje + Eisenhower"]
    O --> S["🗓️ SchedulerAgent<br/>cronograma"]
    O --> C["💬 CoachAgent<br/>siguiente paso"]
    M["👀 MonitorAgent<br/>(cada 15 s)"] -- "retraso detectado" --> O
    O <--> DB[("Pizarra compartida<br/>PostgreSQL")]
    M <--> DB
    I -. "opcional" .-> LLM["LLM<br/>Claude / Ollama"]
    C -. "opcional" .-> LLM
```

**Idea clave:** el orquestador no "piensa". **Enruta** el trabajo entre agentes especializados que leen y escriben un **estado compartido** (patrón pizarra). El LLM es opcional y solo se usa donde aporta, es decir, para entender y redactar lenguaje natural. La prioridad y la agenda son algoritmos deterministas, explicables y probados.

### Requisitos que cubre

| # | Requisito | Dónde |
|---|---|---|
| RF1 | Expresar actividades en lenguaje natural | `IntakeAgent` (LLM con esquema JSON estricto, o analizador de reglas en español) |
| RF2 | Convertirlas en tareas estructuradas (duración, categoría, importancia, fecha límite, hora fija) | `domain/models.py::Task` |
| RF3 | Priorizar | `PrioritizerAgent`: puntaje 0–100 + cuadrante de Eisenhower + explicación |
| RF4 | Organizar un cronograma | `SchedulerAgent`: jornada laboral, descansos, citas fijas, riesgo de incumplimiento |
| RF5 | Acompañar la ejecución | `CoachAgent` + acciones Iniciar / Completar |
| RF6 | Detectar retrasos | `MonitorAgent` en un contenedor `monitor` independiente |
| RF7 | Reorganizar automáticamente | Ruta `monitor → prioritize → schedule → coach` del grafo |
| RF8 | Coordinar agentes con estado compartido | `Orchestrator` + LangGraph `StateGraph` + PostgreSQL |

---

## 3.2 C4 — Nivel 1: Contexto

```mermaid
C4Context
    title Kairos — Diagrama de contexto (C4 nivel 1)
    Person(user, "Usuario", "Estudiante o profesional que quiere organizar su tiempo")
    System(kairos, "Kairos", "Orquestador multiagente: entiende pendientes, prioriza, agenda y replanifica")
    System_Ext(anthropic, "Anthropic API", "Modelos Claude (opcional)")
    System_Ext(ollama, "Ollama", "LLM local de pesos abiertos (opcional)")
    Rel(user, kairos, "Escribe pendientes, inicia y completa tareas", "HTTP")
    Rel(kairos, anthropic, "Extrae tareas y redacta mensajes", "HTTPS/JSON")
    Rel(kairos, ollama, "Extrae tareas y redacta mensajes", "HTTP/JSON")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

---

## 3.3 C4 — Nivel 2: Contenedores

```mermaid
C4Container
    title Kairos — Diagrama de contenedores (C4 nivel 2)
    Person(user, "Usuario", "Usa Kairos desde el navegador")
    System_Boundary(k, "Kairos") {
        Container(web, "Web App + Proxy", "Nginx 1.27, HTML/CSS/JS", "Sirve la interfaz y redirige /api al orquestador")
        Container(api, "Orchestrator API", "Python 3.12, FastAPI, LangGraph", "Casos de uso: planificar, replanificar, acciones sobre tareas, reloj simulado")
        Container(mon, "Monitor Worker", "Python 3.12 (misma imagen)", "Ejecuta el MonitorAgent cada N segundos y dispara la replanificación")
        ContainerDb(db, "Estado compartido", "PostgreSQL 16", "Tareas, eventos de agentes y configuración (pizarra)")
    }
    System_Ext(llm, "Proveedor LLM", "Anthropic Claude u Ollama (opcional)")
    Rel(user, web, "Usa", "HTTP :8080")
    Rel(web, api, "Proxy /api/*", "HTTP/JSON :8000")
    Rel(api, db, "Lee/escribe con bloqueo consultivo", "SQL")
    Rel(mon, db, "Lee/escribe con bloqueo consultivo", "SQL")
    Rel(api, llm, "Prompts con esquema JSON", "HTTPS")
    Rel(mon, llm, "Mensajes del coach", "HTTPS")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

| Contenedor | Imagen | Puerto | Red | Responsabilidad |
|---|---|---|---|---|
| `web` | `kairos/web:1.0` (nginx:1.27-alpine) | 8080 → 80 | frontend | UI estática + proxy inverso |
| `orchestrator` | `kairos/orchestrator:1.0` (python:3.12-slim) | 8000 | frontend, backend | API REST + grafo de agentes |
| `monitor` | `kairos/orchestrator:1.0` | — | backend | Bucle del `MonitorAgent` |
| `db` | `postgres:16-alpine` | interno | backend | Estado compartido |
| `ollama` *(perfil `llm`)* | `ollama/ollama` | interno | backend | LLM local opcional |

---

## 3.4 C4 — Nivel 3: Componentes del Orchestrator API

```mermaid
C4Component
    title Orchestrator API — Diagrama de componentes (C4 nivel 3)
    Container(web, "Web App", "Nginx")
    Container(mon, "Monitor Worker", "Python")
    ContainerDb(db, "Estado compartido", "PostgreSQL")
    System_Ext(llm, "Proveedor LLM", "Claude / Ollama")
    Container_Boundary(api, "Orchestrator API") {
        Component(routes, "API Router", "FastAPI + Pydantic", "Valida HTTP y llama casos de uso")
        Component(orch, "Orchestrator", "Fachada + Unit of Work", "Carga estado, elige ruta, ejecuta grafo y persiste")
        Component(graph, "Grafo de agentes", "LangGraph StateGraph", "KairosState compartido; rutas plan / replan / monitor")
        Component(intake, "IntakeAgent", "LLM + reglas", "Lenguaje natural → tareas")
        Component(prio, "PrioritizerAgent", "Determinista", "Puntaje + cuadrante de Eisenhower")
        Component(sched, "SchedulerAgent", "Greedy", "Cronograma sin solapes; riesgo de incumplimiento")
        Component(monitor, "MonitorAgent", "Determinista", "Detecta tareas no iniciadas y sobrecostos")
        Component(coach, "CoachAgent", "LLM + plantilla", "Siguiente paso concreto")
        Component(llmp, "LLMProvider", "Strategy: Null / Ollama / Anthropic", "Abstracción del modelo")
        Component(repo, "Repository", "SQLAlchemy 2.0", "Mapea filas ↔ dominio; advisory lock")
        Component(clock, "Clock", "Reloj inyectable", "Hora real + desfase simulado compartido")
    }
    Rel(web, routes, "JSON", "HTTP")
    Rel(mon, orch, "monitor_tick()", "llamada en proceso")
    Rel(routes, orch, "usa")
    Rel(orch, graph, "invoke(state)")
    Rel(orch, repo, "carga / guarda")
    Rel(orch, clock, "now()")
    Rel(graph, intake, "nodo intake")
    Rel(graph, prio, "nodo prioritize")
    Rel(graph, sched, "nodo schedule")
    Rel(graph, monitor, "nodo monitor")
    Rel(graph, coach, "nodo coach")
    Rel(intake, llmp, "complete_json()")
    Rel(coach, llmp, "complete_text()")
    Rel(llmp, llm, "HTTPS")
    Rel(repo, db, "SQL")
    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

### Grafo de orquestación (LangGraph)

```mermaid
stateDiagram-v2
    [*] --> router
    router --> intake: mode = plan
    router --> prioritize: mode = replan
    router --> monitor: mode = monitor
    intake --> prioritize: hay tareas nuevas
    intake --> [*]: no entendió nada
    monitor --> prioritize: hay retrasos
    monitor --> [*]: todo en orden
    prioritize --> schedule
    schedule --> coach
    coach --> [*]
```

`KairosState` (estado compartido dentro del grafo):

| Campo | Tipo | Quién lo escribe |
|---|---|---|
| `mode` | `plan` \| `replan` \| `monitor` | Orquestador |
| `now` | `datetime` (reloj compartido) | Orquestador |
| `input_text` | `str` | API |
| `tasks` | `list[Task]` | Intake, Monitor, Prioritizer, Scheduler |
| `new_task_ids` | `list[str]` | Intake |
| `delays` | `list[dict]` | Monitor |
| `events` | `list[AgentEvent]` (reductor `operator.add`) | Todos (bitácora) |

---

## 3.5 C4 — Diagramas dinámicos

### a) Planificar desde lenguaje natural

```mermaid
C4Dynamic
    title Flujo dinámico 1 — Planificar desde lenguaje natural
    Person(user, "Usuario")
    Container(web, "Web App", "Nginx + JS")
    Container_Boundary(api, "Orchestrator API") {
        Component(routes, "API Router", "FastAPI")
        Component(orch, "Orchestrator", "Fachada")
        Component(intake, "IntakeAgent")
        Component(prio, "PrioritizerAgent")
        Component(sched, "SchedulerAgent")
        Component(coach, "CoachAgent")
    }
    ContainerDb(db, "PostgreSQL")
    RelIndex(1, user, web, "Escribe pendientes y pulsa Planificar")
    RelIndex(2, web, routes, "POST /api/plan {text}")
    RelIndex(3, routes, orch, "plan(text)")
    RelIndex(4, orch, db, "BEGIN + pg_advisory_xact_lock + cargar tareas")
    RelIndex(5, orch, intake, "texto → tareas (LLM o reglas)")
    RelIndex(6, orch, prio, "puntaje + cuadrante")
    RelIndex(7, orch, sched, "asignar franjas")
    RelIndex(8, orch, coach, "siguiente paso")
    RelIndex(9, orch, db, "guardar tareas + eventos; COMMIT")
    RelIndex(10, web, routes, "GET /api/state (cada 3 s)")
    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

### b) Detección de retraso y replanificación automática

```mermaid
C4Dynamic
    title Flujo dinámico 2 — Retraso detectado y replanificación
    Container(mon, "Monitor Worker", "Python")
    Container_Boundary(api, "Núcleo de orquestación (en proceso)") {
        Component(orch, "Orchestrator")
        Component(monitor, "MonitorAgent")
        Component(prio, "PrioritizerAgent")
        Component(sched, "SchedulerAgent")
        Component(coach, "CoachAgent")
    }
    ContainerDb(db, "PostgreSQL")
    Container(web, "Web App")
    Person(user, "Usuario")
    RelIndex(1, mon, orch, "monitor_tick() cada 15 s")
    RelIndex(2, orch, db, "lock + cargar tareas + desfase del reloj")
    RelIndex(3, orch, monitor, "¿tareas no iniciadas o pasadas de tiempo?")
    RelIndex(4, orch, prio, "re-puntuar (bono por retraso)")
    RelIndex(5, orch, sched, "reubicar desde ahora; marcar riesgo")
    RelIndex(6, orch, coach, "mensaje de ánimo + siguiente paso")
    RelIndex(7, orch, db, "guardar plan + eventos")
    RelIndex(8, web, orch, "GET /api/state → snapshot() con el nuevo plan")
    RelIndex(9, web, user, "Ve el plan reorganizado y la bitácora")
    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

La misma interacción como diagrama de secuencia:

```mermaid
sequenceDiagram
    autonumber
    participant W as Monitor Worker
    participant O as Orchestrator
    participant DB as PostgreSQL
    participant M as MonitorAgent
    participant P as PrioritizerAgent
    participant S as SchedulerAgent
    participant C as CoachAgent
    loop cada MONITOR_INTERVAL_SECONDS
        W->>O: monitor_tick()
        O->>DB: BEGIN + pg_advisory_xact_lock(4242)
        O->>DB: SELECT tasks, settings
        O->>M: run(tasks, now)
        alt hay retrasos
            M-->>O: delays (+delay_count)
            O->>P: run(tasks, now)
            O->>S: run(tasks, now)
            S-->>O: nuevo cronograma + riesgos
            O->>C: run(tasks, now, replanned=True)
        else sin retrasos
            M-->>O: []
        end
        O->>DB: UPSERT tasks + INSERT agent_events + COMMIT
    end
```

---

## 3.6 C4 — Diagrama de despliegue

```mermaid
C4Deployment
    title Kairos — Diagrama de despliegue (Docker Compose)
    Deployment_Node(client, "Equipo del usuario", "Windows / macOS / Linux") {
        Deployment_Node(browser, "Navegador", "Chrome / Edge / Firefox") {
            Container(spa, "Kairos UI", "HTML/CSS/JS", "Consulta /api/state cada 3 s")
        }
    }
    Deployment_Node(host, "Host Docker", "Docker Engine 28 + Compose v2") {
        Deployment_Node(cweb, "kairos-web-1", "nginx:1.27-alpine · red frontend · :8080→80") {
            Container(web, "Web + Proxy", "Nginx")
        }
        Deployment_Node(capi, "kairos-orchestrator-1", "python:3.12-slim · redes frontend+backend · :8000") {
            Container(api, "Orchestrator API", "Uvicorn + FastAPI")
        }
        Deployment_Node(cmon, "kairos-monitor-1", "python:3.12-slim · red backend") {
            Container(mon, "Monitor Worker", "python -m app.worker")
        }
        Deployment_Node(cdb, "kairos-db-1", "postgres:16-alpine · red backend · volumen pgdata") {
            ContainerDb(db, "PostgreSQL", "tasks, agent_events, settings")
        }
        Deployment_Node(cllm, "kairos-ollama-1 (perfil llm)", "ollama/ollama · volumen ollama") {
            Container(ollama, "Ollama", "qwen2.5:3b")
        }
    }
    System_Ext(anthropic, "Anthropic API", "api.anthropic.com")
    Rel(spa, web, "HTTP", ":8080")
    Rel(web, api, "proxy /api", ":8000")
    Rel(api, db, "SQL", ":5432")
    Rel(mon, db, "SQL", ":5432")
    Rel(api, ollama, "HTTP", ":11434")
    Rel(api, anthropic, "HTTPS", ":443")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

**Decisiones de despliegue**
- **Dos redes**: `frontend` (web ↔ API) y `backend` (API, monitor, BD, Ollama). La BD no queda expuesta al host.
- **Misma imagen, dos procesos**: la API y el monitor comparten código (`kairos/orchestrator:1.0`). Escalan y fallan por separado.
- **Health checks + `depends_on: condition: service_healthy`**: la API espera a la BD y la web espera a la API.
- **Volúmenes**: `pgdata` (persistencia) y `ollama` (modelos descargados).
- **Configuración 12-Factor**: todo por variables de entorno (`.env.example`).

---

## 3.7 Diagramas de paquetes UML por componente

> Mermaid no tiene diagrama de paquetes nativo. Abajo va una aproximación con subgrafos (los paquetes) y flechas punteadas «import». Los diagramas UML formales están en `docs/diagrams/paquetes-*.puml`.

### a) Componente `orchestrator` (API)

```mermaid
flowchart TB
    subgraph app["📦 app"]
        main["main<br/>(composition root)"]
        config["config"]
        worker["worker"]
        subgraph api["📦 app.api"]
            routes["routes"]
        end
        subgraph orchestration["📦 app.orchestration"]
            orchestrator["orchestrator"]
            graphm["graph"]
        end
        subgraph agents["📦 app.agents"]
            base["base"]
            intake["intake"]
            prioritizer["prioritizer"]
            scheduler["scheduler"]
            monitor["monitor"]
            coach["coach"]
        end
        subgraph domain["📦 app.domain"]
            models["models"]
            clock["clock"]
        end
        subgraph infrastructure["📦 app.infrastructure"]
            db["db"]
            repository["repository"]
            llm["llm"]
        end
    end
    main -.->|«import»| api
    main -.->|«import»| orchestration
    main -.->|«import»| infrastructure
    main -.->|«import»| config
    worker -.->|«import»| main
    api -.->|«import»| orchestration
    orchestration -.->|«import»| agents
    orchestration -.->|«import»| infrastructure
    orchestration -.->|«import»| domain
    agents -.->|«import»| domain
    agents -.->|«import»| llm
    repository -.->|«import»| domain
```

**Regla de dependencias:** `domain` no depende de nadie. `agents` solo depende de `domain` y de la abstracción `llm`. La infraestructura se conecta en `main`. Es una arquitectura por capas con el núcleo funcional al centro (estilo hexagonal ligero).

### b) Componente `monitor` (worker)

```mermaid
flowchart LR
    subgraph monitorpkg["📦 kairos-monitor (contenedor)"]
        w["app.worker<br/>bucle + señales SIGTERM"]
    end
    subgraph shared["📦 app (código compartido con la API)"]
        m["app.main.build_orchestrator"]
        o["app.orchestration"]
        a["app.agents.monitor"]
    end
    w -.->|«import»| m
    m -.->|«import»| o
    o -.->|«import»| a
```

### c) Componente `web`

```mermaid
flowchart LR
    subgraph webpkg["📦 web (contenedor nginx)"]
        conf["nginx.conf<br/>proxy /api → orchestrator:8000"]
        html["index.html"]
        css["styles.css"]
        subgraph js["📦 app.js"]
            apic["cliente API<br/>call(), action()"]
            render["render<br/>renderTimeline, renderEvents, renderStats"]
            ui["controladores UI<br/>formulario, botones"]
        end
    end
    html -.->|«use»| css
    html -.->|«use»| js
    ui -.-> apic
    ui -.-> render
    apic -.->|HTTP| conf
```

### d) Componente `db` (esquema)

```mermaid
erDiagram
    TASKS {
        varchar id PK
        varchar title
        varchar category
        int estimated_minutes
        int importance
        timestamptz deadline
        timestamptz fixed_start
        varchar status
        float priority_score
        varchar quadrant
        text rationale
        timestamptz scheduled_start
        timestamptz scheduled_end
        int delay_count
        bool at_risk
    }
    AGENT_EVENTS {
        int id PK
        timestamptz ts
        varchar agent
        varchar kind
        text message
        json payload
    }
    SETTINGS {
        varchar key PK
        varchar value
    }
```

---

## 3.8 Decisiones de arquitectura (ADR resumidos)

| ADR | Decisión | Alternativas | Motivo |
|---|---|---|---|
| 001 | Agentes **en proceso**, orquestados con LangGraph | Un microservicio por agente con un bus (Kafka/RabbitMQ) | Menos latencia y operación más simple para el alcance. El grafo ya aísla responsabilidades. **Evolución**: separar agentes en servicios si crece la carga. |
| 002 | **Estado compartido en PostgreSQL** (pizarra) | Redis; memoria | Transacciones + `advisory lock` dan consistencia entre la API y el monitor. Se persiste para auditar la bitácora. |
| 003 | **LLM opcional** con degradación a reglas | Depender 100 % del LLM | Disponibilidad, costo y reproducibilidad. La demo funciona sin internet ni llaves. |
| 004 | Prioridad y agenda **deterministas** | Pedírselas al LLM | Explicables, comprobables con pruebas y sin alucinaciones aritméticas |
| 005 | **Monitor en contenedor aparte** | Tarea en segundo plano dentro de la API | Aislamiento de fallos y escalado independiente. La API sigue sin estado. |
| 006 | **Reloj con desfase compartido** | Esperar tiempo real | Permite demostrar retrasos en vivo (`+30 min`, `+2 h`) de forma reproducible |
| 007 | UI sin framework | React/Vue | El foco del curso es la arquitectura. Cero pasos de build. Las fuentes (Inter) y los íconos (Lucide) se sirven desde el contenedor, sin CDN, así que la UI funciona sin internet. Las animaciones usan una API nativa del navegador (View Transitions). |

---

## 3.9 API REST

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Estado y proveedor de LLM |
| GET | `/api/state` | Hora (real o simulada), tareas, eventos y métricas |
| POST | `/api/plan` | `{text}` → ruta `plan` |
| POST | `/api/replan` | Ruta `replan` |
| POST | `/api/tasks/{id}/start` · `/complete` | Acción + replanificación |
| DELETE | `/api/tasks/{id}` | Eliminar tarea |
| POST | `/api/clock/advance` | `{minutes}`: simula el paso del tiempo y fuerza un ciclo del monitor |
| PUT | `/api/settings` | Jornada laboral y descansos |
| POST | `/api/reset` | Borra todo (demo) |

Documentación interactiva (Swagger): `http://localhost:8000/docs`.
