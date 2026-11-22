"""Cross-encoder reranking (bge-reranker-v2-m3 by default, sigmoid scores in [0, 1]).

The model is loaded once per model name; `max_length` (truncation of each query+chunk pair)
is applied per call, so changing it never loads a second copy of the model.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from src.index.embed import detect_device
from src.schemas import RetrievedChunk

log = logging.getLogger(__name__)
BATCH_SIZE = 16


@lru_cache(maxsize=2)
def get_reranker(model_name: str):
    import torch
    from sentence_transformers import CrossEncoder

    device = detect_device()
    kwargs = {"torch_dtype": torch.float16} if device == "cuda" else {}
    log.info("Loading reranker %s on %s", model_name, device)
    return CrossEncoder(
        model_name, device=device, activation_fn=torch.nn.Sigmoid(), model_kwargs=kwargs
    )


def rerank(
    query: str, candidates: list[RetrievedChunk], model_name: str, max_length: int = 1024
) -> list[RetrievedChunk]:
    """Score (query, chunk text) pairs and sort candidates by rerank score (desc)."""
    if not candidates:
        return []
    model = get_reranker(model_name)
    model.max_seq_length = max_length
    pairs = [(query, rc.chunk.text) for rc in candidates]
    scores = model.predict(pairs, batch_size=BATCH_SIZE, show_progress_bar=False)
    for rc, s in zip(candidates, scores, strict=True):
        rc.rerank_score = float(s)
    return sorted(candidates, key=lambda r: -(r.rerank_score or 0.0))
