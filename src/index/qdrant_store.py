"""Qdrant vector store: Docker server by default, local on-disk mode when `qdrant.url` is ""."""

from __future__ import annotations

import logging
import uuid
from functools import lru_cache

import numpy as np

from src.config import ROOT, Settings
from src.index.embed import model_slug
from src.schemas import Chunk

log = logging.getLogger(__name__)

PAYLOAD_KEYWORD_FIELDS = ("spec", "release", "section", "content_type")
UPLOAD_BATCH = 256


class QdrantUnavailable(RuntimeError):
    """Raised with an actionable message when the vector store cannot be reached."""


def collection_name(settings: Settings) -> str:
    """Configured collection, re-suffixed with the model slug if another model is used."""
    base = settings.qdrant.collection
    slug = model_slug(settings.embedding.model)
    if base.endswith(slug):
        return base
    return f"{base.rsplit('_', 1)[0]}_{slug}"


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


@lru_cache(maxsize=2)
def _client(url: str, path: str):
    from qdrant_client import QdrantClient

    if url:
        client = QdrantClient(url=url, timeout=30)
        try:
            client.get_collections()
        except Exception as e:
            raise QdrantUnavailable(
                f"Cannot reach Qdrant at {url} ({e.__class__.__name__}). Start it with "
                '`docker compose up -d qdrant`, or set `qdrant.url: ""` in config.yaml to use '
                "local on-disk mode (then rebuild the index)."
            ) from e
        return client
    full = ROOT / path
    full.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(full))


def get_client(settings: Settings):
    return _client(settings.qdrant.url, settings.qdrant.path)


class QdrantStore:
    def __init__(self, settings: Settings):
        self.client = get_client(settings)
        self.collection = collection_name(settings)

    def exists(self) -> bool:
        return self.client.collection_exists(self.collection)

    def count(self) -> int:
        if not self.exists():
            return 0
        return self.client.count(self.collection, exact=True).count

    def recreate(self, dim: int) -> None:
        from qdrant_client import models

        if self.exists():
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )
        for field in PAYLOAD_KEYWORD_FIELDS:
            self.client.create_payload_index(
                self.collection, field_name=field, field_schema=models.PayloadSchemaType.KEYWORD
            )

    def upsert(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        from qdrant_client import models

        for start in range(0, len(chunks), UPLOAD_BATCH):
            batch = chunks[start : start + UPLOAD_BATCH]
            points = [
                models.PointStruct(
                    id=point_id(c.chunk_id),
                    vector=vectors[start + i].tolist(),
                    payload=c.model_dump(),
                )
                for i, c in enumerate(batch)
            ]
            self.client.upsert(self.collection, points=points, wait=True)
        log.info("Upserted %d points into %s", len(chunks), self.collection)

    def search(
        self,
        query_vec: np.ndarray,
        top_n: int,
        specs: set[str] | None = None,
        release: str | None = None,
    ) -> list[tuple[Chunk, float]]:
        """Cosine search, optionally filtered by spec(s) and release. Returns (chunk, score)."""
        from qdrant_client import models

        must = []
        if specs:
            must.append(models.FieldCondition(key="spec", match=models.MatchAny(any=sorted(specs))))
        if release:
            must.append(
                models.FieldCondition(key="release", match=models.MatchValue(value=release))
            )
        res = self.client.query_points(
            self.collection,
            query=query_vec.tolist(),
            limit=top_n,
            query_filter=models.Filter(must=must) if must else None,
            with_payload=True,
        )
        return [(Chunk.model_validate(p.payload), float(p.score)) for p in res.points]
