# Shortcuts for the commands in README.md.
# On Windows without `make`, run the commands directly.
PY ?= python

.PHONY: install env corpus inspect chunks samples qdrant index models app app-fast review eval-retrieval eval-generation latency report test lint format check

install:
	$(PY) -m pip install -r requirements.lock
	$(PY) -m pip install -e ".[dev]" --no-deps

env:
	cp -n .env.example .env

corpus:
	$(PY) scripts/download_corpus.py

inspect:
	$(PY) scripts/inspect_docx_styles.py

chunks:
	$(PY) -m src.ingest.chunker

samples:
	$(PY) scripts/sample_chunks.py

qdrant:
	docker compose up -d qdrant

index:
	$(PY) -m src.index.build_index --rebuild

models:
	$(PY) -m src.generation.llm --list

app:
	$(PY) -m uvicorn app.server:app --host 127.0.0.1 --port 8000

app-fast:  # fast demo profile: bge-reranker-base (configs/fast.yaml)
	RAG_CONFIG=configs/fast.yaml $(PY) -m uvicorn app.server:app --host 127.0.0.1 --port 8000

review:
	$(PY) -m eval.make_testset_review

eval-retrieval:
	$(PY) -m eval.run_retrieval_eval --all-ablations

eval-generation:
	$(PY) -m eval.run_generation_eval --provider gemini --configs best,baseline,no_hybrid,no_reranker,no_routing

latency:
	$(PY) -m eval.measure_latency

report:
	$(PY) -m eval.make_report

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .

check: test lint
	ruff format --check .
