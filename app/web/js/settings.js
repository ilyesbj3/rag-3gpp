// Settings sidebar (UI_SPEC.md §4.3): switches, top-k, provider, examples.
import { el } from "./dom.js";
import { saveSettings, state } from "./state.js";

const NAMES = { gemini: "Gemini", groq: "Groq", grok: "Grok" };
let appliesTimer = null;

function flashApplies() {
  const node = document.getElementById("applies");
  node.textContent = "Applies to your next question";
  clearTimeout(appliesTimer);
  appliesTimer = setTimeout(() => { node.textContent = ""; }, 3000);
}

function syncControls() {
  for (const sw of document.querySelectorAll(".switch[data-setting]")) {
    sw.setAttribute("aria-checked", String(Boolean(state.settings[sw.dataset.setting])));
  }
  document.getElementById("top-k").value = state.settings.final_top_k;
  for (const b of document.querySelectorAll("#provider-group [role=radio]")) {
    const on = b.dataset.provider === state.settings.provider;
    b.setAttribute("aria-checked", String(on));
    b.tabIndex = on ? 0 : -1;
  }
}

export function pipelineLine() {
  const s = state.settings;
  const on = (v) => (v ? "on" : "off");
  return `Pipeline: hybrid search ${on(s.use_hybrid)} · reranker ${on(s.use_reranker)} · `
    + `spec routing ${on(s.use_routing)}`;
}

export function initSettings(onChange) {
  for (const sw of document.querySelectorAll(".switch[data-setting]")) {
    sw.addEventListener("click", () => {
      const key = sw.dataset.setting;
      state.settings[key] = !state.settings[key];
      saveSettings(); syncControls(); flashApplies(); onChange();
    });
  }
  const topK = document.getElementById("top-k");
  topK.addEventListener("change", () => {
    const v = Math.min(10, Math.max(3, parseInt(topK.value, 10) || 6));
    state.settings.final_top_k = v;
    saveSettings(); syncControls(); flashApplies(); onChange();
  });
  const group = document.getElementById("provider-group");
  const radios = [...group.querySelectorAll("[role=radio]")];
  const choose = (b) => {
    if (b.disabled) return;
    state.settings.provider = b.dataset.provider;
    saveSettings(); syncControls(); flashApplies(); onChange();
  };
  radios.forEach((b) => b.addEventListener("click", () => choose(b)));
  group.addEventListener("keydown", (e) => {
    if (!["ArrowLeft", "ArrowRight"].includes(e.key)) return;
    const enabled = radios.filter((r) => !r.disabled);
    const i = enabled.findIndex((r) => r.dataset.provider === state.settings.provider);
    const next = enabled[(i + (e.key === "ArrowRight" ? 1 : enabled.length - 1)) % enabled.length];
    if (next) { choose(next); next.focus(); }
    e.preventDefault();
  });
  const toggle = document.getElementById("settings-toggle");
  toggle.addEventListener("click", () => {
    const panel = document.getElementById("settings");
    const open = !panel.classList.contains("open");
    panel.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", String(open));
  });
  syncControls();
}

// Enable only configured providers; describe the real fallback chain.
export function applyHealthToSettings(health) {
  const chain = (health && health.chain) || [];
  for (const b of document.querySelectorAll("#provider-group [role=radio]")) {
    const p = b.dataset.provider;
    const ok = p === "auto" ? chain.length > 0 : chain.includes(p);
    b.disabled = !ok;
    b.title = ok ? "" : `${NAMES[p] || p} is not configured (no API key in .env)`;
  }
  if (state.settings.provider !== "auto" && !chain.includes(state.settings.provider)) {
    state.settings.provider = "auto";
    saveSettings();
  }
  const hint = document.getElementById("provider-hint");
  if (chain.length > 1) {
    const [first, ...rest] = chain.map((n) => NAMES[n]);
    hint.textContent = `Auto uses ${first} and switches to ${rest.join(", then ")} if it fails.`;
  } else if (chain.length === 1) {
    hint.textContent = `Auto uses ${NAMES[chain[0]]} (no fallback configured).`;
  } else {
    hint.textContent = "No language model is configured.";
  }
  syncControls();
}

export function renderSidebarExamples(examples, ask) {
  const box = document.getElementById("sidebar-examples");
  const picks = ["architecture", "nas", "cross"].map((g) => (examples[g] || [])[0]).filter(Boolean);
  box.replaceChildren(...picks.map((q) => el("button", {
    class: "example-btn", type: "button", text: q, onclick: () => ask(q),
  })));
}
