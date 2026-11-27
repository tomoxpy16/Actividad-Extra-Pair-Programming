// Kairos — cliente web sin dependencias. Consulta el estado compartido cada 3 s.
const API = "/api";

// Los íconos (Lucide) vienen de icons.js, que se carga antes que este archivo.
const svg = (name) => `<svg viewBox="0 0 24 24" aria-hidden="true">${ICON[name] || ICON.otro}</svg>`;

const AGENTS = {
  Orchestrator:     { icon: "orchestrator", color: "#475569", label: "Orquestador" },
  IntakeAgent:      { icon: "intake",       color: "#2563eb", label: "Intake" },
  PrioritizerAgent: { icon: "prioritizer",  color: "#7c3aed", label: "Prioritizer" },
  SchedulerAgent:   { icon: "scheduler",    color: "#0d9488", label: "Scheduler" },
  MonitorAgent:     { icon: "monitor",      color: "#d97706", label: "Monitor" },
  CoachAgent:       { icon: "coach",        color: "#059669", label: "Coach" },
};
const QUADRANT_CLASS = { "Hacer ahora": "Q1", "Planificar": "Q2", "Hacer rápido": "Q3", "Si sobra tiempo": "Q4" };
const CATEGORY = { estudio: "Estudio", trabajo: "Trabajo", salud: "Salud", hogar: "Hogar", personal: "Personal", otro: "Otro" };
const PROVIDER = { rules: "Motor: reglas", ollama: "Motor: Ollama", anthropic: "Motor: Claude" };
const EXAMPLES = [
  { label: "Día de trabajo", text: "Hoy tengo reunión con el equipo a las 3 pm, debo terminar el informe del proyecto antes de las 6 que es muy importante, ir al gimnasio una hora y llamar a mi mamá" },
  { label: "Semana de parciales", text: "Mañana: estudiar cálculo 2 horas para el parcial del viernes; pagar la factura de internet urgente; comprar mercado y si me da tiempo ver una serie" },
  { label: "Entrega de proyecto", text: "Preparar la sustentación de arquitectura 3 horas para el jueves, responder correos media hora y meditar 15 minutos" },
];

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// Las horas se muestran en la zona horaria del servidor (KAIROS_TZ), no en la del navegador.
const hm = (iso) => iso.slice(11, 16);
const dateOf = (iso) => new Date(iso.slice(0, 10) + "T12:00:00");
const weekday = (iso) => dateOf(iso).toLocaleDateString("es-CO", { weekday: "short" });
const dayKey = (iso) => iso.slice(0, 10);
let lastEventId = 0;
let busy = false;
let lastPlanSig = "";
let lastTimelineHtml = "";

async function call(path, options = {}) {
  const res = await fetch(API + path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail?.[0]?.msg || body.detail || `Error ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove("show"), 2800);
}

async function action(fn, okMsg) {
  if (busy) return;
  busy = true;
  document.querySelectorAll("button").forEach((b) => (b.disabled = true));
  $("#plan-btn").classList.add("loading");
  try {
    await fn();
    if (okMsg) toast(okMsg);
  } catch (e) {
    toast(e.message);
  } finally {
    busy = false;
    document.querySelectorAll("button").forEach((b) => (b.disabled = false));
    $("#plan-btn").classList.remove("loading");
    await refresh();
  }
}

// ------------------------------------------------------------------ render
function renderClock(state) {
  $("#clock").textContent = hm(state.now);
  const off = state.clock_offset_minutes;
  $("#clock-meta").textContent = off ? `simulado +${off >= 60 ? (off / 60).toFixed(1).replace(".0", "") + " h" : off + " min"}` : "reloj real";
  $("#clock-box").classList.toggle("simulated", off > 0);
  $("#provider").textContent = PROVIDER[state.llm_provider] || `Motor: ${state.llm_provider}`;
}

function renderStats(s) {
  const pct = s.total ? Math.round((100 * s.done) / s.total) : 0;
  const items = [
    { label: "Tareas", n: s.total, icon: "list" },
    { label: "Completadas", n: s.done, icon: "done", cls: s.done ? "good" : "", bar: pct },
    { label: "En curso", n: s.in_progress, icon: "run" },
    { label: "En riesgo", n: s.at_risk, icon: "alert", cls: s.at_risk ? "warn" : "" },
    { label: "Retrasos detectados", n: s.delays, icon: "rotate", cls: s.delays ? "warn" : "" },
  ];
  $("#stats").innerHTML = items.map((it) => `
    <div class="stat ${it.cls || ""}">
      <div class="stat-top"><span>${it.label}</span>${svg(it.icon)}</div>
      <b>${it.n}</b>
      ${it.bar !== undefined ? `<div class="bar" title="${it.bar}% completado"><i style="width:${it.bar}%"></i></div>` : ""}
    </div>`).join("");
}

function blockHtml(t) {
  const q = QUADRANT_CLASS[t.quadrant] || "Q4";
  const time = t.scheduled_start
    ? `${hm(t.scheduled_start)}<small>${hm(t.scheduled_end)}</small>`
    : `—<small>${t.estimated_minutes} min</small>`;
  const score = Math.round(t.priority_score);
  const tags = [
    t.quadrant ? `<span class="q ${q.toLowerCase()}">${esc(t.quadrant)}</span>` : "",
    `<span class="tag">${svg(t.category)}${CATEGORY[t.category] || esc(t.category)}</span>`,
    `<span class="tag">${svg("clock")}${t.estimated_minutes} min</span>`,
    t.status !== "done" ? `<span class="score" title="Puntaje de prioridad">prioridad ${score}<i style="--w:${score}%"></i></span>` : "",
    t.fixed_start ? `<span class="tag">${svg("pin")}hora fija</span>` : "",
    t.deadline ? `<span class="tag">${svg("flag")}vence ${weekday(t.deadline)} ${hm(t.deadline)}</span>` : "",
    t.delay_count ? `<span class="tag delay">reprogramada ×${t.delay_count}</span>` : "",
    t.at_risk && t.status !== "done" ? `<span class="tag risk">en riesgo</span>` : "",
  ].join("");
  let buttons = "";
  if (t.status === "scheduled" || t.status === "unscheduled")
    buttons += `<button class="act" data-act="start" data-id="${t.id}" title="Iniciar" aria-label="Iniciar">${svg("play")}</button>`;
  if (t.status === "in_progress" || t.status === "scheduled")
    buttons += `<button class="act ok" data-act="complete" data-id="${t.id}" title="Completar" aria-label="Completar">${svg("check")}</button>`;
  if (t.status !== "done")
    buttons += `<button class="act del" data-act="delete" data-id="${t.id}" title="Eliminar" aria-label="Eliminar">${svg("trash")}</button>`;
  return `<div class="block ${q} ${t.status}" style="view-transition-name: t-${t.id}">
      <div class="time">${time}</div>
      <div class="dot"></div>
      <div class="task">
        <div>
          <div class="title">${esc(t.title)}${t.status === "in_progress" ? '<span class="tag live">en curso</span>' : ""}</div>
          <div class="meta">${tags}</div>
          ${t.rationale && t.status !== "done" ? `<div class="why">${esc(t.rationale)}</div>` : ""}
        </div>
        <div class="actions">${buttons}</div>
      </div>
    </div>`;
}

const nowLine = (now) => `<div class="now-line" style="view-transition-name: now-line"><span>${hm(now)}</span><b></b><em></em></div>`;

function dayTitle(key, today) {
  const d = new Date(key + "T12:00:00");
  const t = new Date(today + "T12:00:00");
  const diff = Math.round((d - t) / 86400000);
  const name = diff === 0 ? "Hoy" : diff === 1 ? "Mañana" : d.toLocaleDateString("es-CO", { weekday: "long" });
  return `<div class="day-head"><h3>${esc(name)}</h3><span>${d.toLocaleDateString("es-CO", { day: "numeric", month: "long" })}</span></div>`;
}

function renderTimeline(state) {
  const tasks = state.tasks;
  if (!tasks.length) {
    swapTimeline(`<div class="empty"><img src="logo.svg" alt=""><b>Tu día todavía está en blanco</b>
      Escribe tus pendientes arriba o prueba un ejemplo. Los agentes harán el resto.</div>`, "");
    return;
  }
  const open = tasks.filter((t) => t.status !== "done" && t.scheduled_start)
    .sort((a, b) => a.scheduled_start.localeCompare(b.scheduled_start));
  const unscheduled = tasks.filter((t) => t.status !== "done" && !t.scheduled_start);
  const done = tasks.filter((t) => t.status === "done");
  const days = {};
  open.forEach((t) => (days[dayKey(t.scheduled_start)] ??= []).push(t));
  const today = dayKey(state.now);
  let html = "";
  for (const [key, list] of Object.entries(days)) {
    let blocks = "", nowShown = key !== today;
    for (const t of list) {
      if (!nowShown && t.scheduled_start >= state.now && t.status !== "in_progress") {
        blocks += nowLine(state.now);
        nowShown = true;
      }
      blocks += blockHtml(t);
    }
    if (!nowShown) blocks += nowLine(state.now);
    html += `<div class="day">${dayTitle(key, today)}<div class="blocks">${blocks}</div></div>`;
  }
  if (unscheduled.length) html += `<div class="day"><div class="day-head"><h3>Sin franja</h3><span>no cupieron en el horizonte</span></div><div class="blocks">${unscheduled.map(blockHtml).join("")}</div></div>`;
  if (done.length) html += `<div class="day"><div class="day-head"><h3>Completadas</h3><span>${done.length}</span></div><div class="blocks">${done.map(blockHtml).join("")}</div></div>`;
  const sig = tasks.map((t) => `${t.id}|${t.scheduled_start}|${t.status}|${t.delay_count}`).join(";");
  swapTimeline(html, sig);
}

// Anima el cronograma (View Transitions API) solo cuando el plan cambia de verdad:
// las tareas se deslizan a su nueva hora en lugar de "saltar". Sin soporte, se actualiza normal.
function swapTimeline(html, sig) {
  if (html === lastTimelineHtml) return;
  const update = () => { $("#timeline").innerHTML = html; lastTimelineHtml = html; };
  const animate = lastPlanSig && sig !== lastPlanSig && document.startViewTransition
    && !matchMedia("(prefers-reduced-motion: reduce)").matches;
  lastPlanSig = sig;
  if (animate) document.startViewTransition(update); else update();
}

function renderEvents(events) {
  $("#event-count").textContent = events.length ? `${events.length} recientes` : "";
  if (!events.length) {
    $("#events").innerHTML = `<li class="empty">Aquí verás cómo colaboran los agentes: quién entendió, quién priorizó, quién agendó y quién vigila.</li>`;
    return;
  }
  const maxId = Math.max(...events.map((e) => e.id));
  $("#events").innerHTML = events.map((e) => {
    const a = AGENTS[e.agent] || { icon: "otro", color: "#64748b" };
    const fresh = lastEventId && e.id > lastEventId ? "fresh" : "";
    return `<li class="event ${e.kind} ${fresh}">
        <div class="avatar" style="background:${a.color}">${svg(a.icon)}</div>
        <div class="bubble"><div class="who"><span style="color:${a.color}">${esc(e.agent)}</span><time>${hm(e.ts)}</time></div>
        <div class="msg">${esc(e.message)}</div></div>
      </li>`;
  }).join("");
  lastEventId = maxId;
}

async function refresh() {
  try {
    const state = await call("/state");
    renderClock(state);
    renderStats(state.stats);
    renderTimeline(state);
    renderEvents(state.events);
  } catch (e) {
    $("#clock-meta").textContent = "sin conexión con la API";
  }
}

// ------------------------------------------------------------------ eventos UI
document.querySelectorAll("[data-icon]").forEach((el) => (el.outerHTML = svg(el.dataset.icon)));
$("#agent-legend").innerHTML = Object.values(AGENTS)
  .map((a) => `<span class="agent-chip"><i style="background:${a.color}"></i>${a.label}</span>`).join("");
$("#examples").innerHTML = EXAMPLES.map((ex, i) => `<button type="button" class="chip" data-example="${i}">${ex.label}</button>`).join("");
$("#examples").addEventListener("click", (e) => {
  const i = e.target.closest("[data-example]")?.dataset.example;
  if (i !== undefined) { $("#text").value = EXAMPLES[i].text; $("#text").focus(); }
});
$("#text").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) $("#plan-form").requestSubmit();
});
$("#plan-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = $("#text").value.trim();
  if (text.length < 3) return toast("Escribe al menos una actividad.");
  action(async () => {
    const r = await call("/plan", { method: "POST", body: JSON.stringify({ text }) });
    $("#text").value = "";
    toast(r.new_task_ids.length ? `${r.new_task_ids.length} tarea(s) nuevas en tu plan` : "No encontré actividades en el texto");
  });
});
$("#timeline").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-act]");
  if (!btn) return;
  const { act, id } = btn.dataset;
  if (act === "delete") return action(() => call(`/tasks/${id}`, { method: "DELETE" }), "Tarea eliminada");
  action(() => call(`/tasks/${id}/${act}`, { method: "POST" }), act === "complete" ? "¡Bien! Tarea completada" : "Tarea en curso");
});
document.querySelectorAll("[data-advance]").forEach((b) =>
  b.addEventListener("click", () => action(async () => {
    const r = await call("/clock/advance", { method: "POST", body: JSON.stringify({ minutes: +b.dataset.advance }) });
    toast(r.delays.length ? `El monitor detectó ${r.delays.length} retraso(s) y reorganizó tu día` : "Todo va según el plan");
  })));
$("#replan").addEventListener("click", () => action(() => call("/replan", { method: "POST" }), "Plan recalculado"));
$("#reset").addEventListener("click", () => {
  if (confirm("¿Borrar todas las tareas, eventos y el reloj simulado?")) action(() => call("/reset", { method: "POST" }), "Todo reiniciado");
});

refresh();
setInterval(() => !busy && refresh(), 3000);
