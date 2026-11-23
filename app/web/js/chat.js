// Chat column: empty state, messages, answer / refusal / error cards.
import { api } from "./api.js";
import { splitCitations } from "./citations.js";
import { announce, el, fmt, icon, markdownFragment, specClass } from "./dom.js";
import { pipelineLine } from "./settings.js";
import { focusSource, placeSourcesPanel, renderPlaceholder, renderSources } from "./sources.js";
import { clearHistory, persistHistory, pushMessage, state } from "./state.js";

const NAMES = { gemini: "Gemini", groq: "Groq", grok: "Grok" };
const STEPS = ["Routing the question…", "Searching the specifications…", "Reranking passages…",
  "Writing the answer…"];
const MAX_CHARS = 1000;
let examples = { architecture: [], nas: [], cross: [] };
let hooks = { onAnswer: () => {} };

const $ = (id) => document.getElementById(id);
const newId = () => (crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + Math.random()));

// ----------------------------------------------------------------------------- pieces
function routeBadge(answer) {
  const specs = answer.route.specs || [];
  if (!answer.config.use_routing) return el("span", { class: "badge badge-both", text: "Routing off — searched both specs" });
  if (specs.length === 1) {
    return el("span", { class: `badge ${specClass(specs[0], "badge")}`, text: `Routed to ${specs[0]}` });
  }
  return el("span", { class: "badge badge-both", text: "Routed to both specs" });
}

function citeChip(seg, msgId) {
  return el("button", {
    class: `cite ${specClass(seg.spec, "cite")}`, type: "button", text: seg.label,
    "aria-label": `Show source ${seg.label}`,
    onclick: (e) => { e.stopPropagation(); select(msgId); focusSource(seg); },
  });
}

// Replace citation patterns in the text nodes of a sanitized fragment with chips.
function chipify(fragment, msgId) {
  const walker = document.createTreeWalker(fragment, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    const segs = splitCitations(node.nodeValue);
    if (segs.length === 1 && segs[0].type === "text") continue;
    const parts = segs.map((s) => (s.type === "text" ? document.createTextNode(s.value) : citeChip(s, msgId)));
    node.replaceWith(...parts);
  }
  return fragment;
}

function warningsBox(answer) {
  const items = [];
  const removed = answer.removed_citations || [];
  if (removed.length) {
    const list = removed.map((c) => `${c.spec} §${c.section}`).join(", ");
    items.push(`${removed.length} citation${removed.length > 1 ? "s" : ""} removed: ${list} `
      + `${removed.length > 1 ? "were" : "was"} not among the retrieved sources.`);
  }
  for (const w of answer.warnings || []) items.push(w);
  if (!items.length) return null;
  return el("div", { class: "alert", role: "alert" }, icon("alert"),
    el("ul", {}, items.map((t) => el("li", { text: t }))));
}

function copyButton(answer) {
  const btn = el("button", { class: "btn btn-small", type: "button" }, icon("copy"), "Copy answer");
  btn.addEventListener("click", async (e) => {
    e.stopPropagation();
    const text = answer.text;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = el("textarea", {}); ta.value = text; document.body.append(ta); ta.select();
      try { document.execCommand("copy"); } catch { /* ignore */ }
      ta.remove();
    }
    btn.lastChild.nodeValue = "Copied";
    setTimeout(() => { btn.lastChild.nodeValue = "Copy answer"; }, 2000);
  });
  return btn;
}

function answerCard(msg) {
  const a = msg.data;
  const valid = (a.citations || []).filter((c) => c.valid).length;
  const badges = el("div", { class: "badges" }, routeBadge(a),
    el("span", { class: "route-reason", text: a.route.reason, title: a.route.reason }),
    a.llm.fallback_used ? el("span", { class: "badge badge-fallback", text: `Fallback: answered by ${NAMES[a.llm.provider] || a.llm.provider}` }) : null);
  const body = el("div", { class: "answer-body" });
  body.append(chipify(markdownFragment(a.text), msg.id));
  const foot = el("div", { class: "answer-foot" },
    el("span", { text: `${NAMES[a.llm.provider] || a.llm.provider} · ${a.llm.model}` }), "·",
    el("span", { text: `${(a.citations || []).length} citations · ${valid} valid` }), "·",
    el("span", { text: `Gate score ${fmt(a.gate.score)}` }), "·",
    el("span", { text: `${((a.timings_ms.total || 0) / 1000).toFixed(1)} s` }),
    el("span", { class: "spacer" }), copyButton(a));
  return el("article", { class: "answer", "data-id": msg.id, "aria-label": "Answer" },
    badges, body, warningsBox(a), foot);
}

function refusalCard(msg) {
  const a = msg.data;
  const gate = !a.llm.called;
  const kind = a.gate.kind === "reranker" ? "reranker" : "similarity";
  const explain = gate
    ? `No passage in TS 23.501 or TS 24.501 is relevant enough. The best ${kind} score was `
      + `${fmt(a.gate.score)}, below the ${fmt(a.gate.threshold)} threshold, so no answer was generated.`
    : "The retrieved passages don't contain this information.";
  const route = a.config.use_routing ? `Routed to ${(a.route.specs || []).join(" + ")}` : "Routing off";
  const who = gate ? "LLM not called" : `${NAMES[a.llm.provider] || a.llm.provider} · ${a.llm.model}`;
  return el("article", { class: "answer refusal", "data-id": msg.id, "aria-label": "Refusal" },
    el("div", { class: "refusal-head" }, icon("info"), el("span", { text: a.text })),
    el("p", { text: explain }),
    el("div", { class: "meta", text: `${route} · ${who} · ${((a.timings_ms.total || 0) / 1000).toFixed(1)} s` }));
}

function errorCard(msg) {
  const e = msg.error;
  return el("article", { class: "answer error-card", "data-id": msg.id, role: "alert" },
    el("div", { class: "refusal-head" }, icon("alert"), el("span", { text: e.message })),
    e.fix ? el("div", { class: "fix-line", text: e.fix }) : null,
    el("button", {
      class: "btn btn-small", type: "button", onclick: () => retry(msg),
    }, icon("retry"), "Retry"));
}

function loadingCard() {
  const status = el("div", { class: "status", text: STEPS[0] });
  const card = el("article", { class: "answer loading", "aria-busy": "true", "aria-label": "Loading" },
    el("div", { class: "skeleton" }), el("div", { class: "skeleton" }), el("div", { class: "skeleton" }), status);
  let i = 0;
  card._timer = setInterval(() => {
    i = Math.min(i + 1, STEPS.length - 1);
    status.textContent = STEPS[i];
  }, 700);
  return card;
}

function emptyState() {
  const group = (title, chipText, chipClass, qs) => el("div", { class: "card" },
    el("div", { class: "card-head" }, el("span", { text: title }), el("span", { class: `chip ${chipClass}`, text: chipText })),
    qs.map((q) => el("button", { class: "example-btn", type: "button", text: q, onclick: () => ask(q) })));
  return el("div", { class: "empty" },
    el("h1", { class: "hero", text: "Ask the 5G specifications" }),
    el("p", {
      class: "lead",
      text: "Every answer comes from TS 23.501 (architecture) and TS 24.501 (NAS protocol), "
        + "Release 18, with the spec and section it was taken from. When the documents don't "
        + "cover a question, the assistant says so.",
    }),
    el("div", { id: "empty-composer-slot" }),
    el("div", { class: "cards" },
      group("Architecture", "TS 23.501", "chip-23", examples.architecture || []),
      group("NAS signalling", "TS 24.501", "chip-24", examples.nas || []),
      group("Cross-spec", "Both", "chip-both", examples.cross || [])),
    el("div", { class: "pipeline-line", id: "pipeline-line", text: pipelineLine() }));
}

// ----------------------------------------------------------------------------- render
export function render() {
  const box = $("messages");
  const composer = $("composer-wrap");
  const ta = $("question");
  if (!state.history.length) {
    box.replaceChildren(emptyState());
    $("empty-composer-slot").append(composer);
    ta.rows = 3;
    composer.classList.add("in-empty");
    renderPlaceholder();
    placeSourcesPanel(null);
    return;
  }
  ta.rows = 2;
  composer.classList.remove("in-empty");
  box.after(composer);
  const nodes = [];
  for (const msg of state.history) {
    if (msg.role === "user") nodes.push(el("div", { class: "msg-user", text: msg.text }));
    else if (msg.role === "assistant") nodes.push(msg.data.refused ? refusalCard(msg) : answerCard(msg));
    else if (msg.role === "error") nodes.push(errorCard(msg));
  }
  box.replaceChildren(...nodes);
  for (const card of box.querySelectorAll(".answer[data-id]")) {
    card.addEventListener("click", (e) => {
      if (e.target.closest("button, a")) return;
      select(card.dataset.id);
    });
  }
  const answers = state.history.filter((m) => m.role === "assistant");
  const sel = state.selectedId && answers.find((m) => m.id === state.selectedId);
  select((sel || answers[answers.length - 1] || {}).id || null, false);
}

export function select(id, scroll = false) {
  state.selectedId = id;
  const box = $("messages");
  for (const card of box.querySelectorAll(".answer[data-id]")) {
    card.classList.toggle("selected", card.dataset.id === id);
  }
  const msg = state.history.find((m) => m.id === id && m.role === "assistant");
  renderSources(msg ? msg.data : null);
  const card = id && box.querySelector(`.answer[data-id="${CSS.escape(id)}"]`);
  if (window.matchMedia("(max-width: 899px)").matches && card) {
    let holder = card.querySelector("details.inline-sources");
    if (!holder) {
      holder = el("details", { class: "inline-sources" },
        el("summary", { text: `Sources (${msg ? msg.data.sources.length : 0})` }));
      card.append(holder);
    }
    placeSourcesPanel(holder);
  } else {
    placeSourcesPanel(null);
  }
  if (scroll && card) card.scrollIntoView({ block: "nearest" });
}

// ----------------------------------------------------------------------------- sending
function setBusy(busy) {
  state.busy = busy;
  $("question").disabled = busy;
  updateSend();
}

export function updateSend() {
  const ta = $("question");
  const n = ta.value.trim().length;
  const counter = $("counter");
  counter.hidden = ta.value.length <= 800;
  counter.textContent = `${ta.value.length}/${MAX_CHARS}`;
  counter.classList.toggle("over", ta.value.length > MAX_CHARS);
  $("send").disabled = state.busy || !state.ready || n < 1 || ta.value.length > MAX_CHARS;
}

async function send(question, settings) {
  if (state.busy) return;
  const loading = loadingCard();
  $("messages").append(loading);
  loading.scrollIntoView({ block: "nearest" });
  setBusy(true);
  try {
    const data = await api.ask({ question, ...settings });
    const msg = { id: newId(), role: "assistant", data };
    pushMessage(msg);
    state.selectedId = msg.id;
    hooks.onAnswer(data);
    announce(data.refused ? "Refused" : "Answer ready");
  } catch (err) {
    pushMessage({
      id: newId(), role: "error", question, settings,
      error: { message: err.message, fix: err.fix, code: err.code },
    });
    announce("Error");
  } finally {
    clearInterval(loading._timer);
    setBusy(false);
    render();
    const last = $("messages").lastElementChild;
    if (last) last.scrollIntoView({ block: "nearest" });
  }
}

export function ask(question) {
  const q = String(question || "").trim();
  if (!q || state.busy || !state.ready) return;
  pushMessage({ id: newId(), role: "user", text: q });
  $("question").value = "";
  autoGrow();
  render();
  send(q, { ...state.settings });
}

function retry(msg) {
  if (state.busy) return;
  const idx = state.history.findIndex((m) => m.id === msg.id);
  if (idx >= 0) state.history.splice(idx, 1);
  persistHistory();
  render();
  send(msg.question, msg.settings);
}

function autoGrow() {
  const ta = $("question");
  ta.style.height = "auto";
  const line = 22;
  ta.style.height = `${Math.min(Math.max(ta.scrollHeight, 2 * line), 6 * line + 20)}px`;
}

export function initChat(exampleGroups, opts) {
  examples = exampleGroups || examples;
  hooks = { ...hooks, ...opts };
  const ta = $("question");
  ta.addEventListener("input", () => { autoGrow(); updateSend(); });
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      if (!$("send").disabled) ask(ta.value);
    }
  });
  $("composer").addEventListener("submit", (e) => { e.preventDefault(); ask(ta.value); });
  $("new-chat").addEventListener("click", () => { clearHistory(); render(); ta.focus(); });
  window.matchMedia("(max-width: 899px)").addEventListener("change", () => render());
  render();
  updateSend();
}

export function refreshPipelineLine() {
  const node = document.getElementById("pipeline-line");
  if (node) node.textContent = pipelineLine();
}
