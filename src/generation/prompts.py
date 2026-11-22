"""Prompt templates (CLAUDE.md §9.1). The system prompt is used verbatim."""

from __future__ import annotations

from html import escape

from src.schemas import RetrievedChunk

SYSTEM_PROMPT = """You are a 3GPP 5G standards assistant. You answer questions using ONLY the sources provided
in the user message, which are excerpts from 3GPP TS 23.501 (Release 18) and TS 24.501
(Release 18).

Rules:
1. Answer in English, whatever the language of the question.
2. Use only facts stated in the sources. Do not use prior knowledge, do not guess, do not
   fill gaps. If the sources only partially answer, answer the supported part and state
   clearly which part is not covered by the documents.
3. Cite every factual sentence with the label of the source it comes from, exactly as
   written in the source's label attribute, e.g. [TS 24.501 §5.5.1.2.4]. Several labels may
   follow one sentence. Never cite a section that is not among the provided labels.
4. If the sources do not contain the information needed to answer, reply with exactly this
   sentence and nothing else:
   I could not find this information in the documents.
5. Keep names of messages, information elements, timers, cause values and network
   functions exactly as written in the sources (e.g. REGISTRATION REQUEST, T3510, 5GMM cause #9).
6. Be precise and concise. Use short paragraphs or bullet lists for procedures (ordered
   steps). For questions spanning architecture and NAS signalling, explain the procedure
   (TS 23.501) and then the NAS messages involved (TS 24.501)."""

_DEFAULT_SPECS = "3GPP TS 23.501 (Release 18) and TS 24.501\n(Release 18)"


def system_prompt_for(specs) -> str:
    """System prompt naming the corpus specs; identical to SYSTEM_PROMPT for the default corpus.

    `specs` is the list of `SpecConfig` from the settings (used by corpus-variant bonuses)."""
    names = [f"{s.id} ({s.release.replace('Rel-', 'Release ')})" for s in specs]
    if names == ["TS 23.501 (Release 18)", "TS 24.501 (Release 18)"]:
        return SYSTEM_PROMPT
    listed = ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]
    return SYSTEM_PROMPT.replace(_DEFAULT_SPECS, "3GPP " + listed)


USER_TEMPLATE = """Sources:
{context_blocks}

Question: {question}

Answer (English, with citations like [TS 24.501 §x.y.z]):"""


def format_source(i: int, rc: RetrievedChunk) -> str:
    """One `<source>` block; the text is the chunk body without its contextual header."""
    c = rc.chunk
    return (
        f'<source id="{i}" label="{c.label}" title="{escape(c.title, quote=True)}">\n'
        f"{c.body.strip()}\n</source>"
    )


def build_user_prompt(question: str, sources: list[RetrievedChunk]) -> str:
    blocks = "\n\n".join(format_source(i, rc) for i, rc in enumerate(sources, start=1))
    return USER_TEMPLATE.format(context_blocks=blocks, question=question.strip())
