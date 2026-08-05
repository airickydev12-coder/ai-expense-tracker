# Changelog

Dated history of major milestones, grouped by phase. This summarizes; it does not replace
`git log` — each entry names representative commits, not every commit in the phase. Newest
first.

## 2026-08-05 — Family/child domain guardian-side frontend (Sprint 5, continued)

- Scoped via `AskUserQuestion`: guardian-facing pages only this pass (household selector,
  household management, child-account creation), plus routing MINOR accounts away from the adult
  dashboard — no real child dashboard yet, that's still blocked on Sprint 6's content model.
- `frontend/src/pages/HouseholdsPage.tsx`: list/create households, "My Children" summary (`GET
  /guardian/children`). `HouseholdDetailPage.tsx`: members list, add/remove member, "Add a Child
  Account" form (username/email/password/age band/consent evidence) wired to `POST
  /households/{id}/children` via the existing `useStepUpAuth`/`runWithStepUp` wrapper, matching
  the backend's `require_recent_auth` gate on that endpoint.
- New `AdultAccountRoute` guard (mirrors the existing `AdminRoute` pattern exactly) wraps the
  entire adult route tree — dashboard, every financial page, admin, and the new household pages
  — redirecting any MINOR account to a new minimal `/minor` placeholder instead. Closes the
  frontend side of the "MINOR accounts aren't blocked yet" gap from the backend pass; the
  underlying API endpoints themselves still have no server-side `account_type` check (tracked in
  `ROADMAP.md`'s Known limitations, not solved this pass).
- `UserResponse`'s frontend type gained `account_type` (`'adult' | 'minor'`), which had been
  missing since the backend added the field in the prior pass.
- Live-verified end-to-end in a real headless browser: installed Playwright fresh into a scratch
  directory (`chromium-cli` wasn't available in this environment) and drove the full flow against
  a throwaway backend on port 8001 (the default port 8000 had a stale pre-Sprint-5 process
  squatting it — same recurring issue noted in earlier sprints) — register guardian → create
  household → create child account (no unexpected step-up prompt, confirming fresh `auth_time`
  works correctly) → child appears in both the member list and "My Children" → log out → log in
  as the child → correctly routed to `/minor` → direct URL navigation to `/dashboard` and
  `/households` as that account both redirect straight back to `/minor`. Throwaway accounts and
  household fully scrubbed from the real `data/app.db` afterward via scoped deletes.
- 166/166 frontend tests passing (up from 152), clean `tsc -b`, clean `oxlint` (only the two
  pre-existing, unrelated fast-refresh warnings on `AuthContext.tsx`/`StepUpAuthContext.tsx`).

## 2026-08-04 — Family/child domain backend foundation (Sprint 5, first ADR-007 code pass)

- First code pass against [ADR-007](Architecture/ADR-007-family-child-domain.md.txt), scoped
  backend-only: no frontend, no dashboards, no approval queue (needs Sprint 6's not-yet-designed
  `learning_progress` domain). Explicitly dev/test scaffolding — no real child's personal data
  should be entered until a lawyer reviews the consent flow (ADR-007's own legal-review gate).
- `users.account_type` (`ADULT`/`MINOR`, default `ADULT`) plus 5 new tables exactly as designed:
  `households`, `household_memberships` (composite `(household_id, user_id)` PK, no denormalized
  `owner_user_id` — ownership is derived from the one `OWNER`-role membership row),
  `guardian_child_relationships` (deliberately separate from household membership — a
  non-custodial guardian may need visibility outside their household), `consent_records`
  (append-only, mirrors `admin_audit_events`'s shape), `learning_profiles` (age-banded, never an
  exact birthdate — data minimization).
- `src/financial/households/`: household CRUD + selection (`POST/GET /households`,
  `POST /households/{id}/members`, `DELETE /households/{id}/members/{user_id}` — self-removal
  always allowed, removing someone else requires owner/guardian membership, removing the owner
  is blocked entirely, no ownership-transfer flow yet); guardian-initiated child account creation
  (`POST /households/{id}/children` — one call creates the MINOR user, household membership,
  guardian relationship, learning profile, and initial `ACCOUNT_CREATION` consent record — 5
  separate writes, not one transaction, matching this codebase's existing non-atomic-multi-write
  pattern); `GET /guardian/children`; self-initiated adult transition
  (`POST /account/request-adult-transition` — flips `account_type` and revokes every guardian
  relationship for that child in the same call, per ADR-007's age-transition policy; consent
  records are left untouched as historical record).
- `src/financial/consent/`: grant/revoke (`POST /consent/grant`, `POST /consent/revoke`) —
  self-consent for adults, guardian-for-child only with an active relationship, minors can never
  grant their own consent, per ADR-007's permission matrix.
- Child-account creation, consent actions, and adult transition are all gated by the existing
  `require_recent_auth` step-up dependency (same one MFA disable/revoke-all-sessions/admin
  role-change already use) — a judgment call, not ADR-mandated, since each creates a durable
  account or a legally-relevant record.
- Known, accepted gaps (see `ROADMAP.md`'s Known limitations): MINOR accounts aren't yet blocked
  from the ~14 existing adult financial endpoints (would need touching every one, out of this
  sprint's scope); no cross-repository-call transactions anywhere in this domain; no
  household-ownership-transfer flow; `learning_profiles.ai_coach_enabled` has no update endpoint
  yet.
- 1602/1602 backend tests passing (up from 1516), 0 pyright errors.

## 2026-08-04 — Breached-password screening (Sprint 3 item 6 — closes out Sprint 3)

- Soft warning only (registration, change-password, reset-password all still succeed either way)
  via HaveIBeenPwned's k-anonymity range API (`src/financial/users/breach_check.py`) — only a
  truncated SHA-1 hash prefix is ever sent, the plaintext password never leaves the server. Fails
  open (logs and treats as "not breached") on any network/API error, so this check can never
  block or delay a password-set action.
- Called from the API router layer, after the underlying password-set call already succeeded —
  not from `service.py`'s `register_user`/`change_password`/`reset_password`, avoiding a
  signature change across ~72 existing test call sites for no behavioral benefit.
- New `password_warning: str | None` field: additive on `RegisterResponse` (subclasses
  `UserResponse`) and a new `PasswordActionResponse` for change/reset-password (which moved from
  `204 No Content` to `200` with a body — confirmed non-breaking for the frontend, whose calls to
  those two endpoints are typed `Promise<void>` and never read the body).
- This was the last open Sprint 3 Security-work item — all 6 are now implemented.

## 2026-08-04 — Optional MFA: TOTP + recovery codes (Sprint 3 item 5)

- Self-service MFA: `POST /auth/mfa/enroll` generates and stores an unconfirmed TOTP secret
  (`pyotp.random_base32()`) plus an `otpauth://` provisioning URI; `POST /auth/mfa/confirm`
  verifies a real code before ever enabling it (`users.mfa_enabled_at`) and generates 10
  single-use recovery codes (`XXXX-XXXX` format, SHA-256 hashed for storage like refresh/reset
  tokens), returned in plaintext exactly once. `POST /auth/mfa/disable` and
  `POST /auth/mfa/recovery-codes/regenerate` round out self-service management. All four are
  gated by the `require_recent_auth` step-up dependency from item 4b — not a separate password
  field — the exact reuse the roadmap called for. Change-password stayed ungated, same
  reasoning item 4b used: its own inline current-password check is already at least as strong.
- Login gains a second step when MFA is enabled: `POST /auth/login` returns a short-lived
  (5-minute), purpose-scoped `mfa_challenge` JWT instead of real tokens; `POST /auth/mfa/verify`
  consumes it plus a TOTP or recovery code and, on success, proceeds exactly like a normal login
  (session issue, refresh cookie, new-device notification). A wrong code counts toward the same
  `login_attempts` lockout budget passwords already use, since a 6-digit TOTP space is
  practically brute-forceable without one.
- `create_access_token` gained a `purpose: "access"` claim; `get_current_user` now rejects any
  token whose purpose isn't `"access"` (defaulting a missing claim to `"access"` for backward
  compatibility) — closes a real token-confusion bug class where an intercepted `mfa_challenge`
  token, a validly-signed JWT with its own `sub` claim, could otherwise be replayed as a bearer
  token and authenticate as that user before MFA was ever completed.
- TOTP secrets are encrypted at rest (`src/core/security.py`'s new `encrypt_secret`/
  `decrypt_secret`, Fernet via the `cryptography` package) under a new `MFA_ENCRYPTION_KEY`,
  never stored plaintext — a password can be one-way hashed, but a TOTP secret must be
  reversible to verify future codes, so hashing wasn't an option. Same production fail-fast
  pattern as `JWT_SECRET_KEY`: `ENVIRONMENT=production` with the insecure default key refuses
  to start; development only warns.
- Frontend: `MfaSection.tsx` (new, in Settings) handles enroll → QR code (new `qrcode` npm
  dependency, rendered client-side from the `otpauth://` URI — no backend image generation) →
  confirm → recovery codes shown once, and disable/regenerate for an already-enabled account,
  all wrapped in `runWithStepUp`. `LoginPage.tsx` gains a second step for the code prompt when
  `login()` resolves `mfa_required` instead of `authenticated`.
- Two bugs caught by running the test suite immediately after writing it, not by any test
  written first: (1) `create_refresh_token`'s `auth_time` parameter was accidentally made
  required with no default during an earlier pass this session, breaking every fixture/test that
  didn't pass it explicitly — unrelated to MFA but surfaced again as a reminder to default
  optional-seeming parameters; (2) `QRCode.toDataURL`'s TypeScript overloads (promise vs.
  callback style) made `vi.mocked()` infer the wrong resolved type in the new component test —
  fixed with a narrow `as never` cast on the mock's resolved value, isolated to test code.
- Live-verified end-to-end over real HTTP (`curl` against a throwaway backend instance): full
  enroll → confirm → MFA-required login → verify (TOTP and recovery-code paths, including
  single-use enforcement) → step-up gating on all four management routes (stale token → 403
  `step_up_required` → `POST /auth/reauth` → retry succeeds) → the `MFA_ENCRYPTION_KEY`
  production fail-fast actually refusing to start. No visual browser check this pass — same
  tooling gap as item 4b (no `chromium-cli`/Playwright in this environment) — covered instead by
  RTL tests exercising the real enrollment/login-challenge DOM flows.

## 2026-08-04 — Security-event notifications & step-up auth (Sprint 3 item 4b)

- Security-event notification emails via the existing `send_notification_email`: new device/IP
  sign-in (compared against the caller's other active sessions, skipped on a user's first-ever
  login), refresh-token reuse detected (alongside the existing mass-revoke), password changed,
  and all sessions logged out. All four soft-fail on `ExternalServiceError`, matching the
  established pattern from registration's verification email — delivery failure never blocks
  the underlying action.
- Recent-auth ("step-up") requirement: a new `auth_time` claim on the access token (set at
  login, carried forward unchanged across `POST /auth/refresh` rotations — a refresh never
  re-verifies a password, so rotation alone can't count as recent auth) gates
  `POST /auth/sessions/revoke-all` and the admin role-change/activate-deactivate endpoints. A
  stale `auth_time` returns 403 with `code: "step_up_required"`; a new `POST /auth/reauth`
  (re-verifies the password, mints a fresh access token, updates the session's stored
  `auth_time` so the next refresh carries the fresher value forward) clears it. New
  `refresh_tokens.auth_time` column (self-healing migration, backfilled from `issued_at` for
  pre-existing rows). Change-password was deliberately left ungated — its own inline
  current-password check is already at least as strong, so a separate step-up prompt would just
  be a redundant second password entry.
- Frontend: `StepUpAuthContext`/`ReauthModal` — a `runWithStepUp(action)` wrapper that catches a
  403 `step_up_required`, opens a password-confirmation modal, and retries the original action
  once reauth succeeds; wired into "log out of all devices" and the admin role-change/
  activate-deactivate controls.
- Live-verified end-to-end over real HTTP (`curl` against a throwaway backend instance) for both
  the self-service and admin step-up paths, plus reuse detection — no visual browser check this
  pass, since neither `chromium-cli` nor a Playwright install is available in this environment;
  covered instead by `StepUpAuthContext.test.tsx`'s real-DOM RTL interactions (modal open →
  wrong password → inline error → correct password → close + retry → cancel → reject).
- A bug caught mid-implementation, not by a written test: PyJWT only auto-converts its own
  reserved `iat`/`exp`/`nbf` claims from `datetime` — a custom claim like `auth_time` was left
  as a raw `datetime` and crashed every login with `TypeError: Object of type datetime is not
  JSON serializable`. Fixed by encoding it as a Unix timestamp explicitly. A second bug: the
  `auth_time` backfill `UPDATE` on `refresh_tokens` (DML) left an implicit transaction open
  under Python's default `sqlite3` isolation, which then broke the composite-primary-key
  migration's own `BEGIN` for any test exercising a pre-existing ("old-shape") database — fixed
  by committing right after the one-time backfill.

## 2026-08-04 — Email verification & session management (Sprint 3, continued)

- Soft email verification: `POST /auth/register` now emails a verification link
  automatically (never blocks registration if SMTP fails — verification never blocks login or
  any feature); `POST /auth/verify-email` (public, token-based) consumes it;
  `POST /auth/resend-verification` (authenticated, rate-limited) sends a fresh one. New
  `users.email_verified_at` column, `email_verification_tokens`/`email_verification_requests`
  tables. Frontend: a dismissible-once-verified banner (`Layout.tsx`) with a resend button, and
  `/verify-email` page.
- Self-service session/device management: `GET /auth/sessions` (lists active sessions with
  `user_agent`/`ip_address`, flags the caller's own), `DELETE /auth/sessions/{id}` (revoke one),
  `POST /auth/sessions/revoke-all` ("log out of all devices"). New columns on `refresh_tokens`.
  Frontend: an Active Sessions section on the Settings page.
- Refresh-token reuse detection: `refresh_session()` now distinguishes "token never existed"
  from "token already used and rotated out" — presenting an already-rotated token revokes
  *every* session for that user, not just that one request, since it's a real theft signal, not
  routine staleness.
- A real bug caught mid-implementation, not by a written test: the very first full test-suite
  run after this change took 6 minutes instead of 3 and made real outbound SMTP calls through
  the project's actual configured Gmail account — the new auto-sent verification email had no
  test-suite stub, and this dev environment's `.env` has real SMTP credentials (see
  `production_hardening_and_lan_deployment` history). Fixed with an autouse `conftest.py`
  fixture stubbing `send_notification_email` by default for every test.

## 2026-08-04 — Family/child domain design (Sprint 4)

Design-only, per `ROADMAP.md`'s own scoping — no code changed. New
[ADR-007](Architecture/ADR-007-family-child-domain.md.txt): `account_type` (`ADULT`/`MINOR`)
as a `users` column; `HouseholdRole` per-membership, not per-user; 5 new tables (`households`,
`household_memberships`, `guardian_child_relationships` — deliberately separate from
membership, `consent_records` — append-only, generalized to cover adult self-consent too, and
`learning_profiles` — stores an age band, never an exact birthdate); a permission matrix; and a
fully answered, non-automatic age-transition policy. Explicitly flags that legal review is
still required before any real child account exists — the design isn't a substitute for that.
`docs/Architecture/README.md.txt`'s ADR index and `CLAUDE.md`'s ADR list both updated to
reference it (and incidentally corrected 6 other ADRs' long-stale "Planned" status to
"Accepted" while touching that table).

## 2026-08-04 — Security hardening (Sprint 3, partial)

- Refresh tokens moved from `localStorage` to an HttpOnly, `SameSite=Lax` cookie; the access
  token now lives in memory only on the frontend (never persisted) — a fresh page load
  silently re-establishes the session via the cookie (`POST /auth/refresh`, no body) instead
  of reading a stored access token. `POST /auth/login`/`/auth/refresh` no longer return a
  `refresh_token` in their JSON body at all; `/auth/logout` no longer requires a bearer token
  (the cookie itself can't be forged by JS, so that guard was no longer doing anything).
- New `ENVIRONMENT` config var: the app now refuses to start (`RuntimeError`) if
  `ENVIRONMENT=production` and `JWT_SECRET_KEY` is still the insecure placeholder, instead of
  only logging a warning. Development is unaffected (still just warns).
- New `COOKIE_SECURE` config var (default `false`) — the current self-hosted LAN deployment is
  plain HTTP, and a `Secure` cookie is silently dropped by browsers over HTTP entirely, so this
  defaults off with a startup warning rather than defaulting on and breaking login there.
- `get_current_user` now re-checks `is_active` on every request, not just at login/refresh —
  closes the gap deliberately left open when the admin console's deactivate endpoint shipped.
- Not done this pass: email verification, session/device list, MFA design, breached-password
  screening — see `ROADMAP.md`'s Security work section.

## 2026-08-04 — Roadmap reset + Admin Console MVP frontend (Sprints 1–2)

- **Sprint 1**: replaced the placeholder `ROADMAP.md` and empty `docs/PROJECT.md`/
  `docs/CHANGELOG.md` with real content, reframing the project's next phase around product
  governance (admin console, family/child domain, security hardening) rather than the
  original SQLite/FastAPI/React/AI technology sequence.
- **Sprint 2**: Admin Console MVP frontend — `/admin` Overview (stats computed client-side
  from the user list) and `/admin/users` (search, activate/deactivate, role assignment,
  revoke sessions), route-guarded and hidden from non-admin navigation. Also added the
  `role` field to the frontend's `UserResponse` type, which had been missing entirely.
  Live-verified in a real browser via Playwright against a promoted throwaway admin account.

## 2026-08-04 — Admin console, Stages 1–2 (backend)

- **Stage 2 — user operations**: `GET /admin/users`, `GET /admin/users/{id}`,
  `PATCH /admin/users/{id}/active` (activate/deactivate, revokes all refresh tokens on
  deactivation), `PATCH /admin/users/{id}/role` (super-admin only), and
  `POST /admin/users/{id}/revoke-sessions`. Every mutating action writes an
  `admin_audit_events` row. An admin cannot deactivate or role-change their own account.
- **Stage 1 — authorization foundation**: `PlatformRole` (`USER`/`ADMIN`/`SUPER_ADMIN`) added
  to the `User` model; `require_admin`/`require_super_admin` FastAPI dependencies;
  `admin_audit_events` table; `scripts/promote_platform_role.py` for the (deliberately manual)
  first promotion. (`2e3fffd`)
- Production hardening for the self-hosted LAN deployment: secrets, SMTP, and rate-limit
  configuration tightened. (`db768bb`)

## 2026-08-03 to 2026-08-04 — Authentication hardening backlog

Six stages, each a commit: login rate-limiting (`3eb0cdb`), account settings/profile editing
(`4b9446c`), authenticated change-password (`ec6b502`), forgot/reset password (`e0d031a`),
rotating refresh tokens (`139295a`), server-side logout (`fa1b7c6`).

## 2026-08-03 — Multi-user foundation

- Local JWT auth (Argon2 password hashing, access tokens) and a one-time backfill of existing
  data to a `me` account. (`ac48120`)
- Per-user data isolation: composite `(user_id, ...)` primary keys across every domain table,
  applied domain-by-domain, finishing with CLI call sites and the composition root.
  (`ee005db` … `af2d360`)
- Frontend login/register, route guarding, bearer-token wiring. (`c48a9e7`)

## 2026-08-02 to 2026-08-03 — Product features on top of the AI/React/SQLite stack

- Phase 7, five stages, same push cadence as a single day's work: AI explanation layer
  (`23fcaec`), tool-calling coach with scenario execution (`0debd57`), personal RAG via
  keyword/recency retrieval (`3e123bf`), approval-based coach actions — dismiss
  recommendation, save scenario, add goal, update budget, categorize expense (`42c3dea`,
  `765d90d`), multi-step planning with conflict detection (`e1765cd`).
- Recommendation-engine/coach convergence: unified duplicated business-rule thresholds,
  fixed a real debt-to-income scale bug (coach annualized income, the engine didn't),
  aligned net-worth and health-score severity between the two, consolidated two parallel
  snapshot builders into one. (`fcd71c1`, `e52b7c1`, `08cace8`, `4fe6a2d`, `0167ab8`)
- Dashboard/History/Forecasting/Scenarios gained charts; a Recommendations page with
  dismiss/complete/suppress; recurring expense templates; CSV export; email notifications for
  bills/budget overruns/urgent recommendations. (`117d533`, `0ab19bd`, `1a94e74`, `72b630e`,
  `7d37733`)

## 2026-08-02 — AI integration (Phase 6) + Docker

- Three AI features shipped, all calling the Claude API directly: expense category suggestion
  (`a239470`), natural-language scenario parsing via a discriminated-union JSON schema
  (`2d7f261`), and an agentic financial-coach chat using a real tool-use loop over 9
  read-only domain tools (`f3ac4b8`).
- Docker packaging for the full stack — two-stage backend image, nginx-fronted static
  frontend, same-origin reverse proxy, named volume for `data/app.db`. (`804f3c3`)

## 2026-08-01 — React frontend (Phase 5) + FastAPI completion (Phase 4)

- FastAPI routers for all 12 domains, including sub-resource lifecycles (goal ledger,
  scenario workspace) and a startup-data-loading bug fix. (`b056ed5`, `0c0073e`)
- Full React SPA (Vite + TypeScript + Tailwind) covering all 12 domains — dashboard through
  scenarios/coach — in one session. (`17cc980`)

## 2026-07-20 to 2026-08-01 — SQLite migration (Phase 3) + engineering hygiene

- All 12 domains migrated from per-domain JSON files to a shared `data/app.db` via raw
  `sqlite3`, no ORM. (`96e5c5d`, `14fb008`)
- Custom exception hierarchy, structured logging, constants extraction, `black`/`ruff`
  formatting and linting adopted repo-wide. (`abc3756`, `0269f20`)
- Decimal migration: every monetary field converted from `float`/mixed types to `Decimal`
  throughout the domain layer. (`60a3498`, `cc2a023`)

## 2026-07 and earlier — Foundations through the recommendation engine (Phases 1–2)

CLI-only, in-memory then JSON-persisted, single-domain-at-a-time build-out: expense tracking,
budgets, accounts, bills, debt, goals, income, the financial snapshot engine, the business-rule
engine (18 rules across health/debt/savings/goals/spending), and the centralized recommendation
pipeline that replaced ad hoc per-rule output. This is the largest number of individual commits
in the project's history — see `git log --oneline` for the full list if needed.

---

Going forward, add an entry here for each notable change — new domain, migration, security
fix, or architectural shift — not for every commit. Routine bug fixes and refactors belong in
commit messages, not here.
