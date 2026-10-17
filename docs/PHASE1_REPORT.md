# Phase 1 - Completion Report

**Overall status:** Complete. Every acceptance criterion in `docs/MVP_SPEC.md` section 14 was implemented and verified, with the limitations listed in section G.

## A. Repository audit

The repository was empty (no files, no history), so the structure from the Phase 1 brief was created from scratch. There was no existing work to preserve or reconcile.

## B. Implementation summary

**Configuration.** `backend/app/core/config.py` is the single typed settings module (Pydantic Settings). It validates ports, environment names, log levels, CORS origins (scheme and host only, wildcards rejected) and SQLAlchemy URLs. Failures are converted into a readable `ConfigurationError` naming each variable. Relative SQLite paths resolve from the repository root, derived from the module location, never from a machine-specific path.

**Database.** `backend/app/database.py` holds engine creation, the session factory, table initialisation, a connectivity check and a schema check, all separate functions. Engine and session factory are created once per app in the FastAPI lifespan and stored on `app.state`. Handlers receive sessions only through the `get_session` dependency, which always closes them. SQLite foreign keys are enabled. In-memory SQLite shares one connection so it behaves correctly. Table creation uses `create_all`, documented as a development-stage choice. No rows are ever inserted.

**Models.** `Event` covers every Phase 0 field with nullable columns, UUID primary keys, and created and updated timestamps. `SourceReference` records provenance (type, optional URL unique per event, retrieval timestamp, content hash, JSON metadata) and cascades on event deletion. Datetimes use a custom UTC type that rejects naive values. Enumerated columns carry database check constraints.

**Schemas.** Pydantic schemas are separate from ORM models. `EventCreate` and `SourceReferenceCreate` define validated input (http and https only, no embedded credentials, timezone-aware dates, end not before start, URL required unless the source is manual text). They are not exposed by any route. `EventRead` and `SourceReferenceRead` serve output.

**API.** `GET /api/v1/health` performs a real connection check and schema check. It returns 200 for healthy and 503 with the same body for degraded or unhealthy, with no paths, credentials or traces. `GET /api/v1/events` is a read-only listing so the interface's empty state reflects the real database. A global handler returns a generic 500 body and logs details server-side only. CORS origins come from settings and only `GET` is permitted.

**Frontend.** React, Vite, TypeScript (strict, with `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`) and Tailwind v4. One HTTP client (`services/apiClient.ts`) handles base URL, timeout, cancellation and error classification. Responses are validated at runtime rather than trusted by type assertion. A single `useRemoteResource` hook provides loading, success, error and retry. The interface shows backend status in the header, a thin rule that follows the real connection state, a service status panel, and an event workspace that shows an empty state only when the API reports zero events. A missing `VITE_API_BASE_URL` is reported in the interface instead of producing a blank page.

## C. Testing results

All commands were run from a final `python scripts/verify.py`.

| Check | Result |
| --- | --- |
| Backend `ruff check` | Passed |
| Backend `ruff format --check` | Passed |
| Backend `mypy` (strict, 18 files) | Passed, no issues |
| Backend `compileall` | Passed |
| Backend `pytest` | 75 passed, 0 failed, 0 skipped |
| Frontend `tsc --noEmit` (strict) | Passed |
| Frontend `eslint` | Passed |
| Frontend `vitest` | 29 passed in 4 files, 0 failed |
| Frontend `npm run build` | Passed (CSS 12 kB, JS 231 kB, 72 kB gzipped) |
| Live integration (`scripts/integration_test.py`) | 11 checks passed (including 3 live frontend tests) |

The one pytest warning is a Starlette deprecation notice about its test client using `httpx`. It does not affect behaviour.

Backend tests cover: app initialisation and routes; OpenAPI contract; lifespan; CORS allow and deny; generic 500 responses with no leakage; healthy structure; the health endpoint actually calling the database check; an unreachable database returning 503; response leakage; missing tables reported as degraded and recovery; startup directory and table creation; no seeded rows; idempotent initialisation; foreign keys; invalid configuration (nine parametrised cases); path resolution; model round trips, timezone handling, naive-datetime rejection, constraints, cascades and uniqueness; schema validation including unsafe URLs; events listing and pagination; absence of write methods.

Frontend tests cover: rendering and tagline; loading state; successful health; a 503 never shown as connected; unreachable backend; retry and recovery; empty state with no fictional content; event listing only from API data; independent events retry; missing configuration; malformed payload rejection; timeout, HTTP error, non-JSON and cancellation handling.

## D. Integration verification

`scripts/integration_test.py` starts the real backend on a free port with a throwaway database and observed:

- Health returned 200 `healthy`, with the version taken from configuration and the database component `ok`.
- The configured SQLite file and its directory were created, and the event table was empty.
- CORS returned the allow header for the configured origin and none for another origin.
- The real React app, run with no network stubbing, rendered "Backend connected", the backend's actual version, and the empty workspace.
- The same app pointed at a dead port rendered "Cannot connect to backend", and the retry control remained functional.
- Restarting the backend with an unusable database produced 503 `unhealthy`, with no filesystem paths and no stack trace in the response.

Separately, the dev workflow was checked manually: `python -m app` served health, the Vite dev server served the page, and the dev proxy forwarded `/api/v1/health` to the backend with status 200. Invalid configuration made `python -m app` exit with code 2 and a message naming `BACKEND_PORT` and `CORS_ORIGINS`.

## E. Hardcoding and mock-data audit

Checked by search and by tests:

- Host, port, database URL and CORS origin defaults appear only in `backend/app/core/config.py`. The frontend reads its base URL only through `frontend/src/config.ts`. No other source file contains a host or port.
- `os.environ` and `getenv` are not used outside the settings module.
- No seed, fixture, mock or sample-event code exists in application sources. Synthetic rows exist only in test files and live in per-test temporary databases. A guard fixture fails the run if a test touches `data/eventsignal.db`.
- No secrets, API keys or tokens are present. `.env.example` contains only harmless development values.
- No machine-specific paths and no emoji appear in any project file.
- The production bundle contains no host or port, only React's internal XML namespace string.
- Frontend status derives entirely from live API responses. A 503 is shown as a problem, never as connected.

## F. Deliverables

- `backend/`: application, 75 tests, pinned `requirements.txt` and `requirements-dev.txt`, `pytest.ini`, `pyproject.toml`.
- `frontend/`: application, 29 component tests, live integration test, `package.json`, `package-lock.json`, strict `tsconfig.json`, ESLint and Vite configuration.
- `.env.example`, `.gitignore`, `data/.gitkeep`.
- `scripts/verify.py` and `scripts/integration_test.py`.
- `README.md` with commands for PowerShell and Unix shells, `docs/MVP_SPEC.md`, and this report.

## G. Outstanding work and limitations

- No acceptance criterion is left open.
- Verification used jsdom, not a real browser. Browser-enforced CORS was checked through response headers only. A manual look in Chrome or Firefox is still advisable, particularly for visual review on phones.
- ORM `create_all` is not a migration system. Add Alembic before the schema changes with real data.
- `VITE_API_BASE_URL` is fixed at build time.
- Health is checked on load and on demand, not polled.
- `httpx` and `beautifulsoup4` are declared for Phase 2 and unused in Phase 1 code paths.
- The offline-round challenge is unannounced. Confirm it against organisers' latest instructions.

## H. Phase 2 readiness

The foundation is ready for event ingestion and extraction. Assessment by capability:

| Capability | Readiness | Basis |
| --- | --- | --- |
| Event submission | Ready | `EventCreate` and `SourceReferenceCreate` already enforce URL scheme, no embedded credentials, timezone-aware dates and date ordering. A POST route only needs to call them and persist through `get_session`. |
| Source retrieval | Ready, needs new code | `SourceReference` has `retrieved_at`, `content_hash` and `source_metadata`, and `httpx` is pinned. Still required: SSRF protection (block private and loopback addresses, redirect limits, size and time limits) before any fetch. Current URL validation checks syntax only. |
| Structured extraction | Ready | All Phase 0 fields exist as nullable columns, so partial extraction is representable. Settings already centralise configuration, so LLM keys can be added as backend-only variables. |
| Source-linked evidence | Needs one new table | Add an evidence table keyed by `events.id`, `source_references.id` and a field name, with value, excerpt, method, status and validation issues. Event and source identifiers are stable UUIDs, and evidence statuses from Phase 0 map to an enum. |
| Assessment logic | Needs Phase 3 first | Depends on evidence records. Weights should live in configuration as the specification requires. |

Risks to handle early in Phase 2: add the SSRF guard first; decide how missing, inapplicable, failed and conflicting values are represented at the field level (the evidence table is the natural home); and move to migrations at the first schema change.
