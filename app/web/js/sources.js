// Sources panel (UI_SPEC.md §4.5).
import { citationMatches } from "./citations.js";
import { el, fmt, markdownFragment, specClass } from "./dom.js";

const panel = () => document.getElementById("sources");
const list = () => document.getElementById("sources-list");
const meta = () => document.getElementById("sources-meta");

function scoreLine(src, rerankerOn) {
  const parts = [];
  if (src.rerank_score !== null && src.rerank_score !== undefined) {
    parts.push(`rerank ${fmt(src.rerank_score)}`);
  }
  if (src.dense_rank) parts.push(`dense #${src.dense_rank}`);
  if (src.bm25_rank) parts.push(`BM25 #${src.bm25_rank}`);
  if (!rerankerOn && src.rrf_score) parts.push(`RRF ${fmt(src.rrf_score, 3)}`);
  return parts.join(" · ");
}

function body(src) {
  const box = el("div", { class: "src-body", id: `body-${src.chunk_id}` });
  if (src.content_type === "table") {
    box.classList.add("table-body");
    box.append(el("div", { class: "table-scroll" }, markdownFragment(src.text)));
  } else {
    box.textContent = src.text;
  }
  return box;
}

function card(src, answer, expanded) {
  const rerankerOn = answer.config.use_reranker;
  const head = el("button", {
    class: "src-head", type: "button", "aria-expanded": String(expanded),
    "aria-controls": `body-${src.chunk_id}`,
  },
  el("div", { class: "src-line" },
    el("span", { class: "src-rank", text: `#${src.final_rank ?? "—"}` }),
    el("span", { class: `chip ${specClass(src.spec, "chip")}`, text: `${src.spec} §${src.section}` }),
    src.cited ? el("span", { class: "cited-label", text: "Cited" }) : null),
  el("div", { class: "src-title", text: src.title }),
  el("div", {
    class: "src-scores",
    text: src.below_gate
      ? `rerank ${fmt(src.rerank_score)} · below gate ${fmt(answer.gate.threshold)}`
      : scoreLine(src, rerankerOn),
  }));
  const wrapper = el("div", {
    class: `src${src.cited ? "" : " uncited"}`, "data-spec": src.spec,
    "data-section": src.section,
  }, head);
  const b = body(src);
  b.hidden = !expanded;
  wrapper.append(b);
  head.addEventListener("click", () => {
    const open = head.getAttribute("aria-expanded") === "true";
    for (const other of list().querySelectorAll(".src")) {
      other.querySelector(".src-head").setAttribute("aria-expanded", "false");
      other.querySelector(".src-body").hidden = true;
    }
    head.setAttribute("aria-expanded", String(!open));
    b.hidden = open;
  });
  return wrapper;
}

export function renderPlaceholder() {
  meta().textContent = "";
  list().replaceChildren(el("div", { class: "placeholder", text: "Sources for an answer appear here." }));
}

export function renderSources(answer) {
  if (!answer) return renderPlaceholder();
  const srcs = [...(answer.sources || [])].sort((a, b) => (a.final_rank ?? 99) - (b.final_rank ?? 99));
  const gateRefused = Boolean(answer.refused && !(answer.llm && answer.llm.called));
  meta().textContent = `${srcs.length} chunks · ${answer.config && answer.config.use_reranker === false ? "RRF order" : "reranked"}`;
  const nodes = [];
  if (gateRefused) {
    nodes.push(el("div", { class: "gate-box" },
      el("strong", { text: "No source passed the relevance gate" }),
      el("div", { text: "The closest candidates are listed below, so you can see what was found." })));
  }
  const firstCited = srcs.findIndex((s) => s.cited);
  srcs.forEach((s, i) => nodes.push(card(s, answer, i === firstCited)));
  if (!srcs.length && !gateRefused) {
    nodes.push(el("div", { class: "placeholder", text: "No sources were retrieved." }));
  }
  list().replaceChildren(...nodes);
}

// Open, scroll to and flash the source matching a citation chip.
export function focusSource(cite) {
  const cards = [...list().querySelectorAll(".src")];
  const target = cards.find((c) => citationMatches(cite, { spec: c.dataset.spec, section: c.dataset.section }));
  if (!target) return;
  const head = target.querySelector(".src-head");
  if (head.getAttribute("aria-expanded") !== "true") head.click();
  target.scrollIntoView({ behavior: "smooth", block: "nearest" });
  target.classList.remove("flash");
  void target.offsetWidth; // restart the animation
  target.classList.add("flash");
}

// < 900px: move the panel under the selected answer; otherwise keep it in the grid.
export function placeSourcesPanel(container) {
  const p = panel();
  const narrow = window.matchMedia("(max-width: 899px)").matches;
  if (narrow && container) {
    p.classList.add("inline");
    container.append(p);
  } else if (!narrow) {
    p.classList.remove("inline");
    document.getElementById("view-chat").append(p);
  }
}
