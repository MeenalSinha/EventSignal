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

This repository has completed **Phase 8 — Partnerships, Cross-College Promotion, Pilot & Release Readiness**.

All 8 phases of the reduced authoritative roadmap are fully implemented, verified, and backed by automated quality gates.

| Phase 1–4: Core Foundation | Phase 5: Workspaces & RBAC | Phase 6: Network & Mentoring | Phase 7: Matching & Legacy | Phase 8: Partnerships & Pilot |
| --- | --- | --- | --- | --- |
| Opportunity ingestion with SSRF protection, generic 3-stage extraction, field-level provenance (`FieldEvidence`), deterministic duplicate detection, and declarative evidence assessment | Multi-college workspaces, tenant isolation, PBKDF2 auth, signed tokens, organizational units, campus positions, and immutable audit logging | Student & alumni profiles, server-side privacy projections, explicit `HelpOffer` lifecycle, and purpose-specific connection requests | Student needs, deterministic Gap-to-Helper matching, honest explanations, campus handovers, event memories, and follow-up commitments | Sponsorship prospectuses, brand partner verification, cross-college promotion with conspicuous disclosure, zero-consent alumni CSV import, and live pilot analytics |
| Ingestion & assessment APIs, evidence cards, conflict detection | Role assignments, workspace switching, audit log security | Consent gates (`willing_to_connect`), category filters | Persisted needs & handovers, deterministic scores | Transparent pricing packages, dry-run import preview, real stored metrics |
| 166 backend tests & 36 frontend tests | Institutional Auth & RBAC UI | 173 backend tests & 43 frontend tests | 209 backend tests & 45 frontend tests | **214 backend tests & 47 frontend tests across all quality gates (ALL PASS)** |

---

## Repository Structure

```text
eventsignal/
├── backend/
│   ├── alembic.ini              # Alembic migration configuration
│   ├── migrations/              # Database migration versions
│   │   ├── env.py               # Migration environment anchoring Base.metadata
│   │   └── versions/            # 0001-0007 migrations (Phases 1-8)
│   ├── app/
│   │   ├── api/                 # HTTP routes
│   │   │   ├── health.py        #   GET /api/v1/health
│   │   │   ├── opportunities.py #   Opportunities intake & assessment
│   │   │   ├── auth.py          #   Registration, login & session endpoints
│   │   │   ├── institutions.py  #   Colleges, units, positions & memberships
│   │   │   ├── profiles.py      #   Student & alumni profiles, member discovery
│   │   │   ├── help_offers.py   #   Help offers lifecycle, discovery & requests
│   │   │   ├── phase7.py        #   Phase 7: Student needs, matches, handovers, memories, tasks
│   │   │   ├── phase8.py        #   Phase 8: Sponsorships, campaigns, CSV import, pilot metrics
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
│   │   │   ├── student_need.py  #   Phase 7: Declared student challenges
│   │   │   ├── helper_match.py  #   Phase 7: Persisted helper matches
│   │   │   ├── match_explanation.py # Phase 7: Deterministic score rationales
│   │   │   ├── legacy_handover.py # Phase 7: Leadership transition handovers
│   │   │   ├── event_memory.py  #   Phase 7: Institutional event retrospectives
│   │   │   ├── follow_up_task.py # Phase 7: Post-event follow-up commitments
│   │   │   ├── sponsorship.py   #   Phase 8: Partner orgs & sponsorship prospectuses
│   │   │   ├── promotion_campaign.py # Phase 8: Cross-college campaigns
│   │   │   └── alumni_import.py #   Phase 8: Batch alumni directory import jobs
│   │   ├── services/            # Business & security services
│   │   │   ├── auth.py          #   User lifecycle & token management
│   │   │   ├── institution.py   #   Multi-tenant workspace operations
│   │   │   ├── profile.py       #   Profile CRUD, active gate, privacy projection
│   │   │   ├── help_offer.py    #   Offer lifecycle, discovery & requests
│   │   │   ├── matching.py      #   Phase 7: Deterministic matching engine
│   │   │   ├── legacy.py        #   Phase 7: Handovers, memories & tasks
│   │   │   ├── sponsorship.py   #   Phase 8: Sponsorship lifecycle & commercial terms
│   │   │   ├── promotion.py     #   Phase 8: Campaign review & cross-college feed
│   │   │   ├── alumni_import.py #   Phase 8: Dry-run CSV parser & zero-consent import
│   │   │   ├── pilot_metrics.py #   Phase 8: Operational indicators aggregator
│   │   │   └── audit.py         #   Security event logging
│   │   ├── schemas/             # Pydantic v2 API contracts
│   │   ├── database.py          # Engine, session factory, init_db, health checks
│   │   ├── main.py              # Application factory and lifespan
│   │   └── __main__.py          # `python -m app` entry point
│   ├── tests/                   # Pytest suite (214 tests across isolated DBs)
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
│   │   │   ├── LegacyMatchingPanel.tsx # Phase 7: Needs matching & legacy handovers
│   │   │   ├── PartnershipsPromotionPanel.tsx # Phase 8: Sponsorships, campaigns, CSV import, metrics
│   │   │   ├── AssessmentPanel.tsx # Opportunity assessment viewer
│   │   │   └── OpportunityIntakeForm.tsx # URL ingest & evidence review
│   │   ├── hooks/               # useRemoteResource (loading, error, retry)
│   │   ├── services/            # API client and validation
│   │   ├── types/               # TypeScript interfaces
│   │   ├── App.tsx              # Application shell with 6-tab navigation
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json            # Strict TypeScript settings
│   └── vite.config.ts
├── scripts/
│   ├── verify.py                # Runs all quality gates in order
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
