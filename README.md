# EventSignal

**Evidence Before You Register. Connections Grounded in Purpose.**

EventSignal is an intelligent professional networking platform connecting students with relevant career and learning opportunities and the alumni and mentors who can help them pursue those opportunities.

It is being built by Team NeuroIgniter for HackShift - Cmd+Shift+Create 2026 at IIIT Delhi under the theme: **Alumni Network & Professional Connections: Building a Network, Not a Directory**.

> **"AI extracts. Rules evaluate. Evidence explains. Students decide."**

The authoritative product specification is in [`docs/MVP_SPEC.md`](docs/MVP_SPEC.md). The original Phase 0/1 specification is archived in [`docs/archive/MVP_SPEC_PHASE1.md`](docs/archive/MVP_SPEC_PHASE1.md).

---

## Core Product Workflow

Unlike a static directory of names or events, EventSignal connects opportunities with people through structured intent and explainable evidence:

```
Student Intent
    -> Relevant Opportunities
    -> Relevant Alumni and Mentors
    -> Explainable Recommendations
    -> Purpose-Specific Connection Requests
```

---

## Project Status

This repository is currently at **Phase 3 — Opportunity Intake & Evidence Collection**.

| Foundation (Phase 1) | Foundation (Phase 2) | Completed in Phase 3 | Planned (Phase 4 & Beyond) |
| --- | --- | --- | --- |
| FastAPI application factory and lifecycle | Opportunity model replacing Event with `opportunity_type`, `location`, `compensation` | Safe web retrieval service with robust SSRF protections (blocking loopback, private, link-local, metadata IPs) | Student intent & preference profiling UI |
| Environment-driven configuration | Alembic migration framework (`alembic upgrade head`) | Generic 3-stage content extractor (JSON-LD structured, HTML metadata, rule-based heuristics) | Rule-based explainable recommendation scorer |
| SQLite database initialization and health check | `FieldEvidence` source-linked evidence layer | Honest evidence attribution (`FOUND`, `NOT_FOUND`, etc.) with zero data fabrication | Alumni profile and mentorship availability matching UI |
| Read-only listing endpoint | `StudentProfile` model with self-reported goals and privacy levels | Deterministic duplicate URL detection with optional `force_refresh` | Purpose-specific connection request workflow |
| React, Vite, TypeScript (strict), Tailwind frontend shell | `AlumniProfile` model with explicit `willing_to_connect` consent gate | Opportunity intake API: `POST /api/v1/opportunities/ingest` | Automated LLM extraction provider integration (optional) |
| Complete backend unit/integration tests | `MatchExplanation` persistence grounded in attributes | React frontend intake UI with URL validation, loading state, duplicate handling, and evidence breakdown table | Real-time chat (intentionally excluded from initial MVP) |
| Quality gate verification suite (`scripts/verify.py`) | `ConnectionRequest` with explicit purpose categories and anti-self-loop validation | 138 backend tests (SSRF, retrieval, extractor, API) & 33 frontend tests | Scraping personal social media profiles (strictly prohibited) |
| | Updated `/opportunities` endpoint with backward-compatible `/events` support | Full quality gate suite: 10/10 passing (`scripts/verify.py`) | |

---

## Repository Structure

```text
eventsignal/
├── backend/
│   ├── alembic.ini              # Alembic migration configuration
│   ├── migrations/              # Database migration versions
│   │   ├── env.py               # Migration environment anchoring Base.metadata
│   │   └── versions/
│   │       └── 0001_phase2_domain_foundation.py  # Phase 2 tables migration
│   ├── app/
│   │   ├── api/                 # HTTP routes only
│   │   │   ├── health.py        #   GET /api/v1/health
│   │   │   └── opportunities.py #   GET /api/v1/opportunities & GET /api/v1/events
│   │   ├── core/
│   │   │   ├── config.py        # Typed Settings and validation
│   │   │   ├── errors.py        # Global error handlers (no leak of internals)
│   │   │   └── logging.py
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── base.py          #   DeclarativeBase, UTCDateTime, TimestampMixin
│   │   │   ├── opportunity.py   #   Opportunity entity
│   │   │   ├── source_reference.py # Source provenance
│   │   │   ├── field_evidence.py   # Field-level extraction evidence
│   │   │   ├── student_profile.py  # Self-reported student goals
│   │   │   ├── alumni_profile.py   # Self-reported expertise and consent
│   │   │   ├── match_explanation.py# Explainable recommendation rationale
│   │   │   └── connection_request.py # Purpose-specific connection requests
│   │   ├── schemas/             # Pydantic v2 API contracts
│   │   │   ├── opportunity.py   #   OpportunityCreate, OpportunityRead, etc.
│   │   │   ├── profile.py       #   Student/Alumni profile schemas
│   │   │   ├── connection.py    #   ConnectionRequest schemas
│   │   │   └── health.py        #   Health check schemas
│   │   ├── database.py          # Engine, session factory, init_db, health checks
│   │   ├── main.py              # Application factory and lifespan
│   │   └── __main__.py          # `python -m app` entry point
│   ├── tests/                   # Pytest test suite (90 tests across isolated temp DBs)
│   ├── pyproject.toml           # Ruff and Mypy strict configuration
│   ├── requirements.txt         # Runtime dependencies (pinned, includes alembic)
│   └── requirements-dev.txt     # Test/development dependencies
├── frontend/
│   ├── src/
│   │   ├── components/          # Presentational UI components
│   │   ├── hooks/               # useRemoteResource (loading, error, retry)
│   │   ├── services/            # API client and validation
│   │   ├── types/               # TypeScript interfaces
│   │   ├── config.ts            # Frontend environment configuration
│   │   ├── App.tsx              # Application shell
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json            # Strict TypeScript settings
│   └── vite.config.ts
├── docs/
│   ├── MVP_SPEC.md              # Authoritative adapted Phase 2 MVP spec
│   ├── PHASE1_REPORT.md         # Baseline Phase 1 audit report
│   └── archive/                 # Historical Phase 1 specs and models
├── scripts/
│   ├── verify.py                # Runs all 10 quality gates in order
│   └── integration_test.py      # Live end-to-end integration check
└── data/                        # Local SQLite database (git-ignored)
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ & npm

### Backend Setup

```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\pip install -r requirements-dev.txt

# On macOS/Linux:
.venv/bin/pip install -r requirements-dev.txt

# Run database migrations (optional; create_all executes on app startup if empty):
.venv\Scripts\alembic upgrade head
```

### Running the Backend

```bash
cd backend
.venv\Scripts\python -m app
# Serves at http://127.0.0.1:8000
```

### Frontend Setup & Run

```bash
cd frontend
npm ci
npm run dev
# Serves at http://localhost:5173
```

---

## Verification & Quality Gates

Run the automated quality verification suite from the repository root:

```bash
# Windows:
backend\.venv\Scripts\python scripts\verify.py

# macOS/Linux:
backend/.venv/bin/python scripts/verify.py
```

This runs all 10 quality gates in sequence:
1. `Backend: ruff lint` (strict Python linting)
2. `Backend: ruff format check` (formatting compliance)
3. `Backend: mypy (strict)` (full type validation across all modules)
4. `Backend: compile check` (compilation syntax verification)
5. `Backend: pytest` (90 automated tests on isolated temporary databases)
6. `Frontend: TypeScript (strict)` (`tsc --noEmit`)
7. `Frontend: ESLint`
8. `Frontend: component tests` (Vitest component testing)
9. `Frontend: production build` (Vite build check)
10. `Integration: live backend + frontend` (end-to-end live HTTP check with failure injection)
