"""Build all indexes: parse -> chunk -> embed (cached) -> Qdrant upsert -> BM25.

    python -m src.index.build_index [--rebuild] [--embedding-model BAAI/bge-small-en-v1.5]
                                    [--skip-parse] [--no-dense]

Idempotent: chunks are deterministic, embeddings are cached by sha256(chunks.jsonl), and the
Qdrant collection is only re-uploaded when missing, incomplete, or with --rebuild.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from src.config import load_settings
from src.index.bm25_store import BM25Store
from src.index.embed import embed_chunks_cached
from src.index.qdrant_store import QdrantStore
from src.ingest.chunker import CHUNKS_PATH, build_chunks, load_chunks

log = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Build Qdrant + BM25 indexes")
    ap.add_argument("--rebuild", action="store_true", help="recreate the Qdrant collection")
    ap.add_argument("--embedding-model", help="override embedding.model (e.g. bge-small)")
    ap.add_argument("--skip-parse", action="store_true", help="reuse existing chunks.jsonl")
    ap.add_argument("--no-dense", action="store_true", help="only build BM25")
    args = ap.parse_args(argv)

    overrides = {"embedding": {"model": args.embedding_model}} if args.embedding_model else None
    settings = load_settings(overrides)
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    if args.skip_parse and CHUNKS_PATH.exists():
        chunks = load_chunks()
    else:
        chunks = build_chunks()
    timings["parse+chunk"] = time.perf_counter() - t0
    print(f"chunks: {len(chunks)}")

    t0 = time.perf_counter()
    BM25Store.build(chunks).save()
    timings["bm25"] = time.perf_counter() - t0
    print("bm25: built")

    if not args.no_dense:
        emb = settings.embedding
        t0 = time.perf_counter()
        vecs = embed_chunks_cached(
            [c.chunk_id for c in chunks],
            [c.text for c in chunks],
            emb.model,
            CHUNKS_PATH,
            emb.batch_size,
            emb.max_seq_length,
        )
        timings["embed"] = time.perf_counter() - t0
        store = QdrantStore(settings)
        t0 = time.perf_counter()
        if args.rebuild or store.count() != len(chunks):
            store.recreate(vecs.shape[1])
            store.upsert(chunks, vecs)
        else:
            print(f"qdrant: collection {store.collection} already complete, skipping upload")
        timings["qdrant"] = time.perf_counter() - t0
        print(f"qdrant: {store.collection} has {store.count()} points (dim {vecs.shape[1]})")

    print("timings: " + ", ".join(f"{k} {v:.1f}s" for k, v in timings.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
