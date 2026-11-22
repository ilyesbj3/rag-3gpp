// Bootstrap: health check, header, hash router (UI_SPEC.md §6).
import { api } from "./api.js";
import { ask, initChat, refreshPipelineLine, render, updateSend } from "./chat.js";
import { loadCitationPattern } from "./citations.js";
import { el, specClass } from "./dom.js";
import { renderEvaluation } from "./evaluation.js";
import { applyHealthToSettings, initSettings, renderSidebarExamples } from "./settings.js";
import { state } from "./state.js";

const NAMES = { gemini: "Gemini", groq: "Groq", grok: "Grok" };

function setPill(kind, text, title = "") {
  const pill = document.getElementById("llm-pill");
  pill.querySelector(".dot").className = `dot dot-${kind}`;
  pill.querySelector(".pill-text").textContent = text;
  pill.title = title;
}

// Pill text from the providers that are really configured (and the last answer's provider).
export function updatePill() {
  const h = state.health;
  if (!h) return;
  const chain = h.chain || [];
  if (!chain.length) {
    setPill("err", "No LLM configured", "cp .env.example .env and set GEMINI_API_KEY / GROQ_API_KEY");
    return;
  }
  const primary = chain[0];
  if (state.lastProvider && state.lastProvider !== primary && chain.includes(state.lastProvider)) {
    setPill("warn", `${NAMES[primary]} unavailable · using ${NAMES[state.lastProvider]}`);
    return;
  }
  if (chain.length === 1) {
    setPill("warn", `Only ${NAMES[primary]} configured (no fallback)`);
    return;
  }
  const rest = chain.slice(1).map((n) => NAMES[n]);
  setPill("ok", `${NAMES[primary]} · ${rest.join(", ")} fallback${rest.length > 1 ? "s" : ""} ready`);
}

function renderCorpus(h) {
  const box = document.getElementById("corpus-chips");
  box.replaceChildren(...(h.corpus || []).map((c) => el("span", {
    class: `chip ${specClass(c.spec, "chip")}`, text: `${c.spec} V${c.version}`,
  })));
}

async function checkHealth() {
  const banner = document.getElementById("health-banner");
  try {
    const h = await api.health();
    state.health = h;
    renderCorpus(h);
    updatePill();
    applyHealthToSettings(h);
    if (h.status === "error") {
      document.getElementById("health-message").textContent = h.error ? h.error.message : "The assistant is not ready.";
      document.getElementById("health-fix").textContent = h.error && h.error.fix ? h.error.fix : "";
      banner.hidden = false;
      state.ready = false;
    } else {
      banner.hidden = true;
      state.ready = true;
    }
  } catch (err) {
    document.getElementById("health-message").textContent = err.message;
    document.getElementById("health-fix").textContent = err.fix || "";
    banner.hidden = false;
    state.ready = false;
    setPill("err", "Server unreachable");
  }
  updateSend();
}

function route() {
  const isEval = location.hash === "#/evaluation";
  document.getElementById("view-chat").hidden = isEval;
  document.getElementById("view-eval").hidden = !isEval;
  const [on, off] = isEval ? ["nav-eval", "nav-chat"] : ["nav-chat", "nav-eval"];
  document.getElementById(on).setAttribute("aria-current", "page");
  document.getElementById(off).removeAttribute("aria-current");
  if (isEval) renderEvaluation();
  if (location.hash !== "#/chat" && !isEval) history.replaceState(null, "", "#/chat");
}

async function boot() {
  state.ready = false;
  await loadCitationPattern().catch(() => null);
  let examples = { architecture: [], nas: [], cross: [] };
  try { examples = await api.examples(); } catch { /* keep empty */ }
  initSettings(() => refreshPipelineLine());
  initChat(examples, {
    onAnswer: (data) => {
      if (data.llm && data.llm.called) state.lastProvider = data.llm.provider;
      updatePill();
    },
  });
  renderSidebarExamples(examples, ask);
  document.getElementById("health-retry").addEventListener("click", checkHealth);
  window.addEventListener("hashchange", route);
  route();
  await checkHealth();
  render();
}

boot();
