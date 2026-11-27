# 1. Marco teórico — Pair Programming con IA

> **Tema asignado:** Pair Programming IA: colaboración entre humanos y copilotos de IA (GitHub Copilot, Cursor) en el flujo de desarrollo.
>
> Para explicarlo bien hay que separar cinco temas que suelen confundirse. Van de "más control humano" a "menos código visible":
>
> 1. [Pair programming clásico (programación a cuatro manos)](#tema-1--pair-programming-clásico-programación-a-cuatro-manos)
> 2. [Pair programming con IA (copilotos)](#tema-2--pair-programming-con-ia-copilotos)
> 3. [Agentes de IA de codificación (la IA que asume un rol)](#tema-3--agentes-de-ia-de-codificación)
> 4. [Vibe coding](#tema-4--vibe-coding)
> 5. [No-code / low-code](#tema-5--no-code--low-code)
>
> Cada tema sigue la misma estructura: definición, características, historia y evolución, ventajas y desventajas, casos de uso y casos de aplicación. Las cifras llevan fuente al final ([Referencias](#referencias)). Las que publica el propio fabricante de la herramienta están marcadas como *dato del proveedor*.

---

## Tema 1 — Pair programming clásico (programación a cuatro manos)

### Definición
El **pair programming** (programación en pareja o *a cuatro manos*) es una práctica ágil en la que **dos personas desarrollan juntas, en un solo equipo de cómputo y sobre la misma tarea**. Se habla de "cuatro manos" porque hay dos cerebros y un solo teclado: el código que entra al repositorio lo pensaron y lo revisaron dos personas en tiempo real.

### Los dos roles

| Rol | También llamado | Qué hace | Horizonte |
|---|---|---|---|
| **Driver** | Conductor, piloto | Tiene el teclado. Escribe el código, se concentra en la sintaxis y en el paso inmediato. Piensa en voz alta. | Táctico: la línea, la función |
| **Navigator** | Navegante, copiloto, observador | Revisa cada línea mientras se escribe, detecta errores, piensa en casos límite, en el diseño y en el siguiente paso. No dicta tecla por tecla. | Estratégico: el módulo, la arquitectura, el objetivo |

Los roles **se intercambian con frecuencia**, cada 15–30 minutos, al terminar un pomodoro o con cada prueba en TDD. Si nunca rotan, deja de ser pair programming: uno trabaja y el otro mira.

### Características
- Una tarea, una pantalla, un teclado. En remoto se usa pantalla compartida o un editor colaborativo.
- Conversación continua: el navegante pregunta "¿por qué?" y el conductor explica.
- Revisión de código **continua**, no al final.
- Rotación de roles y, en equipos maduros, también de parejas (*pair rotation*) para repartir el conocimiento.
- Variantes:
  - **Ping-pong pairing**: con TDD, A escribe una prueba que falla, B la hace pasar y escribe la siguiente prueba, y así sucesivamente.
  - **Strong-style pairing** (Llewellyn Falco): una idea solo entra al computador a través de las manos del *otro*. Obliga a explicar.
  - **Experto–novato**: mentoría acelerada.
  - **Remote pairing**: VS Code Live Share, Tuple, JetBrains Code With Me.
  - **Mob / ensemble programming** (Woody Zuill): todo el equipo en una sola pantalla, con un driver que rota.

### Historia y evolución

| Año | Hito |
|---|---|
| 1950s | Fred Brooks contó que programaba en pareja con un colega cuando era estudiante de posgrado. Era práctica informal. |
| 1995 | Larry Constantine describe los *Dynamic Duos* y Jim Coplien publica el patrón organizacional *Developing in Pairs*. |
| 1996–1999 | Kent Beck la formaliza como práctica central de **Extreme Programming (XP)** en el proyecto C3 de Chrysler. En 1999 publica *Extreme Programming Explained*. |
| 2000 | Cockburn y Williams, *The Costs and Benefits of Pair Programming*: las parejas gastan cerca de un 15 % más de horas-persona y entregan alrededor de un 15 % menos defectos, con mejor diseño y más satisfacción. |
| 2002 | Williams y Kessler publican *Pair Programming Illuminated*. |
| 2007–2009 | Arisholm et al. (295 consultores) y el metaanálisis de Hannay et al.: el beneficio **depende de la complejidad de la tarea y de la experiencia**. Mejora la calidad en tareas complejas y cuesta más esfuerzo en tareas simples. |
| 2011–2014 | Surgen el *mob programming* (Hunter Industries) y las herramientas de pairing remoto. |
| 2017–2020 | VS Code Live Share (2017–2018) y la pandemia normalizan el pairing remoto. |
| **2021 →** | GitHub Copilot se presenta como *"Your AI pair programmer"*: **el navegante (o el conductor) puede ser una IA**. Ver Tema 2. |

### Ventajas y desventajas

| Ventajas | Desventajas |
|---|---|
| Menos defectos: la revisión ocurre mientras se escribe | Más horas-persona por tarea (~15 % según Cockburn & Williams) |
| Mejor diseño: dos perspectivas | Agotador. Exige concentración social continua |
| Transferencia de conocimiento; reduce el *bus factor* | Choques de personalidad o de ritmo |
| Onboarding y mentoría acelerados | Poco eficiente en tareas triviales o muy exploratorias |
| Disciplina: menos distracciones y menos atajos | Difícil de medir y de "vender" a la gerencia |
| Propiedad colectiva del código | En remoto depende de la conectividad y de las herramientas |

### Casos de uso (cuándo aplicarlo)
- Lógica crítica o compleja: pagos, seguridad, concurrencia, algoritmos.
- Incorporar a una persona nueva al equipo o a un código desconocido.
- Depurar un bug difícil (*rubber duck* con un pato que responde).
- Decisiones de diseño o refactorizaciones grandes.
- Practicar TDD (ping-pong).
- **No conviene** para tareas mecánicas, investigación individual o lecturas largas.

### Casos de aplicación (industria)
- **Pivotal Labs**, hoy VMware Tanzu Labs: hizo del pairing a tiempo completo su forma estándar de trabajo con clientes.
- **Menlo Innovations** (EE. UU.): todo el desarrollo se hace en parejas que rotan semanalmente. Lo documenta Rich Sheridan en *Joy, Inc.* (2013).
- **ThoughtWorks**: lo promueve como práctica de XP en sus proyectos de consultoría.
- **Hunter Industries**: origen del *mob programming*, una extensión del pairing a todo el equipo.

---

## Tema 2 — Pair programming con IA (copilotos)

### Definición
**AI pair programming** es la práctica de trabajar en pareja con un **asistente de IA integrado en el editor o la terminal** que ocupa uno de los dos roles del pair programming. La IA propone código, explica, revisa y genera pruebas. **El humano conserva la responsabilidad**: entiende, acepta o rechaza cada cambio.

La regla que lo distingue del *vibe coding* (Tema 4): **el humano lee y comprende todo el código que entra al repositorio.**

### Características
- **Integración en el flujo**: autocompletado en línea (*ghost text*), chat contextual, edición de varios archivos, revisión de PR.
- **Contexto del repositorio**: indexación del código (embeddings), archivos abiertos, reglas del proyecto (`AGENTS.md`, `.github/copilot-instructions.md`, `.cursor/rules/`).
- **Multi-modelo**: el usuario elige el LLM (GPT, Claude, Gemini, modelos abiertos).
- **Asimetría**: la IA no se cansa ni se ofende, pero tampoco conoce el negocio ni rinde cuentas.
- **Roles intercambiables** (ver el mapa de roles del Tema 3).

### Herramientas representativas

| Herramienta | Empresa | Forma | Rasgo distintivo |
|---|---|---|---|
| **GitHub Copilot** | GitHub / Microsoft | Extensión (VS Code, JetBrains, Visual Studio, Xcode…), CLI, web | Autocompletado + Chat + *agent mode* + *coding agent* que abre PR. Multi-modelo. |
| **Cursor** | Anysphere | Editor (fork de VS Code) | Diseñado alrededor de la IA: *Tab*, *Agent*, reglas por proyecto, indexación del repo |
| **Windsurf** | Codeium → Cognition (2025) | Editor | Agente *Cascade* |
| **Claude Code** | Anthropic | Terminal, IDE, desktop, web | Agente que lee el repo, edita y ejecuta comandos con permisos |
| **OpenAI Codex** | OpenAI | CLI + agente en la nube | Delegación asíncrona de tareas |
| **Gemini Code Assist / Gemini CLI** | Google | Extensión + CLI | Integración con Google Cloud |
| **Amazon Q Developer** | AWS | Extensión + agentes | Transformación de código (p. ej., actualizar versiones de Java) |
| **JetBrains AI Assistant / Junie** | JetBrains | IDE | Integración nativa en IntelliJ, PyCharm… |
| **Aider, Cline, Continue** | Código abierto | CLI / extensión | Permiten usar modelos locales u otros proveedores. Aider se define como *AI pair programming in your terminal*. |
| **Tabnine** | Tabnine | Extensión | Despliegue privado / on-premise |

### Historia y evolución

| Año | Hito |
|---|---|
| 1996–2015 | Autocompletado sintáctico (IntelliSense) y estadístico (Kite, 2014). |
| 2018–2019 | Tabnine usa modelos de lenguaje (GPT-2) para completar código. |
| **Jun 2021** | **GitHub Copilot** (preview), basado en **OpenAI Codex** y presentado como *"Your AI pair programmer"*. En julio sale el paper de Codex con el benchmark **HumanEval**. |
| Jun 2022 | Copilot disponible para todos (GA). Amazon CodeWhisperer en preview. |
| Nov 2022 | ChatGPT: el chat se vuelve herramienta de programación. |
| 2023 | Copilot Chat. Nace **Cursor**. Primeros estudios controlados de productividad. |
| 2024 | Copilot multi-modelo (Claude, Gemini, GPT). Amazon Q Developer. Aparecen los IDE "agénticos" (Windsurf). |
| 2025 | **Agent mode** en Copilot, VS Code y Cursor. Agentes asíncronos que abren PR (Copilot coding agent, Codex, Jules). Claude Code y Gemini CLI. Copilot alcanza **20 millones de usuarios acumulados** (jul. 2025). |
| 2026 | Copilot reporta **4,7 millones de suscriptores de pago** (ene. 2026). La conversación pasa de "autocompletar" a "orquestar varios agentes". |

### Ventajas y desventajas

| Ventajas | Desventajas / riesgos |
|---|---|
| **Velocidad en tareas acotadas.** En un experimento controlado, quienes usaron Copilot terminaron un servidor HTTP **55,8 % más rápido** (Peng et al., 2023). | **No siempre acelera.** En el RCT de METR (2025), desarrolladores *expertos* en sus propios repos fueron **19 % más lentos** con IA, aunque creían ir un 20 % más rápido. |
| Elimina código repetitivo: boilerplate, pruebas, documentación, migraciones | **Código "casi correcto"**: errores sutiles y APIs inventadas (alucinaciones) |
| Disponible 24/7, sin fatiga social | **Seguridad**: cerca del 40 % de los programas generados por Copilot en escenarios sensibles tenían vulnerabilidades (Pearce et al., 2021) |
| Aprendizaje: explica código y tecnologías nuevas | **Sobreconfianza** (*automation bias*) y pérdida de habilidades en juniors |
| Estandariza el estilo si se definen reglas | Privacidad y propiedad intelectual del código; licencias |
| Mejora la experiencia (*flow*) y reduce la frustración | **Confianza baja**: solo el 33 % confía en la precisión de la IA y el 46 % desconfía (Stack Overflow 2025) |
| | DORA 2024: más adopción de IA se asoció con **menor estabilidad** en las entregas (−7,2 %) |

### Casos de uso
- Escribir pruebas unitarias a partir de una especificación o de código existente.
- Boilerplate: DTO, endpoints CRUD, Dockerfiles, configuración de CI.
- Entender un código heredado ("explícame este módulo").
- Refactorizaciones guiadas con la red de seguridad de las pruebas.
- Traducción entre lenguajes o frameworks y migraciones de versión.
- Revisión previa de PR, documentación y mensajes de commit.

### Casos de aplicación (industria)
- **Accenture + GitHub** (estudio en empresa, 2024): **+8,69 % de pull requests**, **+15 % en tasa de merge** y **+84 % de builds exitosos** con Copilot. *Dato del proveedor.*
- **Mercado Libre** (LatAm): Copilot para toda su organización de desarrollo, con una reducción reportada cercana al **50 % del tiempo dedicado a escribir código**. *Dato del proveedor.*
- **Google**: Sundar Pichai afirmó (oct. 2024) que **más del 25 % del código nuevo** en Google lo genera la IA y luego lo revisan ingenieros.
- **Microsoft**: Satya Nadella estimó (2025) que entre **20 % y 30 %** del código de sus repositorios lo escribe la IA.
- **Bancos argentinos (Galicia, Naranja X)**: adopción de Copilot en el sector financiero (Microsoft LatAm).

---

## Tema 3 — Agentes de IA de codificación

### Definición
Un **agente de IA** es un sistema en el que un modelo de lenguaje **decide y ejecuta acciones en un ciclo** para cumplir un objetivo:

```
objetivo ─► [ percibir (leer código, errores) ─► planear ─► actuar (editar, ejecutar, buscar) ─► observar resultado ] ─► ... ─► entrega
```

A diferencia del autocompletado, el agente **usa herramientas**: lee y escribe archivos, ejecuta pruebas y comandos, busca en la web y consulta servidores **MCP**. Puede iterar hasta que las pruebas pasen. Es la pieza que permite que la IA **asuma cualquiera de los dos roles** del pair programming.

### Anatomía de un agente de codificación

| Componente | Función | Ejemplo |
|---|---|---|
| **Modelo (LLM)** | Razonar, planear, escribir código | Claude Sonnet/Opus, GPT-5, Gemini 2.5 Pro, Qwen3-Coder, DeepSeek |
| **Instrucciones / reglas** | Contexto estable del proyecto: estilo, arquitectura, comandos | `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.cursor/rules/*.mdc` |
| **Herramientas** | Actuar sobre el entorno | Leer/editar archivos, terminal, búsqueda, navegador, **MCP** (Model Context Protocol, 2024) |
| **Contexto / memoria** | Saber qué hay en el repo y qué se decidió | Indexación semántica, historial, notas del proyecto |
| **Bucle de control** | Repetir hasta cumplir o pedir ayuda | Patrón ReAct, *plan-and-execute*, *reflection* |
| **Permisos y sandbox** | Limitar el daño posible | Aprobación de comandos, contenedores, ramas aisladas |
| **Humano en el ciclo** | Validar, decidir, rendir cuentas | Revisión de diffs, aprobación de PR |

### ¿Cómo hace la IA cada rol?

| Modalidad | Driver | Navigator | Cómo se ve en la práctica | Herramientas |
|---|---|---|---|---|
| **IA navegante** | Humano | IA | El humano escribe. La IA sugiere en línea, advierte errores, propone casos de prueba y responde dudas. | Copilot (completado + chat), Cursor *Tab/Ask*, JetBrains AI |
| **IA conductora** | IA | Humano | El humano fija el objetivo y las restricciones. El agente edita varios archivos y ejecuta pruebas. El humano revisa cada diff, corrige el rumbo y aprueba. | Cursor *Agent*, Copilot *agent mode*, Claude Code, Windsurf, Aider, Cline |
| **Ping-pong humano–IA** | Alternan | Alternan | El humano escribe la prueba que falla y la IA la hace pasar. Luego la IA propone la siguiente prueba y el humano implementa. | Cualquiera con chat + terminal |
| **Delegación asíncrona** | IA (sola) | Humano (en el PR) | Se asigna un *issue* al agente, que abre un PR en una rama. El humano lo revisa como el de un colega. Se parece más a un *code review* que a un pairing. | Copilot coding agent, OpenAI Codex, Devin, Jules |
| **Multiagente** | Varios agentes | Humano orquestador | Un agente planifica, otro implementa, otro revisa o prueba. El humano supervisa. | Subagentes de Claude Code, *background agents* de Cursor, frameworks como LangGraph o CrewAI |

> Para que una IA haga bien de **navegante** necesita contexto del objetivo (reglas, issue, arquitectura) y permiso para *contradecir*. Para que haga bien de **conductora** necesita herramientas (terminal, pruebas), límites (sandbox, aprobaciones) y una "definición de terminado" verificable, normalmente pruebas automatizadas.

### Modelos que permiten el pair programming con IA

| Familia | Proveedor | Tipo | Notas |
|---|---|---|---|
| GPT-4.1 / GPT-5 / o-series / Codex | OpenAI | Propietario | Base histórica de Copilot (Codex, 2021) |
| Claude (Sonnet, Opus, Haiku) | Anthropic | Propietario | Muy usado en modo agente (Cursor, Copilot, Claude Code) |
| Gemini 2.5 Pro / Flash | Google | Propietario | Contexto largo; Gemini CLI y Code Assist |
| Qwen2.5-Coder / Qwen3-Coder | Alibaba | Pesos abiertos | Se puede correr localmente (Ollama) |
| DeepSeek-V3 / R1 / Coder | DeepSeek | Pesos abiertos | Bajo costo |
| Codestral / Devstral | Mistral | Pesos abiertos / comercial | Orientados a código |
| StarCoder2, Code Llama | BigCode / Meta | Abiertos | Investigación y despliegue privado |

**Cómo se comparan**: *HumanEval* (2021) mide funciones aisladas. *SWE-bench* (2023) y *SWE-bench Verified* (2024) miden la resolución de issues reales de GitHub, que es lo relevante para agentes. *Terminal-Bench* mide el trabajo en terminal.

### Características
- Autonomía graduable, desde sugerir hasta abrir un PR solo.
- Verificación por herramientas: ejecuta pruebas y linters y corrige.
- Dependencia fuerte del **contexto**: un agente sin reglas ni pruebas produce resultados mediocres.
- Interoperabilidad mediante **MCP** y archivos de reglas estándar (`AGENTS.md`).

### Historia y evolución

| Año | Hito |
|---|---|
| 2022–2023 | Patrones ReAct (razonar + actuar), AutoGPT. **Aider** (2023), pair programming en terminal. |
| Mar 2024 | Cognition presenta **Devin**, *"AI software engineer"*. SWE-agent (Princeton) y OpenDevin/OpenHands en código abierto. |
| Ago 2024 | SWE-bench Verified se vuelve la referencia. |
| Nov 2024 | Anthropic publica **MCP** (Model Context Protocol). |
| 2025 | "El año de los agentes": *agent mode* en Copilot y Cursor, Claude Code, Codex, Gemini CLI. Agentes asíncronos que abren PR. Se populariza `AGENTS.md`. |
| 2026 | Orquestación de varios agentes en paralelo, revisión automática de PR y agentes en CI. |

### Ventajas y desventajas

| Ventajas | Desventajas |
|---|---|
| Automatiza tareas de varios pasos: migraciones, refactorizaciones masivas, actualizar dependencias | Puede hacer cambios grandes difíciles de revisar |
| Verifica su propio trabajo con pruebas | Riesgo operativo si tiene permisos amplios (borrar datos, ejecutar comandos peligrosos) |
| Paraleliza: varios agentes en ramas distintas | Costo de tokens y latencia |
| Libera al humano para diseño y revisión | Inyección de instrucciones (*prompt injection*) desde contenido externo |
| Se integra a CI/CD | La calidad depende del contexto y de las pruebas existentes |

### Casos de uso
- Migraciones y actualizaciones masivas (versiones de lenguaje o framework).
- Corregir issues bien especificados con pruebas que los reproducen.
- Generar o ampliar suites de pruebas.
- Tareas de mantenimiento (*toil*): dependencias, deprecaciones, lint.
- Prototipos completos que luego revisa un humano.
- **Sistemas multiagente de negocio**, como el ejemplo práctico de este proyecto: Kairos coordina agentes especializados con estado compartido.

### Casos de aplicación (industria)
- **Amazon (Q Developer)**: Andy Jassy reportó (ago. 2024) que la actualización automática de aplicaciones Java ahorró el equivalente a **4.500 años-desarrollador** y unos **US$260 millones anuales**.
- **Nubank + Devin**: migración de un monolito ETL de varios millones de líneas. Cognition reporta entre **8 y 12 veces más eficiencia** en horas de ingeniería y unas **20 veces menos costo**. *Dato del proveedor.*
- **Mercado Libre**: Cognition (Windsurf) y Anthropic (Claude Code) publican casos de adopción en su organización de ingeniería. *Dato del proveedor.*

---

## Tema 4 — Vibe coding

### Definición
Término acuñado por **Andrej Karpathy en febrero de 2025**. Describe programar **dándole a la IA instrucciones en lenguaje natural y aceptando lo que genera, sin leer ni entender el código**. Se itera ejecutando el resultado y pidiendo cambios ("no funciona, arréglalo"). El código existe, pero el humano **renuncia a comprenderlo**.

Simon Willison precisa la diferencia: si revisas, pruebas y entiendes cada línea que generó el modelo, **no es vibe coding**. Es usar el LLM como asistente de escritura, es decir, pair programming con IA.

### Características
- El lenguaje natural es la interfaz principal. El código es un "subproducto".
- Se aceptan todos los cambios. Los errores se corrigen pegando el mensaje de error en el chat.
- Ciclos muy cortos de prueba visual ("¿se ve y funciona?").
- Herramientas típicas: **Lovable**, **Bolt.new**, **v0** (Vercel), **Replit Agent**, **Google AI Studio/Firebase Studio**, o Cursor y Claude Code en modo "aceptar todo".
- Usuario típico: personas no programadoras, emprendedores, diseñadores, o programadores haciendo prototipos desechables.

### Historia y evolución

| Año | Hito |
|---|---|
| 2023–2024 | Generadores de UI y apps por prompt (v0 2023; Bolt.new y Replit Agent 2024). |
| **Feb 2025** | Karpathy acuña "vibe coding". |
| Mar 2025 | Y Combinator: cerca de un **25 % de las startups de la cohorte W25** tenían ~95 % de su código generado por IA (Garry Tan). |
| 2025 | Crecimiento explosivo de las plataformas (Lovable, Bolt). Primeros incidentes públicos: datos expuestos en apps generadas y un agente de Replit que **borró la base de datos de producción** de un usuario (jul. 2025). |
| Nov 2025 | *Collins Dictionary* elige "vibe coding" como palabra del año 2025. |
| 2026 | Se distingue entre **vibe coding** (prototipo, uso personal) y **"agentic engineering"** (producción con pruebas, revisión y responsabilidad). |

### Ventajas y desventajas

| Ventajas | Desventajas |
|---|---|
| Velocidad extrema de prototipado (horas, no semanas) | **Deuda técnica invisible**: nadie entiende el código |
| Democratiza la creación de software ("software para uno") | **Seguridad**: credenciales expuestas, controles de acceso ausentes, dependencias inventadas |
| Ideal para validar ideas y hacer demos | Mantenibilidad casi nula. Escalar cuesta caro. |
| Exploración creativa sin barrera técnica | Depuración difícil cuando la IA "da vueltas" |
| | Responsabilidad legal y operativa difusa |

### Casos de uso
- Prototipos y MVP para validar una hipótesis de negocio.
- Herramientas personales o internas de bajo riesgo: scripts, dashboards caseros.
- Hackathons y demos.
- Aprender explorando, siempre que después se estudie el código.
- **No usar** para sistemas con datos personales, pagos, salud o cualquier cosa en producción sin revisión.

### Casos de aplicación (industria)
- **Startups de Y Combinator (W25)**: productos iniciales construidos mayoritariamente con IA.
- **Lovable**: plataforma sueca de vibe coding que reportó un crecimiento de ingresos récord en 2025. *Dato del proveedor.*
- **Contraejemplos instructivos**: el incidente de Replit (jul. 2025) y los reportes de apps generadas con datos expuestos muestran por qué el vibe coding **no sustituye** la ingeniería en producción.

---

## Tema 5 — No-code / low-code

### Definición
- **No-code**: construir aplicaciones **sin escribir código**, mediante interfaces visuales (arrastrar y soltar, formularios, flujos y reglas configurables).
- **Low-code**: lo mismo, pero con **puntos de extensión en código** para la lógica que la plataforma no cubre.

El usuario objetivo es el **desarrollador ciudadano** (*citizen developer*): alguien del negocio que construye sus propias herramientas.

### Características
- Componentes prefabricados, modelado visual de datos y flujos.
- Despliegue y hosting gestionados por la plataforma.
- Integraciones mediante conectores (APIs, SaaS).
- Gobierno centralizado (permisos, ambientes) en las plataformas empresariales.
- Plataformas: **Bubble**, **Webflow**, **Airtable**, **Glide**, **AppSheet** (Google), **Microsoft Power Apps / Power Automate**, **OutSystems**, **Mendix** (Siemens), **Zapier**, **Make**, **n8n** (automatización), **Retool** (herramientas internas, low-code).
- Tendencia actual: la **IA se vuelve la interfaz del no-code**. Se describe la app en lenguaje natural y la plataforma la arma (Copilot en Power Apps, "AI app builders"). Aquí no-code y vibe coding se tocan.

### Historia y evolución

| Año | Hito |
|---|---|
| 1979–1992 | Hojas de cálculo (VisiCalc), lenguajes 4GL, FileMaker, **Visual Basic (1991)**, Access: desarrollo rápido de aplicaciones (RAD). |
| 2001–2012 | OutSystems (2001), Mendix (2005), Zapier (2011), Bubble y Airtable (2012), Webflow (2013). |
| 2014 | Forrester acuña el término **"low-code"**. |
| 2016–2020 | Microsoft Power Apps (2016). **Siemens compra Mendix** (2018). **Google compra AppSheet** (2020). |
| 2021 | Gartner predice que el **70 % de las apps nuevas** de las organizaciones usarán low-code/no-code en 2025 (frente a menos del 25 % en 2020). |
| 2023–2026 | Integración de IA generativa: crear apps y flujos con un prompt. n8n y Make se usan para orquestar agentes de IA sin código. |

### Ventajas y desventajas

| Ventajas | Desventajas |
|---|---|
| Tiempo de entrega muy corto | **Dependencia del proveedor** (*vendor lock-in*) y precios por usuario o ejecución |
| Menor costo inicial; no requiere equipo de desarrollo | Techo de personalización y de rendimiento |
| Empodera al negocio y reduce el backlog de TI | Escalabilidad y portabilidad limitadas |
| Mantenimiento de infraestructura delegado | "Shadow IT": apps sin gobierno, seguridad ni respaldo |
| Ideal para automatizar procesos internos | Difícil de versionar, probar y revisar como el código |

### Casos de uso
- Formularios, aprobaciones y flujos internos (RR. HH., compras).
- Integraciones entre SaaS (CRM → hoja de cálculo → correo).
- MVP de marketplaces o directorios.
- Portales y sitios web de marketing.
- Prototipos de agentes de IA con n8n o Make.

### Casos de aplicación (industria)
- **Siemens** adquirió **Mendix** (2018) y la integró a su portafolio industrial de transformación digital.
- **Google** adquirió **AppSheet** (2020) para que usuarios de Workspace creen apps sin código.
- **Microsoft Power Platform**: muy usada en grandes empresas para automatizar procesos internos con desarrolladores ciudadanos.
- En LatAm es común en pymes y en áreas de negocio de bancos y retail para tableros, formularios y automatizaciones.

---

## Comparación rápida: pair programming con IA vs. vibe coding vs. no-code

| Dimensión | Pair programming clásico | **Pair programming con IA** | Agente asíncrono | **Vibe coding** | **No-code** |
|---|---|---|---|---|---|
| ¿Quién escribe? | Humano (driver) | Humano o IA, alternando | IA | IA | Plataforma (visual) |
| ¿Quién revisa? | Humano (navigator) | Humano siempre (+ IA) | Humano en el PR | Nadie (se prueba "a ojo") | La plataforma / nadie |
| ¿Se lee el código? | Sí, todo | **Sí, todo** | Sí, en el PR | **No** | No hay código visible |
| ¿Quién responde por el código? | La pareja | El humano | El humano que hace merge | Difuso | El proveedor y el usuario |
| Perfil | Desarrolladores | Desarrolladores | Desarrolladores | Cualquiera | Desarrollador ciudadano |
| Calidad / mantenibilidad | Alta | Alta (si hay disciplina) | Media–alta | Baja | Media (dentro del techo) |
| Velocidad inicial | Media | Alta | Alta | Muy alta | Muy alta |
| Ideal para | Código crítico, mentoría | Desarrollo profesional diario | Toil, migraciones | Prototipos, uso personal | Procesos internos, MVP |

> **Idea central:** la diferencia no es la herramienta. Cursor sirve para las tres primeras columnas y también para el vibe coding. Lo que cambia es **la postura del humano**: si conserva el rol de navegante (o conductor) y la responsabilidad, es pair programming con IA. Si delega la comprensión, es vibe coding. Si ni siquiera hay código, es no-code.

---

## Referencias
1. Beck, K. (1999). *Extreme Programming Explained*. Addison-Wesley.
2. Cockburn, A. & Williams, L. (2000). *The Costs and Benefits of Pair Programming*. XP 2000.
3. Williams, L. & Kessler, R. (2002). *Pair Programming Illuminated*. Addison-Wesley.
4. Arisholm, E. et al. (2007). Evaluating Pair Programming with Respect to System Complexity and Programmer Expertise. *IEEE TSE*.
5. Hannay, J. et al. (2009). The effectiveness of pair programming: A meta-analysis. *IST*.
6. Chen, M. et al. (2021). Evaluating Large Language Models Trained on Code (Codex / HumanEval). arXiv:2107.03374.
7. Pearce, H. et al. (2021). Asleep at the Keyboard? Assessing the Security of GitHub Copilot's Code Contributions. arXiv:2108.09293.
8. Peng, S. et al. (2023). The Impact of AI on Developer Productivity: Evidence from GitHub Copilot. arXiv:2302.06590.
9. METR (2025). Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity. https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
10. Stack Overflow (2025). Developer Survey — AI. https://survey.stackoverflow.co/2025/ai
11. Google Cloud DORA (2024). *Accelerate State of DevOps Report*.
12. GitHub Blog (2024). Research: Quantifying GitHub Copilot's impact in the enterprise with Accenture.
13. TechCrunch (2025-07-30). GitHub Copilot crosses 20 million all-time users.
14. Cognition. Nubank customer story. https://devin.ai/customers
15. Karpathy, A. (2025-02-02). Publicación en X que acuña "vibe coding". Willison, S. (2025). *Not all AI-assisted programming is vibe coding*.
16. Gartner (2021). Forecast: low-code development technologies.
17. Anthropic (2024). Introducing the Model Context Protocol.

> ⚠️ **Nota de verificación:** las cifras de casos empresariales (Accenture, Mercado Libre, Nubank, Lovable) provienen de los fabricantes de las herramientas. Conviene presentarlas como *reportadas por el proveedor* y contrastarlas con estudios independientes (METR, DORA, Stack Overflow).
