# Repository Guidelines

## Project Structure & Module Organization

ConvIQ is a Python 3.11+ conversation intelligence backend with a small static web frontend. `apps/api/` contains the FastAPI app (`apps.api.main:app`) and routers for calls, domains, and health. `apps/worker/` contains the Celery entrypoint and pipeline task orchestration. Shared code lives in `core/`, including settings, SQLAlchemy models, database sessions, and domain loading. ML and analysis stages live in `pipeline/`. Domain configurations are YAML files in `domains/`. Infrastructure lives in `infra/` (`docker-compose.yml`, Dockerfile, Alembic environment and migrations). Tests are under `tests/`; static frontend files are under `web/`.

## Build, Test, and Development Commands

- `uv sync --all-extras`: install runtime, dev, training, and eval dependencies.
- `uv run alembic upgrade head`: apply database migrations.
- `uv run uvicorn apps.api.main:app --reload`: run the API locally.
- `uv run celery -A apps.worker.celery_app:celery_app worker --loglevel=info`: run the worker locally.
- `docker compose -f infra/docker-compose.yml up -d --build`: start the full stack.
- `uv run pytest`: run all tests.
- `uv run ruff check .` and `uv run ruff format .`: lint and format.
- `uv run mypy apps core pipeline`: run type checks.

## Coding Style & Naming Conventions

Use Ruff formatting with a 100-character line length and Python 3.11 target. Prefer typed Pydantic models and explicit schemas for API and LLM boundaries. Use `snake_case` for modules, functions, variables, and YAML IDs; use `PascalCase` for classes and Pydantic models. Keep domain-specific behavior in `domains/*.yaml` when possible instead of hardcoding counseling, sales, or support assumptions.

## Testing Guidelines

Tests use `pytest` with `pytest-asyncio` enabled automatically. Place tests in `tests/` and name files `test_*.py`. Add focused tests for domain loading, prompt rendering, schemas, and pipeline behavior when changing shared contracts. Prefer offline tests for LLM prompt/schema logic; do not require external API calls in the default test suite.

## Commit & Pull Request Guidelines

History uses conventional-style commits such as `feat: add FastAPI app`, `test: add offline tests`, `docs: update plans`, and `chore: remove stale .gitkeep`. Keep commits scoped and imperative. Pull requests should describe the change, note affected areas (`apps/api`, `pipeline`, `infra`, etc.), list test commands run, link related issues or plan phases, and include screenshots only for `web/` UI changes.

## Security & Configuration Tips

Do not commit secrets. Local runs need service configuration plus keys such as `GEMINI_API_KEY` and `HF_TOKEN`; see `core/config.py` for settings. `ffmpeg` is required by Whisper and is installed in the Docker image.
