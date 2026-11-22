// Citation detection, using the SAME regexes as src/generation/citation_check.py
// (exported by the server at startup to citation_pattern.json; a test asserts equality).
let PATTERN = null;

export async function loadCitationPattern() {
  const res = await fetch("citation_pattern.json");
  PATTERN = await res.json();
  return PATTERN;
}

export function setCitationPattern(p) {
  PATTERN = p;
}

// Split plain text into [{type: "text", value}, {type: "cite", spec, section, label}].
export function splitCitations(text) {
  if (!PATTERN || !text) return [{ type: "text", value: text || "" }];
  const bracket = new RegExp(PATTERN.bracket, PATTERN.flags);
  const out = [];
  let last = 0;
  let m;
  while ((m = bracket.exec(text)) !== null) {
    const inner = m[1];
    const cite = new RegExp(PATTERN.citation, PATTERN.flags);
    const found = [];
    let c;
    while ((c = cite.exec(inner)) !== null) {
      found.push({ spec: "TS " + c.groups.spec, section: c.groups.section.replace(/\.$/, "") });
    }
    if (!found.length) continue;
    if (m.index > last) out.push({ type: "text", value: text.slice(last, m.index) });
    for (const f of found) {
      out.push({ type: "cite", ...f, label: `${f.spec} §${f.section}` });
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ type: "text", value: text.slice(last) });
  return out;
}

// Does a citation (spec, section) point at a source? Exact match or the citation is an
// ancestor clause of the source (same rule as the server's "cited" flag).
export function citationMatches(cite, src) {
  if (cite.spec !== src.spec) return false;
  return src.section === cite.section || src.section.startsWith(cite.section + ".");
}
