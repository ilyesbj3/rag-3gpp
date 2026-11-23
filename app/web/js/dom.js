// Tiny DOM helpers. Text always goes through textContent; HTML only after DOMPurify.
const SVG_NS = "http://www.w3.org/2000/svg";

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : String(v));
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

const ICONS = {
  info: ["M12 16v-4", "M12 8h.01", "circle:12,12,10"],
  alert: ["M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",
    "M12 9v4", "M12 17h.01"],
  copy: ["rect:9,9,13,13,2", "M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"],
  retry: ["M3 12a9 9 0 1 0 3-6.7L3 8", "M3 3v5h5"],
};

export function icon(name) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("class", "icon");
  svg.setAttribute("aria-hidden", "true");
  for (const part of ICONS[name] || []) {
    let shape;
    if (part.startsWith("circle:")) {
      const [cx, cy, r] = part.slice(7).split(",");
      shape = document.createElementNS(SVG_NS, "circle");
      shape.setAttribute("cx", cx); shape.setAttribute("cy", cy); shape.setAttribute("r", r);
    } else if (part.startsWith("rect:")) {
      const [x, y, w, h, rx] = part.slice(5).split(",");
      shape = document.createElementNS(SVG_NS, "rect");
      shape.setAttribute("x", x); shape.setAttribute("y", y);
      shape.setAttribute("width", w); shape.setAttribute("height", h); shape.setAttribute("rx", rx);
    } else {
      shape = document.createElementNS(SVG_NS, "path");
      shape.setAttribute("d", part);
    }
    svg.append(shape);
  }
  return svg;
}

export function specClass(spec, prefix) {
  if (spec === "TS 23.501") return `${prefix}-23`;
  if (spec === "TS 24.501") return `${prefix}-24`;
  return `${prefix}-both`;
}

export function fmt(v, digits = 2) {
  return typeof v === "number" && Number.isFinite(v) ? v.toFixed(digits) : "—";
}

// Markdown -> sanitized DOM fragment (tag allowlist).
const ALLOWED_TAGS = ["p", "ol", "ul", "li", "strong", "em", "code", "pre", "br", "table",
  "thead", "tbody", "tr", "th", "td"];

export function markdownFragment(text) {
  const tpl = document.createElement("template");
  if (window.marked && window.DOMPurify) {
    const html = window.marked.parse(text || "", { gfm: true, breaks: false });
    tpl.innerHTML = window.DOMPurify.sanitize(html, { ALLOWED_TAGS, ALLOWED_ATTR: [] });
  } else {
    for (const para of String(text || "").split(/\n{2,}/)) {
      tpl.content.append(el("p", { text: para }));
    }
  }
  return tpl.content;
}

export function announce(msg) {
  const live = document.getElementById("live");
  live.textContent = "";
  setTimeout(() => { live.textContent = msg; }, 50);
}
