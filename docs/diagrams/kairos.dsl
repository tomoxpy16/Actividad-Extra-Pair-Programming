/*
 * Kairos — modelo C4 en Structurizr DSL.
 * Pegar en https://playground.structurizr.com  (o abrir con Structurizr Lite).
 * Un solo modelo genera todas las vistas: contexto, contenedores, componentes,
 * dos dinámicas y despliegue. Si cambia el modelo, cambian todas las vistas.
 */
workspace "Kairos" "Orquestador multiagente de productividad personal" {

    !identifiers hierarchical
    !impliedRelationships false

    model {
        usuario = person "Usuario" "Estudiante o profesional que quiere organizar su tiempo."

        anthropic = softwareSystem "Anthropic API" "Modelos Claude. Opcional: LLM_PROVIDER=anthropic." "Externo"

        kairos = softwareSystem "Kairos" "Entiende pendientes en lenguaje natural, los prioriza, arma el cronograma, vigila retrasos y replanifica." {

            spa = container "Interfaz web" "Captura el texto del usuario, muestra cronograma, métricas y bitácora de agentes. Consulta el estado cada 3 s." "HTML, CSS, JavaScript" "Navegador"

            proxy = container "Servidor web y proxy" "Entrega la interfaz y redirige /api/* al orquestador (mismo origen, sin CORS)." "Nginx 1.27"

            api = container "Orchestrator API" "Casos de uso: planificar, replanificar, iniciar/completar tareas y reloj simulado. Ejecuta el grafo de agentes." "Python 3.12, FastAPI, LangGraph" {
                routes = component "API Router" "Valida HTTP con Pydantic y delega en el orquestador." "FastAPI"
                orch = component "Orchestrator" "Fachada + unidad de trabajo: bloquea, carga el estado, elige la ruta del grafo y persiste." "Python"
                graph = component "Grafo de agentes" "Estado compartido KairosState; rutas plan, replan y monitor." "LangGraph StateGraph"
                intake = component "IntakeAgent" "Lenguaje natural -> tareas estructuradas." "LLM + reglas" "Agente"
                prio = component "PrioritizerAgent" "Puntaje 0-100, cuadrante de Eisenhower y explicación." "Determinista" "Agente"
                sched = component "SchedulerAgent" "Cronograma sin solapes dentro de la jornada; marca riesgo de incumplimiento." "Greedy" "Agente"
                mon = component "MonitorAgent" "Detecta tareas no iniciadas y tareas pasadas de tiempo." "Determinista" "Agente"
                coach = component "CoachAgent" "Redacta el siguiente paso concreto para el usuario." "LLM + plantilla" "Agente"
                llm = component "LLMProvider" "Abstracción del modelo: Null, Ollama o Anthropic (Strategy)." "Python ABC"
                repo = component "Repository" "Traduce filas <-> dominio y toma el advisory lock." "SQLAlchemy 2.0"
                clock = component "Clock" "Hora real + desfase simulado compartido." "Python"
            }

            monitor = container "Monitor Worker" "Proceso independiente que ejecuta el ciclo del MonitorAgent cada 15 s con el mismo código del orquestador." "Python 3.12" "Worker"

            db = container "Estado compartido" "Pizarra (blackboard): tareas, eventos de agentes y configuración." "PostgreSQL 16" "BaseDeDatos"

            ollama = container "Ollama" "LLM local de pesos abiertos (perfil llm)." "Ollama + qwen2.5:3b" "Opcional"
        }

        # --- Nivel contenedores (explícitas: las relaciones implícitas están apagadas)
        usuario -> kairos.spa "Escribe pendientes, inicia y completa tareas"
        usuario -> kairos.proxy "Abre http://localhost:8080" "HTTP"
        kairos.proxy -> kairos.spa "Entrega los archivos estáticos" "HTTP"
        kairos.spa -> kairos.proxy "Llama /api/*" "JSON/HTTP"
        kairos.proxy -> kairos.api "Redirige /api/*" "HTTP :8000"
        kairos.api -> kairos.db "Lee y escribe con bloqueo consultivo" "SQL"
        kairos.monitor -> kairos.db "Lee y escribe con bloqueo consultivo" "SQL"
        kairos.api -> kairos.ollama "Extrae tareas / redacta mensajes" "HTTP/JSON"
        kairos.api -> anthropic "Extrae tareas / redacta mensajes" "HTTPS + JSON Schema"
        kairos.monitor -> anthropic "Mensajes del CoachAgent" "HTTPS"

        # --- Nivel contexto
        usuario -> kairos "Organiza su día con"
        kairos -> anthropic "Usa modelos de lenguaje de"

        # --- Nivel componentes
        kairos.proxy -> kairos.api.routes "Redirige /api/*" "HTTP"
        kairos.monitor -> kairos.api.orch "Ejecuta monitor_tick() (mismo código, su propio proceso)"
        kairos.api.routes -> kairos.api.orch "plan(), replan(), task_action(), snapshot()"
        kairos.api.orch -> kairos.api.repo "Carga y guarda el estado"
        kairos.api.orch -> kairos.api.clock "Consulta la hora"
        kairos.api.orch -> kairos.api.graph "invoke(state)"
        kairos.api.graph -> kairos.api.intake "Nodo intake"
        kairos.api.graph -> kairos.api.mon "Nodo monitor"
        kairos.api.graph -> kairos.api.prio "Nodo prioritize"
        kairos.api.graph -> kairos.api.sched "Nodo schedule"
        kairos.api.graph -> kairos.api.coach "Nodo coach"
        kairos.api.intake -> kairos.api.llm "complete_json()"
        kairos.api.coach -> kairos.api.llm "complete_text()"
        kairos.api.llm -> anthropic "Mensajes con salida estructurada" "HTTPS"
        kairos.api.llm -> kairos.ollama "/api/chat" "HTTP"
        kairos.api.repo -> kairos.db "SELECT / UPSERT + pg_advisory_xact_lock" "SQL"

        # --- Despliegue
        local = deploymentEnvironment "Docker Compose" {
            deploymentNode "Equipo del usuario" "" "Windows, macOS o Linux" {
                deploymentNode "Navegador" "" "Chrome, Edge o Firefox" {
                    containerInstance kairos.spa
                }
                deploymentNode "Docker Desktop" "" "Docker Engine 28 + Compose v2" {
                    deploymentNode "kairos-web-1" "Red frontend · puerto 8080 -> 80" "nginx:1.27-alpine" {
                        containerInstance kairos.proxy
                    }
                    deploymentNode "kairos-orchestrator-1" "Redes frontend + backend · puerto 8000 · usuario no-root" "python:3.12-slim" {
                        containerInstance kairos.api
                    }
                    deploymentNode "kairos-monitor-1" "Red backend" "python:3.12-slim" {
                        containerInstance kairos.monitor
                    }
                    deploymentNode "kairos-db-1" "Red backend · volumen pgdata" "postgres:16-alpine" {
                        containerInstance kairos.db
                    }
                    deploymentNode "kairos-ollama-1" "Perfil llm · volumen ollama" "ollama/ollama" {
                        containerInstance kairos.ollama
                    }
                }
            }
            deploymentNode "Anthropic" "" "Nube (api.anthropic.com)" {
                softwareSystemInstance anthropic
            }
        }
    }

    views {
        systemContext kairos "C1-Contexto" "Kairos y su entorno." {
            include *
            autolayout lr
        }

        container kairos "C2-Contenedores" "Contenedores de Kairos." {
            include *
            autolayout lr
        }

        component kairos.api "C3-Componentes" "Componentes del Orchestrator API: cinco agentes coordinados por un grafo con estado compartido." {
            include *
            autolayout tb
        }

        dynamic kairos.api "D1-Planificar" "Flujo dinámico 1: planificar desde lenguaje natural." {
            usuario -> kairos.spa "Escribe sus pendientes y pulsa Planificar"
            kairos.spa -> kairos.proxy "POST /api/plan {text}"
            kairos.proxy -> kairos.api.routes "Redirige la petición"
            kairos.api.routes -> kairos.api.orch "plan(text)"
            kairos.api.orch -> kairos.api.repo "BEGIN + lock + cargar tareas"
            kairos.api.repo -> kairos.db "SELECT tasks, settings"
            kairos.api.orch -> kairos.api.graph "invoke(mode=plan)"
            kairos.api.graph -> kairos.api.intake "Texto -> tareas"
            kairos.api.graph -> kairos.api.prio "Puntaje + cuadrante"
            kairos.api.graph -> kairos.api.sched "Asignar franjas"
            kairos.api.graph -> kairos.api.coach "Siguiente paso"
            kairos.api.orch -> kairos.api.repo "Guardar tareas y eventos"
            kairos.api.repo -> kairos.db "UPSERT + INSERT + COMMIT"
            autolayout lr
        }

        dynamic kairos.api "D2-Replanificar" "Flujo dinámico 2: el monitor detecta un retraso y el plan se reorganiza." {
            kairos.monitor -> kairos.api.orch "monitor_tick() cada 15 s"
            kairos.api.orch -> kairos.api.repo "BEGIN + lock + cargar tareas"
            kairos.api.repo -> kairos.db "SELECT tasks, settings (desfase del reloj)"
            kairos.api.orch -> kairos.api.graph "invoke(mode=monitor)"
            kairos.api.graph -> kairos.api.mon "¿No iniciadas o pasadas de tiempo?"
            kairos.api.graph -> kairos.api.prio "Re-puntuar con bono por retraso"
            kairos.api.graph -> kairos.api.sched "Reubicar desde ahora y marcar riesgo"
            kairos.api.graph -> kairos.api.coach "Mensaje de ánimo + siguiente paso"
            kairos.api.orch -> kairos.api.repo "Guardar plan y eventos"
            kairos.api.repo -> kairos.db "UPSERT + INSERT + COMMIT"
            autolayout lr
        }

        deployment kairos local "Despliegue" "Despliegue local con Docker Compose." {
            include *
            autolayout lr
        }

        styles {
            element "Element" {
                fontSize 22
            }
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "Agente" {
                background #c7d2fe
                color #1e1b4b
                shape RoundedBox
            }
            element "Navegador" {
                shape WebBrowser
            }
            element "BaseDeDatos" {
                shape Cylinder
            }
            element "Worker" {
                shape Hexagon
            }
            element "Externo" {
                background #999999
                color #ffffff
            }
            element "Opcional" {
                border dashed
                opacity 70
            }
            relationship "Relationship" {
                fontSize 20
            }
        }
    }
}
