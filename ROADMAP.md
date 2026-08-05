# Roadmap

This replaces the previous placeholder (a bare list of section headers with no content). It
reflects the actual state of the codebase as of **2026-08-04**, not the original phase plan —
the project has crossed from "build a single-user financial app" into "build a governed
multi-user product with a child-safety and content domain," which is a different scope of work
than the original SQLite → FastAPI → React → AI sequence. That original sequence is
substantially complete; this document picks up from there.

Every item below is labeled:

- **Implemented** — shipped, tested, in the codebase today.
- **Implemented but incomplete** — real, working, but a known partial slice.
- **Planned** — agreed direction, not started.
- **Deferred** — considered, deliberately not now; revisit when the stated trigger occurs.
- **Out of scope** — considered and rejected for this product, not merely postponed.

For dated history of what shipped, see [`docs/CHANGELOG.md`](docs/CHANGELOG.md). For what the
product is and how it's built, see [`docs/PROJECT.md`](docs/PROJECT.md).

## Current product state

A self-hosted, multi-user personal finance platform (CLI + FastAPI + React) with per-user data
isolation, JWT authentication, and a platform-admin authorization foundation. Three AI features
(categorization, NL scenario parsing, agentic coach chat) call the Claude API directly. Running
today on the operator's LAN, not exposed to the public internet.

| Original phase | Status |
|---|---|
| Foundations (Python, Git, CRUD, tests) | Implemented |
| Professional engineering (logging, exceptions, config, lint/format) | Implemented |
| SQLite + repositories | Implemented |
| FastAPI (all 12 domains) | Implemented |
| React frontend (all 12 domains) | Implemented |
| AI integration (categorization, NL parsing, agentic coach) | Implemented, evolving |
| Authentication (JWT, Argon2, rotating refresh tokens, rate limiting) | Implemented |
| Per-user data isolation | Implemented |
| Admin authorization foundation + user-ops backend | Implemented |
| Admin console frontend | Implemented but incomplete (Overview + Users done, Security/Audit/System-health not started) |
| Adult/child learning model | Backend implemented (Sprint 5, dev/test scaffolding only), no dashboards/frontend yet |
| Production operations (backups, observability, staging) | Partial |
| Commercial SaaS readiness | Not implemented |

## Current sprint

Sprint 5 (Family/child foundation, the first *implementation* sprint against ADR-007) has now
shipped both backend and its guardian-side frontend — see Adult/child learning model below.
Sprint 3 is fully complete (item 6, breached-password screening — see Security work, item 6).

## Next sprint

Unsequenced — candidates are the child-facing frontend (a real learning dashboard, not the
current bare `/minor` placeholder — blocked on Sprint 6's content model to have anything to
show) and Sprint 6 itself (educational-content system). Ask before picking one; neither has been
scoped in detail yet.

## Completed sprints

- **Sprint 1 — Roadmap and documentation reset.** This file, `docs/PROJECT.md`,
  `docs/CHANGELOG.md`.
- **Sprint 2 — Admin Console MVP.** `/admin` (Overview) and `/admin/users` (search,
  activate/deactivate, role assignment, revoke sessions), route-guarded and hidden from
  non-admins, wired to the Stage 2 backend endpoints. Live-verified in a real browser.
  Security/Audit-log/System-health pages were deliberately left for later — they weren't part
  of this sprint's scope.
- **Sprint 3 (partial) — Security hardening.** Refresh token moved from `localStorage` to an
  HttpOnly/SameSite=Lax cookie (access token now in memory only, never persisted); production
  fail-fast on an insecure `JWT_SECRET_KEY` when `ENVIRONMENT=production`; `get_current_user`
  now re-checks `is_active` per request (the item explicitly deferred when Stage 2 of the
  admin console shipped). Live-verified in a real browser, including the cross-origin cookie
  flow and a hard-reload session-persistence check.
- **Sprint 4 — Family/child domain design.** Design-only, as scoped — see
  [ADR-007](docs/Architecture/ADR-007-family-child-domain.md.txt): `account_type` as a `users`
  column, `HouseholdRole` per-membership, 5 new tables (`households`, `household_memberships`,
  `guardian_child_relationships`, `consent_records`, `learning_profiles`), a permission matrix,
  and a fully answered (not just listed) age-transition policy. Explicitly **not**
  legally reviewed and **not** implemented — Sprint 5 is where code first appears. Educational-
  content tables (`learning_progress`, etc.) were deliberately left for Sprint 6's own design
  pass rather than guessed at here.
- **Sprint 3, continued — Email verification & session management.** Soft email verification
  (registration/resend sends a link, `POST /auth/verify-email` consumes it, never blocks login
  or feature access); self-service active-sessions list with per-session revoke and "log out
  of all devices" (`GET/DELETE /auth/sessions`, `POST /auth/sessions/revoke-all`); refresh-
  token reuse detection (presenting an already-rotated token now revokes every session for
  that user, not just rejects the one request); `user_agent`/`ip_address` captured per session.
  Live-verified in a real browser across two simulated devices. Deliberately **not** done this
  pass: MFA design, security-event notifications, recent-auth ("step-up") requirements,
  breached-password screening — see Security work below.
- **Sprint 3 item 4b — Security-event notifications & step-up auth.** Email alerts (new device/
  IP sign-in, refresh-token reuse detected, password changed, all sessions logged out) via the
  existing `send_notification_email`; a recent-auth (`auth_time`) claim on the access token,
  refreshed only by `POST /auth/reauth`, gating self-service revoke-all-sessions and admin role-
  change/activate-deactivate behind a 403 `step_up_required` → password-confirmation-modal →
  retry flow. Live-verified over real HTTP (`curl`) end-to-end for both the self-service and
  admin paths, plus reuse detection; no visual browser check this pass (no Playwright/
  chromium-cli available in this environment — covered instead by `StepUpAuthContext.test.tsx`'s
  real-DOM RTL interactions). See Security work below, item 4b.
- **Sprint 3 item 5 — Optional MFA (TOTP + recovery codes).** Self-service enroll (`POST
  /auth/mfa/enroll`/`confirm`) via any TOTP authenticator app, 10 single-use recovery codes
  shown once at confirmation, self-service disable/regenerate — all four gated by the existing
  step-up (`require_recent_auth`) dependency from item 4b, exactly the reuse the roadmap
  anticipated. Login gains a second step (`POST /auth/mfa/verify`) when enabled, via a
  short-lived, purpose-scoped challenge token distinct from a real access token. TOTP secrets
  are encrypted at rest (new `MFA_ENCRYPTION_KEY`, Fernet) rather than stored plaintext. Opt-in
  for every user; enforcement for admins deliberately deferred (needs its own grace-period/
  forced-enrollment UX). Live-verified over real HTTP (`curl`) end-to-end, including step-up
  gating and the production fail-fast on an unset `MFA_ENCRYPTION_KEY`; no visual browser check
  this pass, same tooling gap as item 4b.
- **Sprint 3 item 6 — Breached-password screening.** Soft warning (never blocks) at registration,
  change-password, and reset-password, checked via HaveIBeenPwned's k-anonymity range API (only a
  truncated SHA-1 hash prefix ever leaves the server). Fails open on any network/API error —
  never delays or blocks a password-set action. **This closes out Sprint 3 entirely** — all 6
  Security-work items are now implemented.
- **Sprint 5 — Family/child domain backend foundation.** The first code pass against
  [ADR-007](docs/Architecture/ADR-007-family-child-domain.md.txt), explicitly scoped as
  backend-only, dev/test scaffolding (no real child's personal data — the ADR's legal-review gate
  still stands). `account_type` (`ADULT`/`MINOR`) on `users`; 5 new tables (`households`,
  `household_memberships`, `guardian_child_relationships`, `consent_records`,
  `learning_profiles`); household CRUD + selection (`POST/GET /households`,
  `POST /households/{id}/members`, `DELETE /households/{id}/members/{user_id}`);
  guardian-initiated child account creation (`POST /households/{id}/children` — one call creates
  the MINOR account, household membership, guardian relationship, learning profile, and initial
  consent record); `GET /guardian/children`; consent grant/revoke (`POST /consent/grant`,
  `POST /consent/revoke`); self-initiated adult transition (`POST
  /account/request-adult-transition` — flips `account_type` and revokes every guardian
  relationship atomically-in-intent). Child-account-creation, consent actions, and adult
  transition are all step-up (`require_recent_auth`) gated. Deliberately deferred: household
  selector UI, guardian/child dashboard shells, the approval queue (needs Sprint 6's
  not-yet-designed `learning_progress` domain). See Adult/child learning model below and Known
  limitations for what's intentionally left open.
- **Sprint 5, continued — Guardian-side frontend.** Scoped via `AskUserQuestion`: guardian-facing
  pages only this pass (household selector, household management, child-account creation) plus a
  minimal `/minor` landing stub so `account_type`-based routing has somewhere to send a MINOR
  account — not a real child dashboard (that's still blocked on Sprint 6). New `HouseholdsPage`
  (list/create households, linked-children summary) and `HouseholdDetailPage` (members list,
  add/remove member, "Add a Child Account" form) under a new `/households` nav item; a new
  `AdultAccountRoute` guard (mirrors the existing `AdminRoute` pattern) redirects any MINOR
  account away from the entire adult route tree — dashboard, every financial page, admin, and the
  new household pages — to `/minor`, closing the frontend side of the "MINOR accounts aren't
  blocked yet" gap from the backend pass (the backend API endpoints themselves still aren't
  locked down — that part of the gap remains, tracked in Known limitations). Child-account
  creation reuses the existing `useStepUpAuth`/`runWithStepUp` wrapper, matching the backend's
  `require_recent_auth` gate on that endpoint. Live-verified end-to-end in a real headless
  browser (Playwright, installed fresh into a scratch directory — `chromium-cli` wasn't available
  in this environment, unlike some earlier sprints): register guardian → create household →
  create child account (no unexpected step-up prompt, since `auth_time` was fresh from the just-
  completed login) → child appears under both the household's member list and "My Children" →
  log out → log in as the child → correctly routed to `/minor`, not the dashboard → direct URL
  navigation to `/dashboard` or `/households` as that same minor account both redirect straight
  back to `/minor`. One benign console 401 observed (the existing, pre-existing silent-refresh-
  attempt-on-mount pattern firing before any session exists — not a regression). Throwaway
  accounts/household fully scrubbed from the real `data/app.db` afterward via scoped deletes.

## Completed capabilities

- Full CRUD across 12 financial domains (expenses, budgets, accounts, bills, debt, income,
  goals, history, forecasting, scenarios, recommendations, coach), backend + frontend.
- Business-rule/recommendation engine (18 rules) with a centralized pipeline — see
  [ADR-002](docs/Architecture/ADR-002-recommendation-engine.md.txt).
- Three AI features on the Claude API: expense categorization, NL scenario parsing, agentic
  coach chat (tool-use loop over 9 read-only domain tools), plus an AI explanation layer
  (narrative snapshots, recommendation explanations, monthly reviews) and a pragmatic
  keyword/recency personal-RAG layer.
- Authentication: registration, login, Argon2 password hashing, in-memory JWT access tokens,
  rotating HttpOnly-cookie refresh tokens (with reuse detection), forgot/reset password,
  soft email verification, login-attempt throttling, server-side logout, self-service active-
  sessions list + per-session revoke + log-out-all-devices, production fail-fast on an insecure
  JWT secret, per-request `is_active` enforcement.
- Per-user data isolation: every domain table keyed by `(user_id, ...)`.
- Platform-role authorization: `USER`/`ADMIN`/`SUPER_ADMIN`, enforced via FastAPI
  dependencies, backed by an append-only audit log (`admin_audit_events`).
- Admin user-operations backend: list/get/activate/deactivate/assign-role/revoke-sessions,
  every mutation audited.
- Admin Console MVP frontend: route-guarded `/admin` Overview (client-computed stats) and
  `/admin/users` (search, activate/deactivate, role assignment, revoke sessions), hidden from
  non-admin navigation.
- Docker packaging for the full stack (backend + frontend + SQLite volume).
- Recurring expense templates, CSV export, email notifications (bills due, budget overruns,
  urgent recommendations), dashboard/history/forecasting/scenario charts.
- Production hardening for the current (self-hosted LAN) deployment shape: secrets, SMTP,
  rate limits.

## Known limitations

Real gaps in what's shipped, not aspirational — flag these if they become relevant to a task:

- **`COOKIE_SECURE` defaults to `false`.** The refresh-token cookie is sent over plain HTTP on
  the current LAN deployment — a real, deliberate tradeoff (see Security work item 1) until
  that deployment has TLS in front of it, not an oversight. Flip the one env var once it does.
- **`JWT_SECRET_KEY` still only warns, never fails, in development.** Production
  (`ENVIRONMENT=production`) now fails fast on the insecure default; development intentionally
  still just logs a warning, so local dev never breaks over this.
- **No formal migration framework.** Schema changes are idempotent `ALTER TABLE`/`CREATE TABLE
  IF NOT EXISTS` statements run on every connection (`src/core/db.py`) — this has worked
  cleanly so far (role column, composite PKs, admin audit table) but doesn't scale indefinitely
  as more tables accumulate.
- **The `/admin/overview` API endpoint is still a stub** (message + admin identity only, no
  real server-aggregated metrics) — the Overview page works around this by computing its stats
  client-side from `GET /admin/users` instead of waiting on a real backend endpoint.
- **No admin Security, Audit Log, or System Health pages yet** — only Overview and Users exist.
  `admin_audit_events` already has the data an Audit Log page needs; it just has no viewer.
- **Notification configuration is global**, not per-user (no per-user channel/quiet-hours/
  digest preferences yet).
- **Sprint 3's Security work is fully shipped** — email verification, session/device list,
  security-event notifications, recent-auth "step-up", MFA, and breached-password screening are
  all implemented; no items remain open in that list.
- **MINOR accounts aren't blocked from ordinary adult financial *API endpoints* yet, though the
  frontend now routes them away.** The Sprint 5 frontend's `AdultAccountRoute` guard redirects any
  MINOR account to `/minor` before it can reach the dashboard/financial pages in the browser, but
  the underlying API endpoints themselves have no `account_type` check — a MINOR account's access
  token could still call them directly (e.g. via `curl`). Enforcing that server-side would mean
  touching every one of the ~14 existing financial routers — out of scope for both the backend and
  frontend passes so far. Not a real risk yet since no real child accounts exist (dev/test
  scaffolding only).
- **Sprint 5's multi-table writes aren't transactional.** Guardian-initiated child account
  creation (5 writes across 3 tables) and adult transition (2 writes) each commit independently,
  matching this codebase's existing pattern (`register_user()` isn't atomic with its
  verification-email send either) — a failure partway through leaves partial state. Not fixed
  this pass; would need new cross-repository-call transaction machinery.
- **No household-ownership-transfer flow.** A household's `OWNER` can never leave or be removed
  in Sprint 5 — deliberately deferred, not designed yet.
- **`learning_profiles.ai_coach_enabled`** (the guardian's AI-coach kill switch) is set once at
  child-account-creation time with no update endpoint yet — nothing in Sprint 5's scope calls it.
- **Family/child domain data still requires legal review before real use** — see Adult/child
  learning model below. Sprint 5 is dev/test scaffolding only; no real child's personal data
  should be entered until a lawyer reviews the consent flow, evidence-capture mechanism, and
  overall data-handling practice.
- **MFA is opt-in for everyone, not required for admins/guardians yet** — the roadmap's original
  "strongly encouraged/required for admins" framing needs its own grace-period/forced-enrollment
  UX and product decision, deliberately deferred from this pass.
- **Email verification is soft only** — it never blocks login, registration, or any feature.
  There's no path today to require it before, say, using the AI coach or exporting data; that
  would be a deliberate future product decision, not an oversight to silently fix.
- **No i18n/accessibility work done yet** — hardcoded `$`/US date formats, no accessibility
  audit.
- **SQLite with no automated backup/restore process** — fine for a single self-hosted
  instance, not for anything with real users depending on uptime.
- **Legacy `data/*.json` files remain in the repo** as dormant migration-era backups (see
  `scripts/migrate_json_to_sqlite.py`) — confirmed nothing in `src/` reads or writes them, but
  they haven't been formally retired (moved to an archive path, documented as historical-only,
  or deleted).

## Technical debt

- `RecommendationCategory` and `CoachingCategory` still partially overlap (share
  `CASH_FLOW`/`DEBT`/`SAVINGS`/`INCOME`, diverge on the rest) — deliberately not merged; a
  full merge was scoped once and declined because `CoachingAdvice` generation still doesn't
  consume engine-produced `Recommendation` objects the way ADR-002 says it should, and
  unifying the taxonomy first would paper over that instead of fixing it.
- `Recommendation.key` is derived from `RecommendationCategory`'s member *name* and persisted
  in `recommendation_history` — renaming/merging members needs a deliberate migration script,
  not a casual refactor. (Documented in `CLAUDE.md`; repeating here because it's the kind of
  thing a roadmap item can accidentally trigger.)
- `requirements.txt` is UTF-16-encoded (a quirk of how it was originally generated) — every
  future dependency change needs to preserve that encoding, not corrupt it.

## Security work

Ordered roughly by risk, not necessarily by implementation order:

1. **Cookie-based refresh tokens** (HttpOnly, SameSite=Lax) replacing `localStorage`; the
   access token now lives in memory only (never persisted — a fresh page load silently
   re-establishes the session via the cookie instead of reading a stored access token).
   **Implemented** (Sprint 3). CSRF protection is the cookie's `SameSite=Lax` attribute alone,
   deliberately without a separate double-submit token — sufficient here because the *access*
   token (used for every state-changing request) is never a cookie, only ever an explicit
   `Authorization` header the browser won't attach automatically cross-site; the refresh
   cookie's only reachable targets (`/auth/refresh`, `/auth/logout`) don't expose anything
   useful to an attacker who can't read the (CORS-blocked) response anyway. `Secure` is
   configurable (`COOKIE_SECURE`, default `false`) — see Known limitations.
2. **Fail-fast on an insecure `JWT_SECRET_KEY` in production** instead of only logging a
   warning. **Implemented** (Sprint 3) — gated on a new `ENVIRONMENT` var (default
   `development`, where it still just warns); the current LAN deployment's `.env` needs
   `ENVIRONMENT=production` added explicitly to opt in (not set automatically by this change).
3. **Re-check `is_active` in `get_current_user`.** **Implemented** (Sprint 3) — closes the
   window Stage 2 of the admin console deliberately left open ("we will fix the deactivated
   user's access token later").
4. Email verification (soft — never blocks login/features), self-service session/device list
   with per-session revoke and "log out all devices," refresh-token reuse detection (presenting
   an already-rotated token revokes every session for that user, not just that one request),
   `user_agent`/`ip_address` captured per session. **Implemented** (Sprint 3, continued).
   Security-event notifications and a recent-auth ("step-up") requirement for sensitive actions
   were scoped as part of this item but **not** built — see item 4b below.
4b. Security-event notifications (new device/IP sign-in, refresh-token reuse detected, password
    changed, all sessions logged out — email via the existing `send_notification_email`) and a
    recent-auth/step-up requirement before sensitive actions (self-service revoke-all-sessions,
    admin role changes, admin activate/deactivate). **Implemented** (Sprint 3, continued).
    Step-up is an `auth_time` claim embedded in the access token at login, carried forward
    unchanged across refreshes (a refresh never re-verifies a password, so rotation alone
    doesn't count as recent auth), and refreshed only by a new `POST /auth/reauth` endpoint;
    a 403 with `code: "step_up_required"` from any gated endpoint triggers a password-
    confirmation modal (`StepUpAuthContext`/`ReauthModal`) that retries the original action once
    reauth succeeds. Change-password was deliberately **not** gated by the same check — it
    already re-verifies the current password inline, so a separate step-up prompt would just be
    a second back-to-back password entry with no added security value.
5. Optional MFA (TOTP + 10 single-use recovery codes). **Implemented.** Self-service enroll/
   confirm/disable/regenerate, all gated by the `auth_time`/step-up primitive from item 4b (the
   reuse the roadmap called for) rather than a separate password field — except change-password,
   deliberately excluded for the same "already re-verifies inline" reason item 4b excluded it.
   Login gains a `POST /auth/mfa/verify` second step via a short-lived, purpose-scoped challenge
   token (`purpose: "mfa_challenge"`, distinct from a real access token's `purpose: "access"` —
   `get_current_user` rejects anything else, closing off a token-confusion replay). TOTP secrets
   are Fernet-encrypted at rest (`MFA_ENCRYPTION_KEY`, same production fail-fast pattern as
   `JWT_SECRET_KEY`), not stored plaintext. **Not** yet required for admins/guardians — opt-in
   for everyone this pass, see Known limitations.
6. Breached-password screening. **Implemented.** Soft warning only (registration, change-password,
   reset-password all still succeed either way) via HaveIBeenPwned's k-anonymity API — only a
   truncated SHA-1 hash prefix is ever sent, and any API/network failure fails open silently.
   **This was the last open Security-work item — the list above is now fully shipped.**

## Admin console

Backend (Stages 1–2) and the Sprint 2 MVP frontend (Overview + Users) are done — see Completed
capabilities. Remaining:

- Admin shell: extend to `/admin/security`, `/admin/system`, `/admin/audit` (Overview/Users
  already exist, route-guarded and hidden from non-admins).
- Overview: today's stats are computed client-side from `GET /admin/users` (total/active/
  inactive/admin counts, new-in-7d/30d) plus the existing stub's identity fields. Still
  missing: failed-login counts, active-session counts, notification/AI/DB status, app version,
  security warnings — these need either new backend endpoints or a real `/admin/overview`
  aggregation.
- Users: search (client-side, done), activate/deactivate (done), revoke sessions (done), assign
  role (done). Still missing: filter, pagination (no backend support to build against yet — see
  Known limitations), a per-user detail view, last-login, security-event history.
- Security: failed logins, password-reset activity, active/revoked sessions, rate-limited
  accounts, JWT configuration warnings. **Not started.**
- Audit Log: actor/action/target/timestamp/reason/metadata, filterable, paginated — the data
  already exists in `admin_audit_events`, this is purely a viewer. **Not started.**
- System Health: DB connectivity, schema/migration state, AI/SMTP config status, scheduler
  state, app version/environment, background-job status. **Not started.**

**Definition of done** for the MVP: backend authorization enforced (true) + admin frontend
genuinely hidden and route-guarded for non-admins (true) + every backend admin endpoint
independently protected (true) + destructive actions require confirmation (true — deactivate
and revoke-sessions both prompt) + role changes require `SUPER_ADMIN` (true, enforced both
backend and by hiding the control client-side for non-super-admins) + every state-changing
action creates an audit record (true) + no private financial data shown by default (true —
Users/Overview show account metadata only, never financial data).

## Adult/child learning model

**Status: backend + guardian-side frontend implemented (Sprint 5), dev/test scaffolding only —
no real child dashboard yet.** The design pass (Sprint 4) produced
[ADR-007](docs/Architecture/ADR-007-family-child-domain.md.txt); Sprint 5 implemented it —
household CRUD + selection, guardian-initiated child account creation, consent grant/revoke, and
self-initiated adult transition are all real, tested API endpoints
(`src/financial/households/`, `src/financial/consent/`), now with a real, tested, live-verified
guardian-facing UI in front of them (`frontend/src/pages/HouseholdsPage.tsx`,
`HouseholdDetailPage.tsx`). Do not begin further coding against assumptions from this section —
read the ADR itself for the data model/permission matrix/age-transition policy, this is a
summary, not the source of truth.

**Shipped in Sprint 5 (backend)**: `POST/GET /households`, `GET /households/{id}`,
`POST /households/{id}/members`, `DELETE /households/{id}/members/{user_id}`,
`POST /households/{id}/children` (guardian-initiated MINOR account creation), `GET
/guardian/children`, `POST /consent/grant`, `POST /consent/revoke`,
`POST /account/request-adult-transition`.

**Shipped in Sprint 5 (guardian-side frontend)**: a `/households` page (list/create households,
"My Children" summary), a household detail page (members, add/remove, "Add a Child Account"
form), and `account_type`-based routing (`AdultAccountRoute`) that sends any MINOR account to a
minimal `/minor` placeholder instead of the adult dashboard. **Not** shipped: a real child
dashboard/learning content (blocked on Sprint 6), the approval queue, or `account_type`-based
gating of the adult financial *API endpoints themselves* (the frontend now keeps a MINOR account
from reaching those pages in the browser, but the endpoints have no server-side check yet — see
Known limitations).

**Confirmed and now designed:**
- `PlatformRole` (`USER`/`ADMIN`/`SUPER_ADMIN`) stays exactly what it is — *platform operator
  authority*. `CHILD`/`GUARDIAN` were not added to it, per plan.
- `AccountType` (`ADULT`/`MINOR`) is a `users` column; `HouseholdRole`
  (`OWNER`/`GUARDIAN`/`ADULT_MEMBER`/`CHILD_LEARNER`) is per-membership on
  `household_memberships`, not per-user — supports a child having multiple guardians and an
  adult belonging to more than one household, as required. 5 new tables total: `households`,
  `household_memberships`, `guardian_child_relationships` (deliberately separate from
  membership — see ADR-007), `consent_records`, `learning_profiles`.
- Consent is an append-only auditable record (`consent_records`, mirroring the existing
  `admin_audit_events` pattern), not a boolean checkbox — generalized beyond
  guardian-consents-for-minor to also cover adult self-consent (needed for age transition).
- Age transition now has a fully designed, non-automatic policy (see ADR-007's Age Transition
  section) — explicitly non-automatic because the account only ever stores an age band, never
  an exact birthdate, so there's no reliable signal to auto-trigger it.
- **Still requires legal review before any public launch** that includes real child
  accounts — the design accounts for COPPA-shaped requirements (data minimization, evidence-
  backed consent) but does not itself constitute legal clearance.

**Planned child-specific product surface** (still needed — the current `/minor` page is a bare
placeholder, not this): age-appropriate dashboard, simulated budgets/allowance tracking,
needs-vs-wants exercises, savings goals, challenges/achievements, financial-literacy lessons,
guardian approvals, a restricted-policy AI coach (`learning_profiles.ai_coach_enabled` is the
guardian toggle; the actual policy design is the separate AI governance item below), no access to
adult financial data or unrestricted account-linking.

**Guardian surface**: linked-child overview **(shipped, Sprint 5 — "My Children" on
`/households`)**. Still planned: learning progress, goal approvals, allowance controls, challenge
assignments, AI safety settings (consent management itself — grant/revoke — is shipped
API-side, `POST /consent/grant`/`revoke`, but has no dedicated frontend view yet beyond the
one-time grant at child-account creation).

## Educational content system

**Status: planned**, and blocked on the household/child model above (content needs an
audience — age band, learner profile — before it means anything). Domain: `courses`,
`lessons`, `lesson_versions`, `quizzes`, `quiz_attempts`, `learning_paths`, `assignments`,
`challenges`, `achievements`, `progress_records`. Content should be age-banded (6–9, 10–13,
14–17, adult) and stored as versioned content records, not hardcoded into React components.

## AI governance (adult vs. child policy)

**Status: planned**, blocked on the child model existing. Today's AI features have one policy
profile (the adult one). Once child accounts exist, they need a distinct, more restricted
profile: age-appropriate explanations, no personalized credit advice, no encouragement to hide
activity from guardians, no third-party contact, no consequential writes, no disclosure of
adult household data, guardian-controlled conversation retention, and a clear escalation path
if a child's messages describe harm or exploitation. Broader AI-architecture additions that
benefit both profiles either way: policy-profile-by-account-type, a tool allowlist by role,
prompt versioning, response provenance, token/cost telemetry, content-safety checks, and an
evaluation dataset per policy profile.

## Role-based product experiences

**Status: planned**, depends on the child/household model. Once more than one account type
exists, authorization should shape the *experience*, not just hide endpoints — a role-aware
navigation/routing system (grouped by capability, not one flat link list) rather than the
current single static nav. The current `Layout.tsx` nav (14 flat links) has room for the
already-planned Admin section but would not scale to also adding household/children/
lessons/guardian workflows without a shell redesign — flagged here as a prerequisite, not
undertaken speculatively ahead of the features that would need it.

## Data lifecycle, backups, and operations

**Status: planned**, no work started:

- Export personal data, delete account (+ guardian-initiated deletion once children exist),
  retention periods, soft vs. permanent deletion.
- Automated, *tested* backups (a backup that's never been restored in a test isn't a verified
  backup), corruption detection, documented recovery procedure.
- Observability: structured logs with correlation IDs, error reporting, AI request
  latency/cost tracking, notification delivery metrics, health checks — while continuing to
  never log financial payloads, passwords, or raw tokens.
- Environment separation (dev/test/staging/production) with separate databases, secrets, AI
  credentials, and explicit CORS origins per environment; no dev-default secrets ever reaching
  production.

## Deployment roadmap

Current: `.venv`/`npm run dev` for local work, Docker Compose for a self-hosted LAN
deployment. **Planned**: a staging environment, deployment automation, a documented rollback
process, and the production-secret fail-fast behavior noted under Security work — all
prerequisites for treating this as more than a personal/LAN deployment.

## Commercialization readiness

**Status: not started, and explicitly not implied by anything above.** Multi-tenancy, SaaS
billing, support-access governance (temporary, audited, user-granted access for staff — not
default admin visibility into anyone's data or AI conversations), a `SUPPORT`/`CONTENT_ADMIN`
role split (deferred until a real person needs that responsibility — mirrors why `SUPPORT`
isn't in `PlatformRole` yet), and privacy/legal documentation all sit here. Nothing in the
current roadmap assumes this is happening soon; listed for completeness so it isn't
rediscovered later as a surprise.

## Explicitly out of scope (for now)

- Adding `CHILD`/`GUARDIAN`/`SUPPORT` members to `PlatformRole` — platform authority and
  product-domain relationships are deliberately different axes (see Adult/child learning
  model above).
- Any household/child feature work ahead of the dedicated design pass for that domain.
- Public/commercial launch on the current security posture (MFA opt-in but not required, no TLS
  on the LAN deployment yet) — see Security work for what has to land first.

## Execution order

1. **Sprint 1 — Roadmap & docs reset** — done.
2. **Sprint 2 — Admin Console MVP** — done (Overview + Users; Security/Audit/System-health
   pages still open).
3. **Sprint 3 — Security hardening** — mostly done: cookie-based refresh tokens, prod secret
   fail-fast validation, the `is_active` re-check, email verification, session/device
   management, item 4b's security-event notifications + step-up auth, and item 5's MFA all
   shipped. Still open: breached-password screening (low priority).
4. **Sprint 4 — Family/child domain design** — done. See
   [ADR-007](docs/Architecture/ADR-007-family-child-domain.md.txt).
5. **Sprint 5 — Family/child foundation** *(next candidate, alongside Sprint 3's remaining
   items)*:
   implement ADR-007's migrations, guardian/child accounts, household selection, guardian +
   child dashboard shells, approval queue.
6. **Sprint 6 — Financial-literacy learning system**: lessons, quizzes, challenges,
   achievements, age-banded content.
7. **Sprint 7 — Child-safe AI**: restricted policy profile, guardian controls, safety
   evaluation suite.
8. **Sprint 8 — Persistence & operations**: formal migration framework, JSON retirement,
   backup/restore, notification preferences, observability.
9. **Sprint 9 — Product design & accessibility**: app-shell redesign, design system,
   accessibility audit, localization foundation.
10. **Sprint 10 — Production readiness**: staging, deployment automation, security review,
    privacy documentation, load/concurrency testing.

Sprints 4+ are sequenced, not scheduled — each starts only once the prior one is actually done
and re-confirmed with the user, the same way Sprint 1's scope was confirmed before writing this
document.
