"""Project settings: `config.yaml` (+ optional env overrides) loaded into a typed `Settings`.

Precedence (highest first): explicit overrides passed to `load_settings`, environment
variables prefixed `RAG_` (nested with `__`, e.g. `RAG_RETRIEVAL__USE_HYBRID=false`),
then `config.yaml`. API keys are NOT part of Settings; they are read from `.env` by
`src.generation.llm`.
"""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

ROOT = Path(__file__).resolve().parents[1]
# Corpus variants (bonus experiments, e.g. `configs/rel17.yaml`) are selected with the
# RAG_CONFIG environment variable; each variant gets its own processed/ and index/ folders
# (named after the config file) so the main index is never overwritten.
_CONFIG_ENV = os.getenv("RAG_CONFIG", "")
CONFIG_PATH = ROOT / _CONFIG_ENV if _CONFIG_ENV else ROOT / "config.yaml"
VARIANT = Path(_CONFIG_ENV).stem if _CONFIG_ENV else ""
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed" / VARIANT if VARIANT else DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "index" / VARIANT if VARIANT else DATA_DIR / "index"


class SpecConfig(BaseModel):
    id: str  # "TS 23.501"
    short: str  # "23.501"
    version: str  # "18.12.0"
    release: str  # "Rel-18"
    file: str  # "23501-ic0.zip"
    url: str


class CorpusConfig(BaseModel):
    specs: list[SpecConfig]


class ChunkingConfig(BaseModel):
    max_tokens: int = 800
    overlap_tokens: int = 100
    min_tokens: int = 30


class EmbeddingConfig(BaseModel):
    model: str = "BAAI/bge-m3"
    batch_size: int = 16
    max_seq_length: int = 1024


class QdrantConfig(BaseModel):
    url: str = "http://localhost:6333"
    path: str = "data/index/qdrant"
    collection: str = "3gpp_rel18_bge-m3"


class RetrievalConfig(BaseModel):
    dense_top_n: int = 50
    sparse_top_n: int = 50
    rrf_k: int = 60
    fused_top_n: int = 30
    final_top_k: int = 6
    min_per_spec_when_both: int = 2
    use_hybrid: bool = True
    use_reranker: bool = True
    use_routing: bool = True
    translate_query_for_bm25: bool = False  # bonus: non-English questions -> English for BM25


class GateConfig(BaseModel):
    reranker_threshold: float = 0.15
    dense_threshold: float = 0.45


class RerankerConfig(BaseModel):
    model: str = "BAAI/bge-reranker-v2-m3"
    max_length: int = 1024


class LLMConfig(BaseModel):
    provider: Literal["auto", "gemini", "groq", "grok"] = "auto"
    temperature: float = 0.0
    max_tokens: int = 1024


class Settings(BaseSettings):
    """Typed view of `config.yaml`."""

    model_config = SettingsConfigDict(
        yaml_file=CONFIG_PATH,
        env_prefix="RAG_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    corpus: CorpusConfig
    chunking: ChunkingConfig = ChunkingConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    qdrant: QdrantConfig = QdrantConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    gate: GateConfig = GateConfig()
    reranker: RerankerConfig = RerankerConfig()
    llm: LLMConfig = LLMConfig()
    seed: int = 42

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, env_settings, YamlConfigSettingsSource(settings_cls))

    def spec(self, spec_id_or_short: str) -> SpecConfig:
        """Return the spec config matching `TS 24.501` or `24.501`."""
        for s in self.corpus.specs:
            if spec_id_or_short in (s.id, s.short):
                return s
        raise KeyError(spec_id_or_short)


def _deep_merge(base: dict[str, Any], upd: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, val in upd.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def load_settings(overrides: dict[str, Any] | None = None) -> Settings:
    """Load settings, applying nested `overrides`, e.g. `{"retrieval": {"use_hybrid": False}}`.

    Ablations must go through this function (or env vars), never through code edits.
    """
    base = Settings()
    if not overrides:
        return base
    return Settings.model_validate(_deep_merge(base.model_dump(), overrides))
