// Evaluation page (UI_SPEC.md §5). Every number comes from /api/eval.
import { api } from "./api.js";
import { el, fmt } from "./dom.js";

const onoff = (v) => (v ? "on" : "off");

function kpi(label, value, note) {
  return el("div", { class: "kpi" }, el("div", { class: "kpi-label", text: label }),
    el("div", { class: "kpi-value", text: value }), note ? el("div", { class: "kpi-note", text: note }) : null);
}

function retrievalTable(rows) {
  const metrics = ["recall@1", "recall@5", "recall@10", "mrr"];
  const best = Object.fromEntries(metrics.map((m) => [m, Math.max(...rows.map((r) => r[m] ?? -1))]));
  const sorted = [...rows].sort((a, b) => (b.mrr ?? 0) - (a.mrr ?? 0));
  const n = rows[0] ? rows[0].n : 0;
  return el("div", { class: "table-box" }, el("table", { class: "data" },
    el("caption", { text: `${n} in-corpus questions · gold section in top-k (prefix match)` }),
    el("thead", {}, el("tr", {},
      ["Config", "Hybrid", "Reranker", "Routing", "Recall@1", "Recall@5", "Recall@10", "MRR"]
        .map((h, i) => el("th", { scope: "col", class: i > 0 && i < 4 ? "onoff" : null, text: h })))),
    el("tbody", {}, sorted.map((r) => el("tr", {},
      el("td", { class: "cfg", text: r.config }),
      el("td", { class: "onoff", text: onoff(r.use_hybrid) }),
      el("td", { class: "onoff", text: onoff(r.use_reranker) }),
      el("td", { class: "onoff", text: onoff(r.use_routing) }),
      metrics.map((m) => {
        const td = el("td", { text: fmt(r[m]) });
        if (r[m] !== null && r[m] === best[m]) td.append(el("span", { class: "sr-only", text: " (best)" }));
        if (r[m] !== null && r[m] === best[m]) td.classList.add("best");
        return td;
      }))))));
}

function generationCard(rows) {
  const hasRef = rows.some((r) => r.refusal_accuracy !== null && r.refusal_accuracy !== undefined);
  const head = ["Config", "Faithfulness", "Correctness", "Citation acc."].concat(hasRef ? ["Refusal acc."] : []);
  return el("div", { class: "card" }, el("h2", { text: "Generation" }),
    el("div", { class: "table-box" }, el("table", { class: "data" },
      el("thead", {}, el("tr", {}, head.map((h) => el("th", { scope: "col", text: h })))),
      el("tbody", {}, rows.map((r) => el("tr", {},
        el("td", { class: "cfg", text: r.config }),
        el("td", { text: fmt(r.faithfulness) }),
        el("td", { text: fmt(r.answer_correctness) }),
        el("td", { text: fmt(r.citation_accuracy) }),
        hasRef ? el("td", { text: fmt(r.refusal_accuracy) }) : null))))));
}

function bar(cls, value) {
  const b = el("div", { class: `bar ${cls}` });
  b.style.width = `${Math.max(0, Math.min(1, value || 0)) * 100}%`;
  return el("div", { class: "bar-row" }, el("div", { class: "bar-track" }, b),
    el("div", { class: "bar-val", text: fmt(value) }));
}

function byTypeCard(bestRow, baseRow) {
  const types = [["simple_23", "Simple — TS 23.501"], ["simple_24", "Simple — TS 24.501"], ["cross", "Cross-spec"]];
  return el("div", { class: "card" }, el("h2", { text: "Recall@5 by question type" }),
    types.map(([k, label]) => el("div", { class: "bar-group" },
      el("div", { class: "hint", text: label }),
      bar("bar-best", bestRow?.by_type?.[k]?.["recall@5"]),
      bar("bar-base", baseRow?.by_type?.[k]?.["recall@5"]))),
    el("div", { class: "legend" },
      el("span", { class: "l-best", text: `best (${bestRow ? bestRow.config : "—"})` }),
      el("span", { class: "l-base", text: "baseline" })));
}

export async function renderEvaluation() {
  const view = document.getElementById("view-eval");
  view.replaceChildren(el("div", { class: "placeholder", text: "Loading evaluation results…" }));
  let data;
  try {
    data = await api.evaluation();
  } catch (err) {
    view.replaceChildren(el("div", { class: "banner banner-danger", role: "alert", text: err.message }));
    return;
  }
  if (!data.available) {
    view.replaceChildren(
      el("h1", { class: "page-title", text: "Evaluation" }),
      el("p", { class: "subtitle", text: "No evaluation results yet. Run:" }),
      el("pre", { class: "code", text: "python -m eval.run_retrieval_eval --all-ablations\n"
        + "python -m eval.run_generation_eval --provider gemini --configs best,baseline,no_hybrid,no_reranker,no_routing\n"
        + "python -m eval.make_report" }));
    return;
  }
  const t = data.testset;
  const bt = t.by_type || {};
  const ret = data.retrieval || [];
  const best = [...ret].sort((a, b) => (b.mrr ?? 0) - (a.mrr ?? 0))[0];
  const baseline = ret.find((r) => r.config === "baseline");
  const gen = data.generation || [];
  const genBest = gen.find((g) => g.config === best?.config) || gen.find((g) => g.config === "best") || gen[0];
  const nodes = [
    el("div", { class: "eval-head" },
      el("div", {},
        el("h1", { class: "page-title", text: "Evaluation" }),
        el("div", {
          class: "subtitle",
          text: `${t.total} questions · ${bt.simple || 0} simple, ${bt.cross || 0} cross-spec, `
            + `${bt.out_of_corpus || 0} out-of-corpus · LLM: ${data.run.provider} (forced)`
            + (data.run.model ? ` · ${data.run.model}` : ""),
        })),
      el("div", { class: "mono hint", text: `eval/results/ · run ${data.run.date || "—"} · commit ${data.run.commit || "—"}` })),
  ];
  if (t.verified < t.total) {
    nodes.push(el("div", {
      class: "banner banner-prelim", role: "status",
      text: `Preliminary: the gold set is pending human validation. ${t.verified} of ${t.total} items verified.`,
    }));
  }
  nodes.push(el("div", { class: "kpis" },
    kpi("Best MRR", fmt(best?.mrr), best?.config),
    kpi("Recall@5 (best config)", fmt(best?.["recall@5"]), best?.config),
    kpi("Refusal accuracy", fmt(genBest?.refusal_accuracy), genBest?.config),
    kpi("Citation accuracy", fmt(genBest?.citation_accuracy), genBest?.config)));
  nodes.push(retrievalTable(ret));
  nodes.push(el("div", { class: "two-cards" }, generationCard(gen), byTypeCard(best, baseline)));
  view.replaceChildren(...nodes);
}
