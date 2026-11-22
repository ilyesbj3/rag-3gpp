"""Dense embeddings with sentence-transformers (bge-m3 by default), cached on disk."""

from __future__ import annotations

import hashlib
import json
import logging
from functools import lru_cache
from pathlib import Path

import numpy as np

from src.config import INDEX_DIR

log = logging.getLogger(__name__)

# Models that need an instruction prefix on the query side (documents are embedded as is).
QUERY_PREFIX = {
    "BAAI/bge-small-en-v1.5": "Represent this sentence for searching relevant passages: ",
}


def model_slug(model_name: str) -> str:
    """`BAAI/bge-m3` -> `bge-m3`."""
    return model_name.split("/")[-1].lower()


def detect_device() -> str:
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@lru_cache(maxsize=4)
def get_embedder(model_name: str, max_seq_length: int = 1024):
    """Load a SentenceTransformer once per (model, max length). fp16 only on CUDA."""
    from sentence_transformers import SentenceTransformer

    device = detect_device()
    kwargs = {"torch_dtype": "float16"} if device == "cuda" else {}
    log.info("Loading embedder %s on %s", model_name, device)
    model = SentenceTransformer(model_name, device=device, model_kwargs=kwargs)
    # never exceed what the model supports (bge-small-en-v1.5: 512 positions)
    model.max_seq_length = min(max_seq_length, model.max_seq_length or max_seq_length)
    return model


def embed_documents(
    texts: list[str], model_name: str, batch_size: int = 16, max_seq_length: int = 1024
) -> np.ndarray:
    """Normalized float32 document embeddings, shape (n, dim)."""
    model = get_embedder(model_name, max_seq_length)
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 64,
        convert_to_numpy=True,
    )
    return vecs.astype(np.float32)


def embed_query(text: str, model_name: str, max_seq_length: int = 1024) -> np.ndarray:
    """Normalized query embedding (adds the model's query instruction if it has one)."""
    model = get_embedder(model_name, max_seq_length)
    q = QUERY_PREFIX.get(model_name, "") + text
    return model.encode([q], normalize_embeddings=True, convert_to_numpy=True)[0].astype(np.float32)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def cache_paths(model_name: str, chunks_path: Path) -> tuple[Path, Path]:
    key = f"emb_{model_slug(model_name)}_{file_sha256(chunks_path)[:12]}"
    return INDEX_DIR / f"{key}.npy", INDEX_DIR / f"{key}.ids.json"


def embed_chunks_cached(
    ids: list[str],
    texts: list[str],
    model_name: str,
    chunks_path: Path,
    batch_size: int = 16,
    max_seq_length: int = 1024,
) -> np.ndarray:
    """Embed all chunks, reusing `data/index/emb_<model>_<sha(chunks.jsonl)[:12]>.npy`."""
    vec_path, ids_path = cache_paths(model_name, chunks_path)
    if vec_path.exists() and ids_path.exists():
        cached_ids = json.loads(ids_path.read_text(encoding="utf-8"))
        if cached_ids == ids:
            log.info("Embedding cache hit: %s", vec_path.name)
            return np.load(vec_path)
        log.warning("Embedding cache ids differ from chunks; recomputing")
    vecs = _reuse_or_embed(ids, texts, model_name, batch_size, max_seq_length)
    vec_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(vec_path, vecs)
    ids_path.write_text(json.dumps(ids), encoding="utf-8")
    log.info("Saved embeddings to %s", vec_path.name)
    return vecs


def _main_cache(model_name: str) -> dict[str, tuple[str, np.ndarray]]:
    """chunk_id -> (text, vector) from the main (non-variant) index cache, if present."""
    from src.config import DATA_DIR

    main_chunks = DATA_DIR / "processed" / "chunks.jsonl"
    if not main_chunks.exists():
        return {}
    key = f"emb_{model_slug(model_name)}_{file_sha256(main_chunks)[:12]}"
    vec_path = DATA_DIR / "index" / f"{key}.npy"
    ids_path = DATA_DIR / "index" / f"{key}.ids.json"
    if not (vec_path.exists() and ids_path.exists()):
        return {}
    vecs = np.load(vec_path)
    ids = json.loads(ids_path.read_text(encoding="utf-8"))
    texts = {}
    with main_chunks.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            texts[row["chunk_id"]] = row["text"]
    return {i: (texts.get(i, ""), vecs[k]) for k, i in enumerate(ids)}


def _reuse_or_embed(
    ids: list[str], texts: list[str], model_name: str, batch_size: int, max_seq_length: int
) -> np.ndarray:
    """Reuse vectors of chunks whose id AND text are identical in the main index cache
    (corpus-variant builds), embed only the rest."""
    from src.config import VARIANT

    known = _main_cache(model_name) if VARIANT else {}
    reuse = [
        k
        for k, (i, t) in enumerate(zip(ids, texts, strict=True))
        if i in known and known[i][0] == t
    ]
    reused = set(reuse)
    todo = [k for k in range(len(ids)) if k not in reused]
    log.info(
        "Embeddings: %d reused from the main index cache, %d to compute", len(reuse), len(todo)
    )
    dim = None
    out: list[np.ndarray | None] = [None] * len(ids)
    for k in reuse:
        out[k] = known[ids[k]][1]
        dim = out[k].shape[0]
    if todo:
        new = embed_documents([texts[k] for k in todo], model_name, batch_size, max_seq_length)
        for j, k in enumerate(todo):
            out[k] = new[j]
        dim = new.shape[1]
    return np.vstack(out).astype(np.float32) if dim else np.zeros((0, 0), np.float32)
