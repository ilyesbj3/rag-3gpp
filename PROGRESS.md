# PROGRESS

Running log of the build (CLAUDE.md §17, autonomous mode). On restart: read CLAUDE.md, then
this file, then continue with the first phase not marked done.

Environment: Windows 11, CPU only, Python 3.11 venv in `.venv` (pip + `requirements.lock`),
Docker available (Qdrant default), API keys present in `.env` (never printed or committed).

## Phase status

| # | Phase | Status | Commit |
|---|---|---|---|
| 1 | Scaffold | done | feat(scaffold) |
| 2 | Corpus + VERSIONS.md + style inspection | done | feat(corpus) |
| 3 | Parser + chunker + tokenizer + tests | done | feat(ingest) |
| 4 | Embeddings + Qdrant + BM25 + build_index | todo | |
| 5 | Router, hybrid, reranker, quotas, gate | todo | |
| 6 | Prompts, citation check, pipeline | todo | |
| 7 | Streamlit app | todo | |
| 8 | Test set draft + review file | todo | |
| 9 | Retrieval eval + gate calibration | todo | |
| 10 | Generation eval + report | todo | |
| 11 | README + presentation + architecture | todo | |
| 12 | Bonuses | todo | |

## Phase 1–2 (summary)
- Corpus: TS 23.501 V18.12.0 (`23501-ic0.zip`, cover dated 2025-12) and TS 24.501 V18.14.0
  (`24501-ie0.zip`, cover dated 2026-09), one .docx each; SHA-256 in `data/VERSIONS.md`.
- Style findings recorded in CLAUDE.md §5.1 (H6/H2 heading styles, lettered clause numbers,
  annex titles with a line break, annex sub-clauses styled Heading 1, duplicate 8.2.6.35).

## Phase 3 — ingestion
- `python -m src.ingest.chunker` → `data/processed/chunks.jsonl` + `parse_report.md` (~28 s).
- **3,597 chunks**: TS 23.501 1,281 (860 sections with text, median 482 tokens, p95 777);
  TS 24.501 2,316 (1,124 sections, median 616, p95 782). Tables parsed: 54 + 541
  (3 cover tables per spec skipped). Change-history annexes skipped (23.501 R, 24.501 F).
- Acceptance checks (§5.5): all PASS (both specs, no empty section, unique ids, no table
  split mid-row).
- Spot checks, found by searching the chunks (verified section numbers):
  - 24.501 5GMM cause #9 → **§A.1** ("Causes related to UE identification").
  - 24.501 T3510 and T3502 → timer table in **§10.2** (Table 10.2.1, UE side).
  - 24.501 REGISTRATION REQUEST message content → **§8.2.6.1** (Table 8.2.6.1.1), under
    8.2.6 "Registration request".
  - 23.501 AMF / SMF / UPF → **§6.2.1 / §6.2.2 / §6.2.3**.
  - 23.501 standardized 5QI table → **§5.7.4** (Table 5.7.4-1, split by rows into parts 1–4).
  - 23.501 Network slicing → **§5.15** (heading only; text in 5.15.x sub-clauses).
- Decisions:
  - Heading-only sections (219 + 246) produce no chunk; their titles appear in descendants'
    headers/breadcrumbs.
  - 12 chunks exceed 800 tokens: each is a single table row too large to split (bit-coding
    IE tables, max 3,669 tokens). Kept whole per §16.4; the embedder truncates them at 1024
    tokens, BM25 sees everything.
  - Full-width table rows (notes) keep the text in the first column only (avoids repeating a
    long note in every column).
  - BM25 tokenizer additionally emits the parts of hyphenated terms (`5g-guti` → `guti`),
    besides the whole and de-hyphenated forms.
  - `parse_report.md` and `chunk_samples.md` are committed (rest of `data/processed/` ignored).
- Review file: `data/processed/chunk_samples.md` (15 random chunks, seed 42 + cause #9,
  T3510, REGISTRATION REQUEST, 5QI table).

## Open issues
- none

## Blocked / needs human
- none
