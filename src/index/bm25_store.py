"""Sparse BM25 index (bm25s) over all chunks, using the telecom tokenizer of §6."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from src.config import INDEX_DIR
from src.ingest.tokenizer import tokenize
from src.schemas import Chunk

log = logging.getLogger(__name__)

BM25_DIR = INDEX_DIR / "bm25"


class BM25Store:
    """One global index. Spec filtering is applied on the full score vector, which is exact
    and cheap for a corpus of a few thousand chunks (equivalent to the "larger pool, then
    filter" strategy of §7 without its truncation risk)."""

    def __init__(self, retriever, chunks: list[Chunk], stem: bool = False):
        self.retriever = retriever
        self.chunks = chunks
        self.stem = stem
        self._spec = np.array([c.spec for c in chunks])

    @classmethod
    def build(cls, chunks: list[Chunk], stem: bool = False) -> BM25Store:
        import bm25s

        corpus_tokens = [tokenize(c.text, stem=stem) for c in chunks]
        retriever = bm25s.BM25()
        retriever.index(corpus_tokens, show_progress=False)
        return cls(retriever, chunks, stem)

    def save(self, path: Path = BM25_DIR) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.retriever.save(str(path))
        meta = {"chunk_ids": [c.chunk_id for c in self.chunks], "stem": self.stem}
        (path / "chunk_ids.json").write_text(json.dumps(meta), encoding="utf-8")

    @classmethod
    def load(cls, chunks_by_id: dict[str, Chunk], path: Path = BM25_DIR) -> BM25Store:
        import bm25s

        meta_path = path / "chunk_ids.json"
        if not meta_path.exists():
            raise FileNotFoundError(
                f"BM25 index missing in {path}: run `python -m src.index.build_index`"
            )
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        retriever = bm25s.BM25.load(str(path))
        chunks = [chunks_by_id[i] for i in meta["chunk_ids"]]
        return cls(retriever, chunks, meta.get("stem", False))

    def scores(self, query: str) -> np.ndarray:
        vocab = self.retriever.vocab_dict
        toks = [t for t in tokenize(query, stem=self.stem) if t in vocab]
        if not toks:
            return np.zeros(len(self.chunks), dtype=np.float32)
        return np.asarray(self.retriever.get_scores(toks), dtype=np.float32)

    def search(
        self, query: str, top_n: int, specs: set[str] | None = None
    ) -> list[tuple[Chunk, float]]:
        """Top-n (chunk, score) with score > 0, optionally restricted to `specs`."""
        sc = self.scores(query)
        if specs:
            sc = np.where(np.isin(self._spec, list(specs)), sc, 0.0)
        order = np.argsort(-sc, kind="stable")[:top_n]
        return [(self.chunks[i], float(sc[i])) for i in order if sc[i] > 0]
