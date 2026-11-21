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
    model.max_seq_length = max_seq_length
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
    vecs = embed_documents(texts, model_name, batch_size, max_seq_length)
    vec_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(vec_path, vecs)
    ids_path.write_text(json.dumps(ids), encoding="utf-8")
    log.info("Saved embeddings to %s", vec_path.name)
    return vecs
