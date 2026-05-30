# Repository Guidelines

## Project Structure & Module Organization

ConvIQ is a Python 3.11+ conversation intelligence backend. `apps/api/` contains the FastAPI app (`apps.api.main:app`) and routers for calls, domains, and health. `apps/worker/` contains the Celery entrypoint and pipeline task orchestration. Shared code lives in `core/`, including settings, SQLAlchemy models, database sessions, domain loading, and pipeline contracts. ML and analysis stages live in `pipeline/`. Domain configurations are YAML files in `domains/`. Infrastructure lives in `infra/` (`docker-compose.yml`, Dockerfile, Alembic environment and migrations). Tests are under `tests/`.

## Build, Test, and Development Commands

- `conda create -n conviq python=3.12 && conda activate conviq`: create and enter the local environment.
- `python -m pip install -e ".[dev,training,eval]"`: install dependencies inside the active conda environment.
- `alembic upgrade head`: apply database migrations.
- `uvicorn apps.api.main:app --reload`: run the API locally.
- `celery -A apps.worker.celery_app:celery_app worker --loglevel=info`: run the worker locally.
- `docker compose -f infra/docker-compose.yml up -d --build`: start the full stack.
- `pytest`: run all tests.
- `ruff check .` and `ruff format .`: lint and format.
- `mypy apps core pipeline`: run type checks.

## Coding Style & Naming Conventions

Use Ruff formatting with a 100-character line length and Python 3.11 target. Prefer typed Pydantic models and explicit schemas for API and LLM boundaries. Use `snake_case` for modules, functions, variables, and YAML IDs; use `PascalCase` for classes and Pydantic models. Keep domain-specific behavior in `domains/*.yaml` when possible instead of hardcoding counseling, sales, or support assumptions.

## Testing Guidelines

Tests use `pytest` with `pytest-asyncio` enabled automatically. Place tests in `tests/` and name files `test_*.py`. Add focused tests for domain loading, prompt rendering, schemas, and pipeline behavior when changing shared contracts. Prefer offline tests for LLM prompt/schema logic; do not require external API calls in the default test suite.

## Commit & Pull Request Guidelines

History uses conventional-style commits such as `feat: add FastAPI app`, `test: add offline tests`, `docs: update plans`, and `chore: remove stale files`. Keep commits scoped and imperative. Pull requests should describe the change, note affected areas (`apps/api`, `pipeline`, `infra`, etc.), list test commands run, and link related issues or plan phases.

## Security & Configuration Tips

Do not commit secrets. Local runs need service configuration plus keys such as `GEMINI_API_KEY` and `HF_TOKEN`; see `core/config.py` for settings. `ffmpeg` is required by Whisper and is installed in the Docker image.
