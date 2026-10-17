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

This repository has completed **Phase 6 — Campus Network, Profiles & Help Offers**.

| Foundation (Phase 1) | Domain Model (Phase 2) | Intake & Ingestion (Phase 3) | Assessment & Evaluation (Phase 4) | Institutional Identity & RBAC (Phase 5) | Campus Network & Help Offers (Phase 6) |
| --- | --- | --- | --- | --- | --- |
| FastAPI application factory and lifecycle | Opportunity model with `opportunity_type`, `location`, `compensation` | Safe web retrieval service with robust SSRF protections (blocking loopback, private, link-local, metadata IPs) | Declarative, configurable Assessment Policy (`default_assessment_policy.json` validated via Pydantic) | Multi-college workspaces with strict multi-tenant isolation and workspace-scoped opportunity filtering | Institution-scoped `StudentProfile` and `AlumniProfile` models tied to authenticated users and active memberships |
| Environment-driven configuration | Alembic migrations (`alembic upgrade head`) | Generic 3-stage content extractor (JSON-LD structured, HTML metadata, rule-based heuristics) | Multi-dimensional scoring engine: Completeness, Evidence Quality, Cross-Source Consistency | Standard-library PBKDF2 password hashing & HMAC-SHA256 signed bearer token authentication | Granular server-side privacy projections (`private`, `students_only`, `alumni_only`, `public`) with zero data leaks |
| SQLite database initialization and health check | `FieldEvidence` source-linked evidence layer | Honest evidence attribution (`FOUND`, `NOT_FOUND`, etc.) with zero data fabrication | Multi-source conflict detection preserving competing values, source attribution, and supporting excerpts | Hierarchical organizational units (departments, cells, centers, offices) and official campus positions | Explicit, consent-based `HelpOffer` model with lifecycle states (`active`, `paused`, `archived`) and owner consent control |
| Read-only listing endpoint | `StudentProfile` model with self-reported goals and privacy levels | Deterministic duplicate URL detection with optional `force_refresh` | Assessment persistence models & versioned migrations (`0002`, `0003`, `0004`) | Time-bounded campus role assignments with verification workflows and immutable security audit logs | Purpose-specific connection requests linking students to mentors on published help offers |
| React, Vite, TypeScript (strict), Tailwind frontend shell | `AlumniProfile` model with explicit `willing_to_connect` consent gate | Opportunity intake API: `POST /api/v1/opportunities/ingest` | Assessment APIs: `POST /api/v1/opportunities/{id}/assess`, `GET .../assessment`, `POST .../sources` | Institutional Auth & Workspace UI (`AuthModal`, `InstitutionWorkspacePanel`, college switcher, role badges) | Complete frontend experience: `MyProfileModal`, `MemberDiscoveryPanel`, `HelpOffersPanel`, dynamic category filters |
| Quality gate verification suite (`scripts/verify.py`) | `ConnectionRequest` with explicit purpose categories and anti-self-loop validation | React frontend intake UI with URL validation, loading state, duplicate handling, and evidence breakdown table | Explainable Assessment Panel UI with score ring, dimension breakdowns, counters, and conflict details | 166 backend tests & 36 frontend tests | 173 backend tests & 43 frontend tests across all 10 automated quality gates (10/10 PASS) |

---

## Repository Structure

```text
eventsignal/
├── backend/
│   ├── alembic.ini              # Alembic migration configuration
│   ├── migrations/              # Database migration versions
│   │   ├── env.py               # Migration environment anchoring Base.metadata
│   ├── migrations/              # Database migration versions
│   │   ├── env.py               # Migration environment anchoring Base.metadata
│   │   └── versions/            # 0001-0005 migrations (Phase 1-6)
│   ├── app/
│   │   ├── api/                 # HTTP routes only
│   │   │   ├── health.py        #   GET /api/v1/health
│   │   │   ├── opportunities.py #   Opportunities intake & assessment
│   │   │   ├── auth.py          #   Registration, login & session endpoints
│   │   │   ├── institutions.py  #   Colleges, units, positions & memberships
│   │   │   ├── profiles.py      #   Student & alumni profiles, member discovery
│   │   │   ├── help_offers.py   #   Help offers lifecycle, discovery & requests
│   │   │   └── deps.py          #   FastAPI auth & RBAC dependency injection
│   │   ├── core/
│   │   │   ├── config.py        # Typed Settings and validation
│   │   │   ├── errors.py        # Global error handlers (no leak of internals)
│   │   │   ├── security.py      # PBKDF2 password hashing & signed token auth
│   │   │   └── logging.py
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── base.py          #   DeclarativeBase, UTCDateTime, TimestampMixin
│   │   │   ├── opportunity.py   #   Opportunity entity (scoped to institution_id)
│   │   │   ├── user.py          #   Platform User identity
│   │   │   ├── institution.py   #   Colleges / institutional workspaces
│   │   │   ├── membership.py    #   Multi-tenant RBAC memberships & roles
│   │   │   ├── student_profile.py # Institution-scoped StudentProfile
│   │   │   ├── alumni_profile.py  # Institution-scoped AlumniProfile & consent
│   │   │   ├── help_offer.py    #   Explicit HelpOffer & lifecycle states
│   │   │   ├── connection_request.py # Purpose-specific connection requests
│   │   │   ├── organizational_unit.py # Departments, cells, and offices
│   │   │   ├── campus_position.py # Official campus positions & tenure
│   │   │   ├── audit_log.py     #   Immutable security audit log
│   │   │   ├── source_reference.py # Source provenance
│   │   │   └── field_evidence.py   # Field-level extraction evidence
│   │   ├── services/            # Business & security services
│   │   │   ├── auth.py          #   User lifecycle & token management
│   │   │   ├── institution.py   #   Multi-tenant workspace operations
│   │   │   ├── profile.py       #   Profile CRUD, active gate, privacy projection
│   │   │   ├── help_offer.py    #   Offer lifecycle, discovery & requests
│   │   │   ├── audit.py         #   Security event logging
│   │   │   ├── crawler.py       #   Safe SSRF-protected content fetcher
│   │   │   ├── extractor.py     #   Structured & heuristic data extraction
│   │   │   └── evaluator.py     #   Explainable opportunity assessment
│   │   ├── schemas/             # Pydantic v2 API contracts
│   │   ├── database.py          # Engine, session factory, init_db, health checks
│   │   ├── main.py              # Application factory and lifespan
│   │   └── __main__.py          # `python -m app` entry point
│   ├── tests/                   # Pytest test suite (173 tests across isolated DBs)
│   ├── pyproject.toml           # Ruff and Mypy strict configuration
│   └── requirements.txt         # Runtime dependencies (pinned, includes alembic)
├── frontend/
│   ├── src/
│   │   ├── components/          # Presentational UI components
│   │   │   ├── AuthModal.tsx    #   Authentication & session modal
│   │   │   ├── MyProfileModal.tsx # Student & alumni profile editor
│   │   │   ├── MemberDiscoveryPanel.tsx # College network member discovery
│   │   │   ├── HelpOffersPanel.tsx # Campus mentorship & help offer manager
│   │   │   ├── InstitutionWorkspacePanel.tsx # College workspace manager
│   │   │   ├── AssessmentPanel.tsx # Opportunity assessment viewer
│   │   │   └── OpportunityIntakeForm.tsx # URL ingest & evidence review
│   │   ├── hooks/               # useRemoteResource (loading, error, retry)
│   │   ├── services/            # API client and validation
│   │   ├── types/               # TypeScript interfaces
│   │   ├── App.tsx              # Application shell with view switching
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json            # Strict TypeScript settings
│   └── vite.config.ts
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
5. `Backend: pytest` (173 automated tests on isolated temporary databases)
6. `Frontend: TypeScript (strict)` (`tsc --noEmit`)
7. `Frontend: ESLint`
8. `Frontend: component tests` (43 automated Vitest tests)
9. `Frontend: production build` (Vite build check)
10. `Integration: live backend + frontend` (end-to-end live HTTP check with failure injection)
