# EventSignal

**Evidence Before You Register. Connections Grounded in Purpose.**

EventSignal is an intelligent campus opportunity discovery and purpose-driven networking platform connecting students, seniors, alumni, faculty, and student organizations.

Built for **Hacktober HackDays 2026 — SheBuilds, Tech for Social Good**, continuing from its original foundation developed for **HackShift — Cmd+Shift+Create 2026** at IIIT Delhi (Team NeuroIgniter).

> **"AI extracts. Rules evaluate. Evidence explains. Students decide."**

- **Authoritative Product Specification:** [`docs/MVP_SPEC.md`](docs/MVP_SPEC.md)
- **Competition Implementation Record:** [`docs/HACKTOBER_HACKDAYS_2026.md`](docs/HACKTOBER_HACKDAYS_2026.md)
- **Comprehensive Quality Audit Report:** [`docs/FINAL_AUDIT_REPORT.md`](docs/FINAL_AUDIT_REPORT.md)
- **Demo Mode Verification Report:** [`docs/DEMO_MODE_AUDIT_REPORT.md`](docs/DEMO_MODE_AUDIT_REPORT.md)

---

## 1. Project Title & Tagline

**EventSignal**  
*Evidence Before You Register. Connections Grounded in Purpose.*

---

## 2. Competition & Project Overview

EventSignal is developed for the **SheBuilds — Tech for Social Good** track of **Hacktober HackDays 2026**.

The project originated at **HackShift — Cmd+Shift+Create 2026** under the theme *Alumni Network & Professional Connections: Building a Network, Not a Directory*. In this repository, EventSignal’s foundation has been audited, documented, and aligned with the civic and educational mission of **Tech for Social Good**: democratizing opportunity discovery, facilitating purpose-driven mutual aid, and preserving institutional knowledge across student generations.

---

## 3. Core Product Workflow

EventSignal structures campus interaction around a 3-pillar workflow:

$$\textbf{Discover} \longrightarrow \textbf{Connect} \longrightarrow \textbf{Preserve}$$

1. **Discover (Opportunity Intake & Credibility Assessment):** Students browse and evaluate hackathons, fellowships, and internships with transparent, field-level extraction provenance (`FieldEvidence`) and declarative credibility tiers (High, Moderate, Speculative).
2. **Connect (Deterministic Gap-to-Helper Matching):** Students declare learning gaps; an explainable rules engine matches them with verified peers and alumni mentors who have explicitly granted consent (`willing_to_connect = true`), eliminating cold outreach spam.
3. **Preserve (EventSignal Legacy & Institutional Memory):** Student leaders document officer handovers (`LegacyHandover`), post-event retrospectives (`EventMemory`), and post-event follow-up commitments (`FollowUpTask`), preventing campus amnesia as seniors graduate.

---

## 4. 🚀 Quick Start (Up & Running in 5 Minutes)

This Quick Start contains verified repository instructions for setting up, running, and exploring EventSignal locally.

### 4.1 Prerequisites
Ensure the following tools are installed on your machine:
- **Python:** `3.11+` (Verified on Python `3.14.2`)
- **Node.js:** `18+` (Verified on Node `22.x` & npm `10.x`)
- **Git:** Standard git client

### 4.2 Clone the Repository
```bash
git clone https://github.com/MeenalSinha/EventSignal.git
cd EventSignal
```

### 4.3 Configure Environment Variables
Copy the safe development configuration template from `.env.example` to `.env` in the repository root:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

> [!NOTE]
> `.env.example` ships with safe local development defaults. No external API keys (e.g. Cloudinary, payment gateways) are required for local execution or presentation demo evaluation. All sensitive secrets remain strictly server-side and excluded from version control.

---

### 4.4 Start the Complete Application (2 Terminals)

#### Terminal 1 — Backend (FastAPI)

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
# Activate virtual environment
.\.venv\Scripts\Activate.ps1
# Install development & runtime dependencies
pip install -r requirements-dev.txt
# Start the backend server
python -m app
```
*(Alternative without script activation: `.\.venv\Scripts\pip install -r requirements-dev.txt` then `.\.venv\Scripts\python.exe -m app`)*

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
# Activate virtual environment
source .venv/bin/activate
# Install development & runtime dependencies
pip install -r requirements-dev.txt
# Start the backend server
python -m app
```

- **Backend Status:** Listens on `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check Endpoint:** `http://127.0.0.1:8000/api/v1/health`
- **Database Initialization:** The local SQLite database (`data/eventsignal.db`) and its containing folder are automatically initialized upon startup. If `DEMO_MODE_ENABLED=true` (the default in `.env.example`), the synthetic demonstration community is seeded automatically and idempotently.

---

#### Terminal 2 — Frontend (React 19 + Vite)

```bash
cd frontend
# Install pinned dependencies
npm ci
# Launch Vite development server
npm run dev
```

- **Frontend Client:** Available at `http://localhost:5173`
- **Dev Server Proxy:** Vite automatically communicates with the backend API at `http://127.0.0.1:8000`.

---

### 4.5 Exploring Access Modes
When opening `http://localhost:5173`, select one of three access modes:

1. **Presentation Demo Mode (Recommended for Evaluators):**
   - Click the **"Demo Mode"** tab.
   - Use default demo credentials: `demo@eventsignal.local` / `DemoSignal2026!Secure`.
   - Explores the isolated **Apex Institute of Technology** (`demo-inst-apex-tech-001`) with 30 synthetic members, 13 academic units, 12 opportunities, 12 help offers, and an interactive 5-stage tour card.
2. **Guest Mode:**
   - Click **"Continue as Guest"**.
   - Browse public opportunity listings in read-only mode without authentication. Institutional APIs return HTTP 401/403.
3. **Normal User Mode:**
   - Register or sign in with your own credentials to create authentic institutional records.

---

### 4.6 Quick Verification Smoke Test
To verify that your local installation is healthy, run the test suites:

```powershell
# Run backend regression tests (229 tests, ~3 mins)
cd backend
.\.venv\Scripts\pytest -q

# Run frontend tests & type checks (71 tests, ~1 min)
cd ../frontend
npm test -- --run
npm run typecheck
npm run build
```

---

### 4.7 First-Run Troubleshooting Guide

| Symptom | Probable Cause | Diagnostic & Resolution Step |
| :--- | :--- | :--- |
| **"Cannot connect to backend"** banner | Backend is not running or port conflict | Confirm Terminal 1 shows `Uvicorn running on http://127.0.0.1:8000`. Verify `VITE_API_BASE_URL=http://127.0.0.1:8000` in `.env`. |
| **`ConfigurationError: Missing .env`** | Environment file not copied | Run `Copy-Item .env.example .env` (or `cp .env.example .env`) in the repository root. |
| **PowerShell script execution error** | Script execution policy restricted | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or directly invoke `.\.venv\Scripts\python.exe -m app`. |
| **Port 8000 already in use** | Another local service using port 8000 | In `.env`, change `BACKEND_PORT=8001`, update `VITE_API_BASE_URL=http://127.0.0.1:8001`, and update `CORS_ORIGINS`. |
| **Demo Tab missing on landing page** | `DEMO_MODE_ENABLED` set to `false` | In `.env`, set `DEMO_MODE_ENABLED=true` and restart the backend server in Terminal 1. |
| **Database lock or migration mismatch** | Stale local SQLite file | Delete `data/eventsignal.db` and restart `python -m app` to auto-recreate and re-seed clean tables. |

---

## 5. Problem Statement

Modern college ecosystems face critical structural inequalities in student opportunity and professional growth:

1. **Information Inequality in Opportunity Discovery:** Valuable hackathons, research fellowships, startup grants, and specialized internships are scattered across chaotic messaging channels (WhatsApp, Telegram, Discord), unindexed departmental sites, and informal peer networks. Students outside privileged social circles miss crucial deadlines or invest effort into unverified, low-credibility events.
2. **Superficial, Directory-Style Networking:** Traditional college alumni portals resemble static phone books. Students resort to cold, uncontextualized outreach with dismal response rates, while alumni face broad, unfocused requests that ignore their availability and domain expertise.
3. **Institutional Amnesia (Campus Brain Drain):** Student societies, technical chapters, and organizing committees experience organizational memory loss every 1–2 years as senior cohorts graduate. Event retrospectives, vendor contacts, sponsor relationships, and leadership handover notes vanish, forcing incoming student leaders to rebuild from scratch.

---

## 6. Target Users & Social Impact

### 6.1 Target Users
- **Students:** Seeking credible, evidence-backed hackathons, fellowships, and internships, and requesting purpose-specific guidance from compatible mentors.
- **Seniors & Alumni Mentors:** Sharing domain expertise, publishing structured help offers, and setting explicit availability and consent thresholds.
- **Campus Club Leaders & Organizers:** Managing student organizations, conducting transparent leadership handovers, and preserving post-event lessons.
- **Faculty & College Administrators:** Overseeing multi-tenant campus workspaces, appointing official student positions, and reviewing verified pilot metrics.
- **Corporate & Community Partners:** Sponsoring student initiatives through transparent prospectuses and cross-college campaigns with conspicuous disclosure.
- **Hackathon Judges & Evaluators:** Exploring the platform using an isolated presentation environment (**Demo Mode**) pre-populated with an interconnected synthetic college community.

### 6.2 Social Impact
EventSignal acts as an equalizer for campus communities:
- **Democratizes Access:** Leveling the playing field so every student, regardless of existing social network or seniority, can access verified opportunities.
- **Protects Student Time & Trust:** Field-level evidence provenance (`FieldEvidence`) prevents students from falling victim to misleading opportunity claims.
- **Promotes Purposeful Mentorship:** Eliminating spam and cold outreach by routing requests only to mentors who have explicitly consented and match declared learning gaps.
- **Builds Long-Term Civic Capital:** Retaining institutional experience on campus, transforming student leadership from an ephemeral cycle into an enduring institutional asset.

---

## 7. Deep-Dive Core Features

### 7.1 Opportunity Discovery (Discover)
- **Secure Public URL Ingestion:** Streamlined intake with robust Server-Side Request Forgery (SSRF) protection, port allowlists (80/443), and private IP blocking.
- **Generic 3-Stage Extraction:** Multi-stage content extraction across JSON-LD structured data, OpenGraph tags, and semantic heuristic trees.
- **Field-Level Provenance (`FieldEvidence`):** Distinguishes extraction outcomes (`FOUND`, `NOT_FOUND`, `SOURCES_DISAGREE`, `EXTRACTION_FAILED`).
- **Deterministic Deduplication:** Canonical URL normalization prevents duplicate listings while supporting administrative refresh.
- **Declarative Evidence Assessment:** Policy-driven scoring of completeness, evidence tiers (High, Moderate, Speculative), and source conflict tracking.

### 7.2 Gap-to-Helper Engine (Connect)
- **Student Need Declaration:** Students articulate specific challenges, required skills, urgency, and privacy scope.
- **Deterministic Matching Engine:** Rule-based compatibility scoring pairing student needs with active help offers and alumni expertise.
- **Grounded Match Explanations (`MatchExplanation`):** Transparent rationales explaining domain overlap, skill synergy, and availability.
- **Explicit Help Offers (`HelpOffer`):** Mentors publish structured offers with defined delivery modes and monthly capacities.
- **Consent-Gated Connection Routing:** Enforces `willing_to_connect = true` and monthly connection caps before requests can be routed.

### 7.3 EventSignal Legacy (Preserve)
- **Leadership Handovers (`LegacyHandover`):** Multi-stage transition records (`draft`, `submitted`, `acknowledged`, `superseded`) from outgoing to incoming club officers.
- **Institutional Event Memories (`EventMemory`):** Retrospectives capturing achievements, operational mistakes, vendor contacts, and institutional lessons.
- **Follow-up Commitments (`FollowUpTask`):** Accountable post-event tasks with priority levels and permanent completion locking.

### 7.4 Institutional Workspace & Pilot Suite
- Multi-tenant college workspaces with Role-Based Access Control (`PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `MEMBER`).
- Verified partner directory, tiered sponsorship prospectuses, and cross-college campaigns with mandatory "Featured — Sponsored" disclosures.
- Pre-commit dry-run CSV alumni directory import with zero default consent.
- Measurable operational pilot metrics calculated from persisted records.

---

## 8. Key Differentiators

| Traditional Campus Portals | EventSignal Platform |
| :--- | :--- |
| **Static Directory of Names:** Unfiltered lists encouraging blind cold messaging. | **Purpose-Grounded Matching:** Needs-based Gap-to-Helper engine pairing specific student gaps with consented mentors. |
| **Unverified Opportunity Bulletins:** Promotional text accepted without validation. | **Evidence Before You Register:** Field-level extraction provenance (`FieldEvidence`) exposing missing or conflicting data. |
| **Black-Box AI Recommendations:** Opaque suggestions with no explainability. | **Deterministic, Explainable Rules:** Human-auditable scoring breakdowns explaining every match rationale. |
| **Annual Institutional Memory Wipeout:** Information lost when club leaders graduate. | **EventSignal Legacy:** Structured handovers, event retrospectives, and follow-up commitments preserved across cohorts. |
| **Unregulated Outreach:** Mentors inundated with random connection requests. | **Consent & Availability Gates:** Outreach strictly requires `willing_to_connect = true` and respects monthly capacity limits. |

---

## 9. Actual Technology Stack

The stack is strictly aligned with the codebase manifests (`backend/requirements.txt`, `frontend/package.json`):

### Backend
- **Framework:** FastAPI `0.143.3` (ASGI web framework)
- **Language / Runtime:** Python `3.12+` (Verified on Python `3.14.2`)
- **Server:** Uvicorn `0.54.0` (standard worker)
- **Validation & Settings:** Pydantic `2.14.1` & Pydantic-Settings `2.16.0`
- **Email Validation:** email-validator `2.2.0`
- **ORM & Database Toolkit:** SQLAlchemy `2.1.4` (DeclarativeBase, 2.0-style queries)
- **Schema Migrations:** Alembic `1.16.1` (7 linear migration scripts)
- **HTTP Client & Parsing:** httpx `0.28.1`, BeautifulSoup4 `4.15.0`
- **Authentication:** PBKDF2-HMAC-SHA256 password hashing, PyJWT-based HS256 tokens

### Frontend
- **Framework:** React `19.3.1` with React DOM `19.3.1`
- **Language:** TypeScript `~5.9.3` (Strict mode configured)
- **Build Tool & Dev Server:** Vite `8.3.4`
- **Styling:** Vanilla Tailwind CSS `4.3.3` (`@tailwindcss/vite`)
- **Testing:** Vitest `5.0.5`, `@testing-library/react` `16.3.3`, jsdom `30.1.3`
- **Avatars:** Client-side dynamic SVG identicons (`Avatar.tsx`)

### Database & Storage
- **Local Database:** SQLite (`data/eventsignal.db`)
- **Production Database Target:** PostgreSQL (connection string configurable via `DATABASE_URL`)
- **Media Storage:** **Not Implemented** (See Section 19 for proposed Cloudinary architecture)

---

## 10. Architecture Diagram

The diagram below reflects the verified application components. Solid lines indicate fully implemented and verified flows; dashed lines indicate the proposed Cloudinary media integration:

```mermaid
graph TD
    subgraph Users ["Campus Community"]
        Student["Student"]
        Senior["Senior / Alumni"]
        Leader["Club Leader / Organizer"]
        Admin["College Administrator"]
        Presenter["Evaluator / Demo User"]
    end

    subgraph Client ["Frontend Layer (React 19 + TypeScript + Tailwind v4)"]
        Landing["Auth Landing Page\n(Normal / Guest / Demo)"]
        Shell["Application Shell\n(3-Column Layout & ErrorBoundary)"]
        FeedUI["Opportunity Feed & Evidence Cards"]
        NetworkUI["Campus Network & Member Discovery"]
        OffersUI["Mutual Aid & Help Offers"]
        LegacyUI["Institutional Memory & Handovers"]
        PartnersUI["Partnerships & Pilot Metrics"]
        TourUI["Evaluator Guided Tour"]
    end

    subgraph API ["FastAPI REST Backend (/api/v1)"]
        AuthAPI["/auth\n(PBKDF2, JWT, Demo Seeding & Reset)"]
        OppAPI["/opportunities & /assessment\n(SSRF Guard, Ingestion, Scoring)"]
        ProfileAPI["/profiles & /help-offers\n(Privacy Projections, Consent Gates)"]
        Phase7API["/phase7\n(Matching Engine, Handovers, Memories)"]
        Phase8API["/phase8\n(Partnerships, CSV Import, Pilot Analytics)"]
        InstAPI["/institutions\n(Multi-Tenant RBAC & Workspaces)"]
        MediaAPI["[PLANNED] /media/sign-upload\n(HMAC-SHA256 Signature)"]
    end

    subgraph Services ["Core Business Logic"]
        IngestSvc["Ingestion & Extraction Service"]
        MatchSvc["Deterministic Gap-to-Helper Matching"]
        LegacySvc["Handover & Retrospective Service"]
        DemoSvc["Idempotent Demo Seeding Service"]
        ImportSvc["Alumni CSV Dry-Run Parser"]
        MetricsSvc["Live Operational Metrics Aggregator"]
    end

    subgraph Persistence ["Persistence Layer"]
        DB[("Database (SQLite / PostgreSQL)\n7 Linear Alembic Migrations")]
    end

    subgraph CloudMedia ["External Cloud Media (Planned Competition Feature)"]
        Cloudinary[("Cloudinary Media Cloud\n(Signed Uploads, Auto-format CDN)")]
    end

    %% User Interactions
    Users --> Landing
    Landing --> Shell
    Shell --> FeedUI & NetworkUI & OffersUI & LegacyUI & PartnersUI & TourUI

    %% Client to Backend API (Solid = Existing)
    FeedUI --> OppAPI
    NetworkUI & OffersUI --> ProfileAPI
    OffersUI & LegacyUI --> Phase7API
    PartnersUI --> Phase8API
    Shell --> InstAPI
    Landing --> AuthAPI

    %% Backend to Services
    OppAPI --> IngestSvc
    Phase7API --> MatchSvc & LegacySvc
    AuthAPI --> DemoSvc
    Phase8API --> ImportSvc & MetricsSvc

    %% Services to DB
    IngestSvc & MatchSvc & LegacySvc & DemoSvc & ImportSvc & MetricsSvc --> DB

    %% Proposed Cloudinary Integration (Dashed = Planned)
    FeedUI -.->|Request Upload Signature| MediaAPI
    MediaAPI -.->|Generate HMAC Signature| FeedUI
    FeedUI -.->|Direct Signed Upload| Cloudinary
    FeedUI -.->|Store Asset Reference| OppAPI
    Cloudinary -.->|Deliver Transformed Media| FeedUI

    classDef planned fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,stroke-dasharray: 5 5;
    class MediaAPI,Cloudinary planned;
```

---

## 11. Security and Privacy Principles

1. **Password Hashing:** PBKDF2-HMAC-SHA256 with unique per-user salt; plaintext passwords are never stored or logged.
2. **Token Security:** HS256-signed JWT tokens with expiration validation. No session hijacking through local storage spoofing.
3. **SSRF Defense:** Strict socket resolution blocking access to `127.0.0.1`, loopback, link-local (`169.254.0.0/16`), and private RFC-1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
4. **Tenant Isolation:** Every institution-scoped route dependency enforces `require_institution_membership`. Cross-tenant data leakage is prevented at the database query layer.
5. **Privacy by Default:** Student profiles default to `PRIVATE` visibility.
6. **Mandatory Consent Gates:** Unsolicited outreach to alumni is blocked unless `willing_to_connect = true`.
7. **Honest Uncertainty:** Missing information is explicitly labeled `NOT_FOUND` or `NEEDS_VERIFICATION`—never masked as fraudulent or clean nulls.
8. **Demo Data Isolation:** Demonstration records carry `institution_id = "demo-inst-apex-tech-001"` and cannot be accessed or modified by real tenants.

---

## 12. Three-Mode Access Model & Demo Community

EventSignal enforces a strict three-mode access boundary:

| Feature | Normal User Mode | Guest Mode | Presentation Demo Mode |
| :--- | :--- | :--- | :--- |
| **Authentication** | Personal Email & Password | None (Unauthenticated) | Dedicated Demo Credentials |
| **Session Token** | Signed JWT (`is_demo: false`) | None | Signed JWT (`is_demo: true`) |
| **Workspace Scope** | Real Institutional Workspace | Global Public Feed Only | Apex Institute of Technology (`demo-inst-apex-tech-001`) |
| **Institutional APIs** | Authorized access | Blocked (HTTP 401/403) | Scoped to demo data |
| **Visual Indicator** | Standard Header | Guest Mode Indicator | Amber Persistent Demo Banner |

### 12.1 Apex Institute of Technology Synthetic Community
Demo Mode provisions a complete, interconnected demonstration dataset on backend startup:
- **13 Academic Units & Clubs:** Departments (CSE, AI/DS, ECE, Design, Management) and societies (ACM Chapter, Robotics, E-Cell).
- **10 Official Campus Positions:** Club presidents, vice-presidents, and secretaries.
- **30 Synthetic Members:** Students, alumni mentors, and faculty with active profiles.
- **12 Curated Opportunities:** Hackathons, fellowships, and internships with field-level evidence provenance.
- **12 Active Help Offers:** Multi-track mentorship offers.
- **4 Student Needs & 3+ Helper Matches:** Real deterministic match scores with explanations.
- **3 Handovers, 3 Event Memories, 6 Follow-Up Tasks:** Institutional continuity records.
- **3 Verified Partners, 3 Sponsorships, 2 Campaigns, 1 CSV Import Job.**

### 12.2 Demo Seeding & Reset Endpoints
- `GET /api/v1/auth/demo/status`: Returns current seeding status.
- `POST /api/v1/auth/demo/seed`: Idempotently seeds all demo records (requires authentication).
- `POST /api/v1/auth/demo/reset`: Safely clears demo records without touching real data (requires authentication).

---

## 13. Repository Structure

```text
eventsignal/
├── .env.example             # Safe development configuration template
├── README.md                # Main repository documentation & guide
├── backend/
│   ├── alembic.ini          # Alembic database migration configuration
│   ├── pyproject.toml       # Ruff and Mypy strict configuration
│   ├── pytest.ini           # Pytest test discovery settings
│   ├── requirements.txt     # Runtime Python dependencies (pinned)
│   ├── requirements-dev.txt # Development & test tools (pytest, ruff, mypy)
│   ├── app/
│   │   ├── api/             # FastAPI HTTP routes (health, auth, opportunities, profiles, phase7, phase8)
│   │   ├── core/            # Typed settings, security, logging, error handling
│   │   ├── models/          # SQLAlchemy ORM models (21 entities)
│   │   ├── schemas/         # Pydantic v2 request/response contracts
│   │   ├── services/        # Business logic: matching, legacy, ingestion, demo, pilot
│   │   ├── database.py      # Database engine, session factory, connectivity checks
│   │   └── main.py          # FastAPI application factory and startup lifespan
│   ├── migrations/          # Alembic migrations (0001 through 0007)
│   └── tests/               # 20 test files, 229 passing unit & integration tests
├── frontend/
│   ├── package.json         # React 19, TypeScript, Vite, Tailwind v4, Vitest
│   ├── tsconfig.json        # Strict TypeScript configuration
│   ├── vite.config.ts       # Vite bundler configuration & dev server proxy
│   └── src/
│       ├── components/      # UI components (Auth, Feed, Network, Offers, Legacy, Partnerships)
│       ├── hooks/           # Custom React hooks (useRemoteResource)
│       ├── services/        # Typed API clients (auth, opportunities, profiles, legacy, phase8)
│       ├── types/           # TypeScript interfaces mirroring API contracts
│       ├── App.tsx          # Main application shell with 8-tab navigation & ErrorBoundary
│       └── main.tsx         # React application entry point
├── docs/
│   ├── MVP_SPEC.md          # Authoritative MVP product specification
│   ├── HACKTOBER_HACKDAYS_2026.md # Competition implementation record & Cloudinary audit
│   ├── FINAL_AUDIT_REPORT.md     # Phase 1-8 technical audit report
│   ├── DEMO_MODE_AUDIT_REPORT.md # 3-mode access & presentation demo verification
│   ├── PHASE1_REPORT.md     # Historical Phase 1 foundation report
│   ├── PHASE4_REPORT.md     # Historical Phase 4 assessment engine report
│   └── archive/             # Historical initial specification
├── scripts/
│   ├── verify.py            # Automated quality gates runner
│   └── integration_test.py  # Live end-to-end integration verification
└── data/                    # Local SQLite database files (git-ignored)
```

---

## 14. Environment Configuration Reference

All environment variables are declared and validated in `backend/app/core/config.py`. Copy `.env.example` to `.env` in the repository root:

| Variable | Default Safe Value | Classification | Description |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | `EventSignal` | General | Display name reported by health endpoint |
| `APP_VERSION` | `0.1.0` | General | Application version reported in API specs |
| `APP_ENV` | `development` | Core | Environment name (`development`, `test`, `production`) |
| `LOG_LEVEL` | `INFO` | Core | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `BACKEND_HOST` | `127.0.0.1` | Network | Host interface for backend server |
| `BACKEND_PORT` | `8000` | Network | TCP port for backend server |
| `BACKEND_RELOAD` | `false` | Dev | Auto-reload on backend code changes |
| `DATABASE_URL` | `sqlite:///./data/eventsignal.db` | Persistence | SQLAlchemy database connection string |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Security | Allowed frontend origins (no wildcards) |
| `AUTH_SECRET_KEY` | `eventsignal-dev-secret-key-...` | Security (Secret) | HS256 JWT signing key (replace in production) |
| `AUTH_TOKEN_EXPIRE_MINUTES` | `1440` | Security | JWT session validity duration in minutes |
| `DEMO_MODE_ENABLED` | `true` | Presentation | Toggles presentation demo environment |
| `DEMO_USER_EMAIL` | `demo@eventsignal.local` | Presentation | Dedicated demo presenter account email |
| `DEMO_USER_PASSWORD` | `DemoSignal2026!Secure` | Presentation | Dedicated demo presenter account password |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Frontend | Full API URL accessed by the client browser |

---

## 15. Database Architecture & Migrations

- **Engine:** SQLite by default (`data/eventsignal.db`), resolved from repository root.
- **Auto-Initialization:** On application startup, `backend/app/main.py` executes `init_db(engine)`, ensuring tables exist without manual commands.
- **Alembic Migrations:** 7 linear, fully reversible migration revisions (`0001` through `0007`) in `backend/migrations/versions/`.
- **Manual Migration Command:**
  ```bash
  cd backend
  alembic upgrade head
  ```
- **PostgreSQL Readiness:** The ORM code and Alembic revisions are fully backend-agnostic. To target PostgreSQL, change `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname` in `.env`.

---

## 16. Reproducible Verification Guide & Quality Gates

This section documents the authoritative commands used to validate the project, along with a transparent three-state distinction between historical, documented, and freshly verified results.

### 16.1 Three-State Test Classification

To resolve any potential ambiguity across reports, EventSignal documentation strictly categorizes test totals into three verifiable states:

1. **Historical Results:** Totals recorded at previous development checkpoints:
   - *Phase 8 Initial Audit (commit `21e94d0`):* 214 backend tests, 47 frontend tests (261 total).
   - *Phase 8 Closeout Summary:* 226 backend tests, 60 frontend tests (286 total).
2. **Latest Repository-Reported Baseline:** The documented pre-audit total before this testing session: 229 backend tests, 71 frontend tests (300 total).
3. **Freshly Verified Results (Executed on October 25, 2026 at commit `e235ff4`):**
   - **Backend Tests:** **229 collected, 229 passed, 0 failed** across 20 test files in 193.93 s.
   - **Frontend Tests:** **71 collected, 71 passed, 0 failed** across 14 test files in 70.84 s.
   - **TypeScript Typecheck:** **0 errors** (Strict mode clean).
   - **Production Build:** **PASS** (Clean bundle: 556 kB JS, 75.8 kB CSS).
   - **Combined Test Total:** **300 passed / 0 failed** (100% pass rate).

### 16.2 Execution Commands

#### 1. Backend Test Suite (Pytest)
```bash
cd backend
# Windows:
.\.venv\Scripts\pytest
# macOS/Linux:
pytest
```
*Expected output: `229 passed, 3 warnings in ~190s` across 20 test files.*

#### 2. Frontend Test Suite (Vitest)
```bash
cd frontend
npm test
```
*Expected output: `Test Files 14 passed (14), Tests 71 passed (71)` in ~70s.*

#### 3. Strict TypeScript Typecheck
```bash
cd frontend
npm run typecheck
```
*Expected output: Clean exit (code 0) with zero diagnostics.*

#### 4. Frontend Production Build
```bash
cd frontend
npm run build
```
*Expected output: Successful Vite build outputting to `dist/`.*

#### 5. Automated Verification Script
Run all gates in sequence via the repository verification script:
```powershell
python scripts/verify.py --skip-integration
```

---

## 17. Current Implementation Status

All 8 phases of the application architecture are implemented and backed by automated tests:

| Phase | Functional Scope | Key Implemented Capabilities | Verified Tests |
| :--- | :--- | :--- | :--- |
| **Phase 1: Foundation** | Project scaffolding & core API | Typed config, health check, lifespan, CORS validation | 6 tests |
| **Phase 2: Domain Model** | Core ORM schema | SQLAlchemy models, UTCDateTime, constraints, cascades | 21 tests |
| **Phase 3: Opportunity Intake** | Web ingestion & provenance | SSRF defense, 3-stage generic extraction, FieldEvidence | 12 tests |
| **Phase 4: Assessment** | Credibility evaluation | Declarative policy assessment, multi-source conflicts | 57 tests |
| **Phase 5: Workspaces & RBAC** | Multi-tenant security | PBKDF2 auth, signed JWTs, campus units, positions, memberships | 10 tests |
| **Phase 6: Campus Network** | Mentorship & profiles | Student & alumni profiles, privacy gates, HelpOffers | 7 tests |
| **Phase 7: Matching & Legacy** | Gap matching & memory | Deterministic Gap-to-Helper engine, handovers, memories, tasks | 36 tests |
| **Phase 8: Partnerships & Pilot** | Corporate & cross-college | Sponsorships, cross-college campaigns, CSV import, live metrics | 5 tests |
| **Demo Mode & Isolation** | Evaluator presentation | Apex Tech synthetic community, collision defense, 3-mode isolation | 15 tests |
| **Frontend Test Suite** | UI components & clients | Auth landing, feed, network, offers, legacy, partnerships, settings | 71 tests |
| **Total Automated Tests** | — | — | **300 PASS (0 FAIL)** |

---

## 18. Risks, Limitations & Defect Resolutions

### 18.1 Resolution of Historical Test Consistency Risk
- **Former Concern:** An earlier documentation note indicated that historical test totals showed varying figures (214, 226, 229 backend; 47, 60, 71 frontend).
- **Status & Resolution:** **Fully Resolved & Verified.** Independent audit and fresh execution confirm that the variation reflected legitimate test suite growth across development phases (e.g., adding dedicated demo isolation tests, account collision protection tests, SettingsModal tabs, and ErrorBoundary recovery tests). Fresh execution on October 25, 2026 confirms that **229 backend tests** and **71 frontend tests** (**300 total**) execute cleanly with zero failures.

### 18.2 Current Known Limitations
1. **Cloudinary Media Storage Outstanding:** Cloud media storage for event posters and memory photos is not yet built. Avatars use mathematical SVG identicons, and partner logos use inline SVG graphics or standard URLs.
2. **Local SQLite Concurrency:** SQLite is utilized as the default local development database. Deployments serving concurrent multi-institutional traffic must configure `DATABASE_URL` for PostgreSQL.
3. **Synchronous CSV Directory Processing:** The Alumni Directory Import runs synchronously on the API thread. For large institutional rosters (>1,000 rows), processing should be migrated to a background Celery or ARQ worker.
4. **Email & Payment Gateways:** Outbound transactional emails and payment gateway checkouts operate as graceful mock stubs during evaluator demonstrations.

---

## 19. Competition-Specific Contributions (Hacktober HackDays 2026)

This milestone for **Hacktober HackDays 2026 (SheBuilds, Tech for Social Good)** introduces the following contributions:

1. **Tech for Social Good Realignment:** Repositioned EventSignal around civic impact—tackling campus opportunity inequality, preventing mentorship fatigue, and protecting institutional memory.
2. **Exhaustive Codebase Audit:** Conducted an independent audit of all 29 git commits, executing all quality gates and establishing an authoritative baseline of 300 passing automated tests.
3. **Authoritative Cloudinary Integration Audit & Specification:** Verified that Cloudinary is currently **Not Implemented (Level 1)**, preventing inaccurate claims, and authored an enterprise-grade technical specification with signed HMAC workflows in [`docs/HACKTOBER_HACKDAYS_2026.md`](docs/HACKTOBER_HACKDAYS_2026.md).
4. **Unified Documentation & Quick Start Suite:** Introduced a prominent, reproducible Quick Start near the top of the README, overhauled setup instructions, and harmonized verification standards across all reports.

---

## 20. Project References & Credits

### Project Documentation
- [Authoritative MVP Specification](docs/MVP_SPEC.md): Product rules, domain models, and scope boundaries.
- [Competition Implementation Record](docs/HACKTOBER_HACKDAYS_2026.md): HackDays 2026 context, provenance, Cloudinary audit, and timeline.
- [Final Comprehensive Audit Report](docs/FINAL_AUDIT_REPORT.md): Complete technical audit, security findings, and test matrices.
- [Demo Mode Verification Report](docs/DEMO_MODE_AUDIT_REPORT.md): In-depth audit of 3-mode access separation and synthetic datasets.

### Credits & Attribution
- Developed by **Team NeuroIgniter** (Original project for HackShift — Cmd+Shift+Create 2026, IIIT Delhi).
- Continued development & documentation audit by **Meenal Sinha** for **Hacktober HackDays 2026 (SheBuilds, Tech for Social Good)**.
