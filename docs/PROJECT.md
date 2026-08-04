# AI Expense Tracker — Project Overview

This document describes what the product is today, who it's for, how it's built, and where
to find deeper detail. For what's planned next, see [`ROADMAP.md`](../ROADMAP.md) at the repo
root. For a dated history of what's shipped, see [`CHANGELOG.md`](CHANGELOG.md).

## What this is

A personal financial platform: expense/income/budget/bill/debt/goal tracking, scenario
planning, forecasting, and an AI financial coach, delivered as a CLI and a web app (React +
FastAPI) over a shared SQLite-backed domain core. Three AI features (expense categorization,
natural-language scenario parsing, and an agentic coach chat with tool use) call the Claude API
directly.

It began as a solo learning project ("Project Genesis" — see below) and has since crossed into
a real multi-user application: registration, login, per-user data isolation, and a platform-role
authorization model (`USER` / `ADMIN` / `SUPER_ADMIN`) are all implemented and tested.

## Who it's for, today

**Current product mode: single adult financial user, self-hosted.** Every account is a full
peer with its own isolated financial data — there is no household, guardian/child, or
educator relationship modeled yet, and no distinct "kid-safe" experience. The `PlatformRole`
enum governs *platform operator authority* (who can administer the app), not product-facing
account types — see the "Product modes" section below for what's implemented vs. planned.

## Origin: Project Genesis

This repo is being built as a mentor-guided learning curriculum (a WGU student's path toward
becoming an "AI Founder"), with reusable engineering assets (an auth module, a logging
package, an AI prompt/schema pattern) accumulating alongside the product itself. That context
explains some of the codebase's choices — e.g. raw `sqlite3` instead of an ORM, and building
JWT auth from primitives instead of an off-the-shelf library — which were deliberate learning
decisions, not oversights.

## Architecture at a glance

Layered, per [ADR-001](Architecture/ADR-001-clean-architecture.md.txt):

```
src/core/          cross-cutting infra: config, money (Decimal), exceptions, logging, db, security
src/financial/      domain logic, one package per domain (expenses, budgets, accounts, bills,
                     debt, income, goals, history, forecasting, scenarios, recommendations,
                     coach, users, notifications, recurring_expenses, ...)
src/api/            FastAPI REST layer (routers, schemas, dependencies)
src/presentation/   CLI layer
frontend/           Vite + React + TypeScript + Tailwind SPA, consumes the API over HTTP
```

Each domain package follows the same internal shape (`models.py` / `repository.py` /
`service.py` / `analytics.py`) — see ADR-004. Persistence is a single SQLite file
(`data/app.db`) via raw `sqlite3`, no ORM, self-healing schema (`CREATE TABLE IF NOT EXISTS`
plus idempotent `ALTER TABLE` migrations run on every connection — see `src/core/db.py`). The
full set of architecture decision records lives in `docs/Architecture/` and should be read
before making a structural change in the area it covers — do not re-derive the reasoning from
scratch.

| ADR | Covers |
|---|---|
| [ADR-001](Architecture/ADR-001-clean-architecture.md.txt) | Layering |
| [ADR-002](Architecture/ADR-002-recommendation-engine.md.txt) | Centralized recommendation engine |
| [ADR-003](Architecture/ADR-003-application-adapters.md.txt) | Application adapters |
| [ADR-004](Architecture/ADR-004-domain-model-responsibilities.md.txt) | Domain model responsibilities |
| [ADR-005](Architecture/ADR-005-development-workflow.md.txt) | Development workflow |
| [ADR-006](Architecture/ADR-006-testing-strategy.md.txt) | Testing strategy |
| [ADR-007](Architecture/ADR-007-family-child-domain.md.txt) | Family & child account domain (design only, not implemented) |

## Product modes

| Mode | Status | Notes |
|---|---|---|
| Adult financial user (self-service, isolated data) | **Implemented** | The only mode that exists today. Every registered account gets this. |
| Platform admin / super-admin (operate the app) | **Implemented but incomplete** | Backend + Overview/Users admin frontend exist (`src/api/routers/admin.py`, `frontend/src/pages/Admin*Page.tsx`); Security/Audit-log/System-health pages not built yet. |
| Guardian / household member | **Designed, not implemented** | Data model + permission matrix + consent design done — see [ADR-007](Architecture/ADR-007-family-child-domain.md.txt). Implementation is `ROADMAP.md`'s Sprint 5. |
| Child / minor learner | **Designed, not implemented** | Same ADR. Also needs a dedicated age-banded product experience (Sprint 6+), not just a permission flag. |
| Educator / content admin | **Planned, not designed** | Depends on the learning-content domain existing first (`ROADMAP.md`'s Sprint 6). |
| Support (limited-scope staff access) | **Deferred** | `PlatformRole` intentionally has no `SUPPORT` member yet — add only when a real person needs that responsibility. |

## Environments

- **Local dev**: `.venv` (backend) + `npm run dev` (frontend), talking to `data/app.db`
  directly. See the root `CLAUDE.md` for exact commands.
- **Docker**: `docker compose up --build` — nginx-fronted static frontend + uvicorn backend,
  same-origin via reverse proxy, data in a named volume. Additive to, not a replacement for,
  the `.venv` workflow.
- **Live self-hosted deployment**: currently running on the operator's LAN (not
  internet-exposed). Production-hardening (secret validation, SMTP, rate limiting) is done for
  this deployment shape specifically — see `ROADMAP.md`'s "Known limitations" for what's still
  missing before a genuinely public/commercial deployment.

## Where to look next

- **What's planned, and in what order** → [`ROADMAP.md`](../ROADMAP.md)
- **What's shipped, and when** → [`CHANGELOG.md`](CHANGELOG.md)
- **Build/test/lint commands, code style, gotchas** → root `CLAUDE.md`
- **Why a structural decision was made** → `docs/Architecture/ADR-*`
