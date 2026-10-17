# EventSignal

**Evidence Before You Register.**

EventSignal is an AI-powered event intelligence platform for students. It is being built by Team NeuroIgniter for HackShift - Cmd+Shift+Create 2026 at IIIT Delhi (online-round problem statement PS3, EventRank: Discover What's Worth Attending).

Students evaluate hackathons, workshops, conferences and competitions using information scattered across many pages. EventSignal is designed to gather that information, tie each detail to its source, point out what is missing or inconsistent, and let the student decide.

> **AI extracts. Rules evaluate. Evidence explains. Students decide.**

The complete Phase 0 requirements are preserved in [`docs/MVP_SPEC.md`](docs/MVP_SPEC.md).

## Project status

This repository contains **Phase 1 - Project Foundation**. It is a working, tested base for later phases. It is not the MVP.

| Implemented now (Phase 1) | Not implemented (later phases) |
| --- | --- |
| FastAPI backend with typed, environment-driven settings | Event URL submission and manual-text input (F01) |
| SQLite database via SQLAlchemy, created on startup, never seeded | Web retrieval and page parsing |
| `Event` and `SourceReference` models matching the Phase 0 schema | LLM-based structured extraction (F02) |
| Pydantic schemas, separate from ORM models, with URL and date validation | Source-linked evidence records (F03) |
| Real health endpoint that checks the database | Completeness, evidence, consistency and relevance assessment (F04, F05, F07, F08) |
| Read-only event listing endpoint (returns the real, empty database) | Event comparison (F06) |
| React, Vite, TypeScript (strict) and Tailwind frontend shell | Authentication, user profiles, deployment |
| Live backend status, loading, error and empty states, with retry | |
| Backend and frontend test suites, plus live end-to-end integration | |

There is no event data anywhere in the application. A fresh install has an empty database, and the interface says so.

## Repository structure

```text
eventsignal/
├── backend/
│   ├── app/
│   │   ├── api/                 # HTTP routes only
│   │   │   ├── health.py        #   GET /api/v1/health
│   │   │   └── events.py        #   GET /api/v1/events (read-only)
│   │   ├── core/
│   │   │   ├── config.py        # the only place settings are defined and read
│   │   │   ├── errors.py        # global handler; no stack traces in responses
│   │   │   └── logging.py
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── base.py          #   declarative base, UTC datetime type, timestamps
│   │   │   ├── event.py
│   │   │   └── source_reference.py
│   │   ├── schemas/             # Pydantic API contracts (separate from ORM)
│   │   │   ├── event.py
│   │   │   └── health.py
│   │   ├── database.py          # engine, sessions, init, health checks
│   │   ├── main.py              # application factory and lifespan
│   │   └── __main__.py          # `python -m app` entry point
│   ├── tests/                   # 75 pytest tests, isolated temp databases
│   ├── pyproject.toml           # ruff and mypy configuration
│   ├── pytest.ini
│   ├── requirements.txt         # runtime dependencies (pinned)
│   └── requirements-dev.txt     # adds pytest, ruff, mypy
├── frontend/
│   ├── src/
│   │   ├── components/          # presentational components
│   │   ├── hooks/               # useRemoteResource (loading, error, retry)
│   │   ├── services/            # the only code that calls the backend
│   │   ├── types/               # response types mirroring the API
│   │   ├── config.ts            # reads VITE_* settings
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── vitest.live.config.ts    # live integration test config
│   ├── tsconfig.json            # strict mode
│   └── eslint.config.js
├── data/                        # local SQLite database lives here (git-ignored)
│   └── .gitkeep
├── docs/
│   ├── MVP_SPEC.md              # Phase 0 baseline
│   └── PHASE1_REPORT.md         # verification report and Phase 2 readiness
├── scripts/
│   ├── verify.py                # runs every quality gate
│   └── integration_test.py      # live backend + frontend end-to-end check
├── .env.example
├── .gitignore
└── README.md
```

## Requirements

| Software | Version tested |
| --- | --- |
| Python | 3.12 (3.12 or newer) |
| Node.js | 22 (20.19 or newer is required by Vite) |
| npm | 10 |
| Git | any recent version |

## Configuration

All environment-dependent values come from environment variables, loaded from a `.env` file in the repository root. The real `.env` is git-ignored. Only `.env.example` is committed, and it holds harmless development defaults.

macOS / Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

| Variable | Used by | Purpose | Default |
| --- | --- | --- | --- |
| `APP_NAME` | backend | Name reported by the API | `EventSignal` |
| `APP_VERSION` | backend | Version reported by the health endpoint | `0.1.0` |
| `APP_ENV` | backend | `development`, `test` or `production` | `development` |
| `LOG_LEVEL` | backend | `DEBUG` to `CRITICAL` | `INFO` |
| `BACKEND_HOST`, `BACKEND_PORT` | backend | Bind address for `python -m app` | `127.0.0.1`, `8000` |
| `BACKEND_RELOAD` | backend | Auto-reload on code change | `false` |
| `DATABASE_URL` | backend | Any SQLAlchemy URL. Relative SQLite paths resolve from the repo root | `sqlite:///./data/eventsignal.db` |
| `CORS_ORIGINS` | backend | Comma-separated browser origins allowed to call the API | `http://localhost:5173,http://127.0.0.1:5173` |
| `VITE_API_BASE_URL` | frontend | Backend address as seen by the browser. **Required**, may be empty | `http://127.0.0.1:8000` |
| `VITE_DEV_SERVER_PORT` | frontend | Vite dev-server port | `5173` |
| `VITE_PROXY_TARGET` | frontend | Backend target for the dev proxy | `http://127.0.0.1:8000` |
| `VITE_REQUEST_TIMEOUT_MS` | frontend | Request timeout | `8000` |

Invalid or missing configuration is rejected with a readable message. For example, `BACKEND_PORT=banana` makes `python -m app` exit with code 2 and list the offending variable names.

**Never put secrets in `VITE_*` variables.** Anything with that prefix is bundled into browser code. Future service keys (such as an LLM key) belong in backend-only variables.

**Two ways to connect the frontend to the backend**

- *Direct mode (default):* `VITE_API_BASE_URL` is the backend's full URL. The browser calls it directly, so `CORS_ORIGINS` must include the frontend's origin.
- *Proxy mode:* set `VITE_API_BASE_URL=` (empty). The browser calls its own origin and the Vite dev server forwards `/api` to `VITE_PROXY_TARGET`. This applies to `npm run dev` only.

`VITE_API_BASE_URL` is read when the frontend is built or started. Create `.env` before `npm run dev` or `npm run build`, and rebuild after changing it.

## Setup and run

### 1. Backend

macOS / Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m app
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m app
```

If PowerShell blocks the activation script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

The API listens on the configured host and port (`http://127.0.0.1:8000` by default). Interactive API documentation is at `/docs`. Equivalent direct launch with uvicorn: `uvicorn app.main:create_app --factory --reload`.

### 2. Frontend

In a second terminal (same commands on every platform):

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. With the backend running, the header shows **Backend connected** and the workspace shows its empty state. Stop the backend and press **Retry connection** to see the honest error state.

### 3. Production build

```bash
cd frontend
npm run build
```

Output goes to `frontend/dist/`. Preview it with `npm run preview`. Serving and deployment are out of scope for Phase 1.

## Database

- The default database is a SQLite file at `data/eventsignal.db`. The directory is created on startup if needed.
- Tables are created from the ORM models when the backend starts (`Base.metadata.create_all`). This is a development-stage choice. A migration tool such as Alembic should replace it before the schema changes for real data.
- **No rows are ever inserted automatically.** There is no seed data.
- If the database cannot be initialised, the backend still starts and reports the failure through the health endpoint instead of hiding it.
- Delete `data/eventsignal.db` at any time to start fresh.

### Data model summary

`events` holds the Phase 0 fields. Every published-information column is nullable, because a missing value is a legitimate state. Datetimes are timezone-aware and stored as UTC. `mode` is limited to `online`, `offline` or `hybrid`.

`source_references` links to an event (cascade delete) with a source type, an optional URL (unique per event), a retrieval timestamp that is set only when content was actually retrieved, a content hash, and a JSON metadata column. The Phase 0 `source_urls` field is modelled as this relationship.

Evidence records, field-level statuses and assessment results are deliberately absent. They belong to later phases.

## API

### `GET /api/v1/health`

Returns `200` only when every check passes, otherwise `503` with the same body shape.

```json
{
  "status": "healthy",
  "message": "All checks passed.",
  "app_name": "EventSignal",
  "version": "0.1.0",
  "environment": "development",
  "checked_at": "2026-01-01T10:00:00Z",
  "components": {
    "api": { "status": "ok", "message": "API responding." },
    "database": { "status": "ok", "message": "Database reachable and schema present." }
  }
}
```

| `status` | HTTP | Meaning |
| --- | --- | --- |
| `healthy` | 200 | API responding, database reachable, expected tables present |
| `degraded` | 503 | Database reachable but expected tables are missing |
| `unhealthy` | 503 | Database unreachable |

Responses never include credentials, filesystem paths or stack traces. Details go to the server log.

### `GET /api/v1/events?limit=50&offset=0`

Read-only list of stored events (`limit` 1 to 100). It exists so the interface's empty state reflects the real database. There are no create, update or delete endpoints in Phase 1.

## Testing

Run everything with one command from the repository root (after the backend virtualenv and `npm ci` steps above):

macOS / Linux:

```bash
backend/.venv/bin/python scripts/verify.py
```

Windows PowerShell:

```powershell
backend\.venv\Scripts\python scripts\verify.py
```

This runs backend lint, format check, strict type check, compile check and pytest; frontend type check, ESLint, component tests and production build; then the live integration check. Add `--skip-integration` to skip the last step.

Or run the parts individually:

```bash
# Backend (from backend/, virtualenv active)
pytest
ruff check .
mypy

# Frontend (from frontend/)
npm run typecheck
npm run lint
npm test
npm run build
```

**Isolation.** Backend tests build their own settings, ignore `.env`, and use a temporary database per test. A guard fixture fails the run if any test creates or modifies `data/eventsignal.db`. The few explicit synthetic rows used in model tests exist only in those temporary databases. Frontend tests stub the network at the `fetch` boundary, and only in test code.

**Live integration** (`scripts/integration_test.py`) starts the real backend on a free port with a throwaway database, then verifies over real HTTP: health, configured version, database file creation, empty event table, CORS allow and deny. It then runs the real React app (Vitest and jsdom, no stubbing) against that backend and against a dead port, and finally restarts the backend with an unusable database to confirm a `503` with no leaked paths or traces. It never touches your `.env` or real database.

## Known limitations

- ORM `create_all` is not a migration system.
- The live integration test uses jsdom, not a real browser, so browser CORS enforcement is checked at the HTTP-header level only. The CORS header check passes for allowed and denied origins, but a manual look in a real browser is still advisable.
- Visual design has not been reviewed across browsers or on physical devices.
- `VITE_API_BASE_URL` is fixed at build time. A built bundle must be rebuilt to point elsewhere.
- Health is checked when the page loads and on demand. There is no automatic polling.
- Ingestion dependencies (`httpx`, `beautifulsoup4`) are declared but unused until Phase 2. `httpx` is also needed by the FastAPI test client.
- The offline-round challenge has not been announced, so nothing here assumes it.

## Next phase

Phase 2, event ingestion and information extraction (F01, F02), will add event submission with URL safety checks, source retrieval, and structured extraction into the existing models. See `docs/PHASE1_REPORT.md` for the readiness assessment.
