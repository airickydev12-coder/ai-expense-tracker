# AI Expense Tracker (Financial Core)
A layered Python financial platform (CLI + FastAPI backend) that tracks expenses, budgets, debt, goals, and scenario planning, currently backed by JSON files and migrating toward SQLite. A React frontend lives under `frontend/`, consuming the FastAPI backend over HTTP.

## Build, Test & Lint Commands
This project uses a `.venv` virtual environment — the global `python`/`pip` on PATH do **not** have project dependencies installed. Always invoke tools through the venv.

- Install deps: `.venv/Scripts/pip.exe install -r requirements.txt -r requirements-dev.txt`
- Run CLI app: `.venv/Scripts/python.exe main.py`
- Run API dev server: `.venv/Scripts/uvicorn.exe src.api.main:app --reload`
- Run all tests: `.venv/Scripts/python.exe -m pytest -q`
- Run a single test file: `.venv/Scripts/python.exe -m pytest tests/test_file.py -q`
- Run tests matching a keyword: `.venv/Scripts/python.exe -m pytest -k "keyword" -q`
- Type-check (lint): `npx pyright` (config: `pyrightconfig.json`; must report 0 errors/0 warnings)
- No build step — pure Python, no compilation/bundling.
- **Before reporting any change done**: run the full test suite AND `npx pyright`. Both must be clean (955+ passing, 0 pyright errors) — this project has zero tolerance for regressions introduced silently.

## Frontend (`frontend/`)
A Vite + React + TypeScript + Tailwind SPA, added in Phase 5, consuming the FastAPI backend over HTTP (CORS-enabled in `src/api/main.py` for the Vite dev server). All commands below run from inside `frontend/`.

- Install deps: `npm install`
- Run dev server: `npm run dev` (defaults to `http://localhost:5173`)
- Build for production: `npm run build`
- Run tests: `npm run test`
- Type-check: `npx tsc -b` (matches the `build` script's type-check step)
- Expects the backend running at `http://127.0.0.1:8000` (see `frontend/.env.development`, `VITE_API_BASE_URL`) — start the backend first (`.venv/Scripts/uvicorn.exe src.api.main:app --reload`), or dashboard data will show the error state rather than crash.
- Not held to the backend's "955+ tests / 0 pyright errors" bar yet — but `npm run test` should pass before reporting a frontend change done.

## Docker
A containerized deployment also exists, additive to (not a replacement for) the
`.venv`/`npm run dev` workflow above — use whichever fits the task.

- One-command startup: `docker compose up --build`
- Backend: FastAPI served by `uvicorn` on `http://localhost:8000` (same port as local
  dev; `/docs` and `/health` work identically)
- Frontend: built to static files and served by nginx on `http://localhost:3000`, which
  reverse-proxies `/api/*` to the backend container — same-origin through nginx, so no
  CORS configuration is involved in this path
- Data: `data/app.db` and the JSON files persist in a named Docker volume
  (`expense-data`), not in the image — `docker compose down` (no `-v`) keeps your data;
  `docker compose down -v` deletes it
- Secrets: copy `.env.example` to `.env` at the repo root and set `ANTHROPIC_API_KEY`
  before starting — the backend container reads it via `env_file`, never baked into the
  image
- Rebuild after a dependency or code change: `docker compose up --build`
- Stop everything: `docker compose down`
- Running the test suite in Docker is out of scope for this setup — the suite already
  isolates itself from `data/app.db` via an autouse fixture in `tests/conftest.py` and
  needs no container; run it locally as documented above.

## Architecture Decision Records
Detailed rationale lives in `docs/Architecture/`. Load the relevant one before making a change in its area rather than re-deriving the reasoning from scratch.

### Clean Architecture (layering) — `@docs/Architecture/ADR-001-clean-architecture.md.txt`
### Centralized Recommendation Engine — `@docs/Architecture/ADR-002-recommendation-engine.md.txt`
### Application Adapters — `@docs/Architecture/ADR-003-application-adapters.md.txt`
### Domain Model Responsibilities — `@docs/Architecture/ADR-004-domain-model-responsibilities.md.txt`
### Development Workflow — `@docs/Architecture/ADR-005-development-workflow.md.txt`
### Testing Strategy — `@docs/Architecture/ADR-006-testing-strategy.md.txt`

## Code Style & Architecture
- **Layering** (see ADR-001 above): `src/core/` (cross-cutting infra: config, money, exceptions, logging) → `src/financial/` (domain logic, one package per domain) → `src/api/` (FastAPI REST layer) and `src/presentation/` (CLI layer) as separate, parallel presentation adapters over the same domain.
- **Per-domain file pattern** inside `src/financial/<domain>/`: `models.py` (dataclasses with `__post_init__` validation), `repository.py` (JSON load/save), `service.py` (in-memory CRUD + orchestration), `analytics.py` (pure calculations). Follow this shape when adding a new domain.
- **Money is always `Decimal`, never `float`.** Use `src/core/money.py` helpers (`to_money`, `add_money`, `subtract_money`, `money_to_json`, `money_from_json`) instead of calling `Decimal()`/`round()` directly. Percentages, scores, ratios, and rates (e.g. interest rate, health score, scenario ranking score) are legitimately `float` — don't force those into Decimal.
- **Exceptions**: raise from `src/core/exceptions.py` (`ValidationError`, `NotFoundError`, `BusinessRuleError`, `PersistenceError`) instead of bare `ValueError`. All subclass `ValueError` for backward compatibility, so `except ValueError` / `pytest.raises(ValueError)` still work — pick the most specific subclass: input/invariant validation → `ValidationError`; "no X found" lookups → `NotFoundError`; calculation-feasibility failures → `BusinessRuleError`; malformed persisted/JSON data → `PersistenceError`. `TypeError` from `isinstance` checks is left alone (different semantics, not part of this hierarchy).
- **Logging**: get a logger via `src.core.logging.get_logger(__name__)`; never call `configure_logging()` outside the two entry points (`main.py`, `src/api/main.py`). Log at repository I/O boundaries (load/save, debug level) and service-level mutations (create/update/delete/lifecycle transitions, info level) — not blanket per-function logging.
- **Naming**: `snake_case` for functions/files/modules (standard Python), `PascalCase` for classes/dataclasses. No abbreviations in domain terms (`transaction`, not `txn`).
- **Indentation**: 4 spaces (standard Python/PEP 8).

## Technical Gotchas & Rules
- **Decimal/float arithmetic mixing raises `TypeError`.** `Decimal(5) + 0.5` fails; `Decimal(5) > 0.5` and `max(Decimal(5), 0.5)` work fine (comparisons are safe, arithmetic operators `+ - * /` are not). Convert one side explicitly before mixing.
- **`json.dump`/`json.load` cannot serialize `Decimal` natively.** For flat dataclass fields, use `money_to_json`/`money_from_json` (string round-trip). For free-form nested dicts (e.g. scenario snapshots) whose Decimal fields can appear at arbitrary depth, use the tagged encoder/decoder pattern in `src/financial/scenarios/workspace_repository.py` (`_DecimalEncoder` / `_decimal_object_hook`) rather than trying to enumerate money keys.
- **Persistence is still JSON** (`data/*.json`) — this is Phase 3 of the roadmap (SQLite + repository pattern), not yet started. Don't assume a database exists.
- **Never import test frameworks (`pytest`) into `src/` application code.** Found and removed one real instance of this; it's always a mistake, never intentional.
- **`.pyc` files are tracked in git** in this repo (pre-existing, unrelated to normal `.gitignore` behavior for build artifacts) — they will show up in `git status`/diffs alongside real changes; don't be alarmed or try to "fix" this unless asked.
- **`requirements.txt` is UTF-16 encoded** (a quirk of how it was generated) — if editing it programmatically, decode/encode as UTF-16, not UTF-8, or you'll corrupt it.
- **No database config exists to accidentally modify** yet — once SQLite lands (Phase 3), never change DB connection/migration config without asking first.
- **Ask before**: force-pushing, deleting data files under `data/`, or running destructive git operations. This project's data files are the only persistence today.
