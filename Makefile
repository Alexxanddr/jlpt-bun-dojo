.PHONY: dev check seed update-data

dev:
	uv run uvicorn trainer.app:app --host 127.0.0.1 --env-file .env --no-access-log
check:
	uv run ruff check .
	uv run mypy trainer
	uv run pytest
seed:
	uv run sh scripts/seed
update-data:
	uv run python -m trainer.import_data "$(or $(MANIFEST),trainer/data/manifest.json)"
