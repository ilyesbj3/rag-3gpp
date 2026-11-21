# Shortcuts for the commands in CLAUDE.md §15.
# On Windows without `make`, run the commands directly.
PY ?= python

.PHONY: install env corpus inspect qdrant index models app eval-retrieval eval-generation report test lint format check

install:
	$(PY) -m pip install -e ".[dev]"

env:
	cp -n .env.example .env

corpus:
	$(PY) scripts/download_corpus.py

inspect:
	$(PY) scripts/inspect_docx_styles.py

qdrant:
	docker compose up -d qdrant

index:
	$(PY) -m src.index.build_index --rebuild

models:
	$(PY) -m src.generation.llm --list

app:
	streamlit run app/streamlit_app.py

eval-retrieval:
	$(PY) -m eval.run_retrieval_eval --all-ablations

eval-generation:
	$(PY) -m eval.run_generation_eval --provider gemini --configs best,baseline,no_hybrid,no_reranker,no_routing

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
