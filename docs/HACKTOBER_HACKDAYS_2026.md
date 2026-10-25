# EventSignal — Hacktober HackDays 2026 Project Implementation Record

**Competition:** Hacktober HackDays 2026  
**Track:** SheBuilds — Tech for Social Good  
**Repository:** `MeenalSinha/EventSignal`  
**Tagline:** Evidence Before You Register. Connections Grounded in Purpose.  
**Core Product Workflow:** Discover → Connect → Preserve  
**Date of Audit & Update:** October 25, 2026  

---

## 1. Competition Overview & Social Good Positioning

### 1.1 The Social Good Problem

In modern college ecosystems, career and developmental opportunities—such as hackathons, specialized internships, research fellowships, mutual aid, and alumni mentorship—suffer from severe **information inequality** and **institutional amnesia**:

1. **Fragmented Opportunity Discovery:** Critical notifications and opportunity details are dispersed across informal messaging groups (WhatsApp/Telegram), ephemeral bulletin boards, social media feeds, and unindexed departmental webpages. Students from non-privileged networks or junior cohorts miss critical application windows or fall prey to unverified, low-credibility events.
2. **Superficial, Directory-Style Networking:** Traditional campus alumni portals resemble static phone directories. Students are left to make cold, uncontextualized outreach with no insight into an alumnus's current availability, domain alignment, or willingness to help, resulting in high rejection rates and mentoring fatigue.
3. **Loss of Institutional Memory (Campus Brain Drain):** Student organizations, technical societies, and event committees experience total knowledge loss every 1–2 years as senior organizers graduate. Post-event retrospectives, vendor contacts, sponsor relationships, and leadership handover documentation routinely vanish into personal drives or chat histories.

### 1.2 The EventSignal Solution

EventSignal is engineered as a **Tech for Social Good** platform that democratizes opportunity discovery and builds purpose-grounded institutional continuity for college communities:

- **Discover:** Ingests public opportunity notices and applies generic multi-stage extraction and policy-driven credibility assessments. Every extracted detail (deadlines, prize tiers, fees, eligibility) is backed by field-level provenance (`FieldEvidence`), ensuring students evaluate opportunities based on verified facts rather than promotional claims.
- **Connect:** Replaces static directories with a deterministic, explainable **Gap-to-Helper Matching Engine**. Students declare specific learning or preparation needs; the engine pairs them with verified student peers or alumni mentors with explicit consent gates (`willing_to_connect = true`) and transparent match rationales.
- **Preserve:** Provides an institutional memory layer (**EventSignal Legacy**) where student leaders register official handovers, capture structured post-event retrospectives, and track accountable follow-up commitments, preserving vital institutional knowledge for future cohorts.

---

## 2. Project Provenance & Development History

### 2.1 Provenance
EventSignal originated as a hackathon submission for **HackShift — Cmd+Shift+Create 2026** at IIIT Delhi by Team NeuroIgniter under the theme *Alumni Network & Professional Connections: Building a Network, Not a Directory*. The project established an 8-phase domain model, multi-tenant workspace architecture, explainable matching algorithms, and a synthetic college dataset for evaluator testing.

### 2.2 Continuation for Hacktober HackDays 2026
This repository represents the ongoing development and documentation audit of EventSignal for **Hacktober HackDays 2026 (SheBuilds, Tech for Social Good)**. The focus of this milestone is:
1. Re-anchoring the project architecture around the **Discover → Connect → Preserve** workflow as a civic and educational public good.
2. Conducting an exhaustive, independent code and quality gate audit across all 8 architectural phases.
3. Conducting an authoritative verification of third-party integrations, specifically Cloudinary media storage.
4. Harmonizing historical documentation discrepancies and establishing a verified baseline of automated tests and quality gates.

---

## 3. Scope of Work: Prior Work vs. Competition Milestone

To ensure total transparency for hackathon evaluators and judges, the table below partitions pre-existing capabilities from the Hacktober HackDays 2026 milestone:

| Module / Capability | Status in Repository | Provenance / Milestone |
| :--- | :--- | :--- |
| **Project Foundation (Phase 1)** | Fully implemented & verified | HackShift 2026 (Commit `bfebea9`) |
| **Domain-Model Foundation (Phase 2)** | Fully implemented & verified | HackShift 2026 (Commit `03e0f10`) |
| **Opportunity Intake & Extraction (Phase 3)** | Fully implemented & verified | HackShift 2026 (Commit `caca22a`) |
| **Evidence Assessment Engine (Phase 4)** | Fully implemented & verified | HackShift 2026 (Commits `a71223a`, `cb357ea`) |
| **Workspaces & RBAC Multi-Tenancy (Phase 5)** | Fully implemented & verified | HackShift 2026 (Commit `207d7d6`) |
| **Profiles, Help Offers & Mentorship (Phase 6)** | Fully implemented & verified | HackShift 2026 (Commit `5d7b326`) |
| **Gap-to-Helper Matching & Legacy (Phase 7)** | Fully implemented & verified | HackShift 2026 (Commit `2277cfa`) |
| **Partnerships, Promotion & Pilot Metrics (Phase 8)** | Fully implemented & verified | HackShift 2026 (Commit `21e94d0`) |
| **Authentication-First UI & 3-Mode Access** | Fully implemented & verified | Post-Phase 8 (Commits `be07614`, `548c38f`, `36d3a9c`) |
| **Demo Community Seeding & Isolation** | Fully implemented & verified | Post-Phase 8 (Commits `89b97f9`, `c2f6d67`) |
| **Tech for Social Good Framing & Positioning** | **New Contribution** | **Hacktober HackDays 2026 Milestone** |
| **Exhaustive Code & Quality Audit (300 Tests)** | **New Contribution** | **Hacktober HackDays 2026 Milestone** |
| **Cloudinary Integration Audit & Specification** | **New Contribution** | **Hacktober HackDays 2026 Milestone** |
| **Documentation Realignment (README, Spec, Audits)** | **New Contribution** | **Hacktober HackDays 2026 Milestone** |

---

## 4. Architecture & Technical Decisions

EventSignal utilizes a decoupled, modern web architecture optimized for reliability, auditable business logic, and strict tenant isolation:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  CLIENT LAYER (React 19)                                │
│  App Shell · 3-Column LinkedIn-Style Layout · ErrorBoundary · 3-Mode Access Separation │
│   [Normal Mode (JWT)]       [Guest Mode (Read-Only)]       [Demo Mode (Isolated)]       │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │ HTTP / JSON (Axios-free apiClient)
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                FASTAPI REST API (Python 3.12+)                          │
│  ├── /health                 ├── /profiles              ├── /phase7 (Matching & Legacy) │
│  ├── /auth (PBKDF2/JWT)      ├── /help-offers           ├── /phase8 (Partners & Pilot)  │
│  ├── /opportunities (SSRF)   ├── /institutions (RBAC)   └── /assessment (Rules Engine)  │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               DATABASE & PERSISTENCE LAYER                              │
│         SQLAlchemy 2.0 ORM · Alembic Migrations (7 Linear Chains) · SQLite / Postgres   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Decisions:
1. **FastAPI + Pydantic v2:** Chosen for asynchronous request handling, typed schemas, strict data validation, and automated OpenAPI documentation.
2. **SQLAlchemy 2.0 + Alembic:** Provides declarative ORM models with explicit foreign keys, check constraints, and a strictly linear 7-step migration chain.
3. **Vanilla Tailwind CSS v4 + React 19:** Built with clean, accessible, modern UI components without third-party template bloat. All user avatars use custom SVG identicons generated dynamically from profile names, avoiding external CDN dependencies.
4. **Deterministic Rules Engine Over Black-Box AI:** All opportunity assessments and Gap-to-Helper matches use auditable, rule-based logic with field-by-field explanations rather than opaque neural predictions.

---

## 5. Cloudinary Integration Audit — Critical Finding

### 5.1 Audit Result: **Not Implemented**
A thorough inspection of backend dependencies (`requirements.txt`), frontend packages (`package.json`), environment schemas (`config.py`), database models, API routes, and client services revealed **zero references to Cloudinary** or any third-party media storage SDK.

- **Current Media Handling:**
  - Avatars are rendered purely client-side via mathematical SVG identicons (`Avatar.tsx`).
  - Partner logos and banner graphics are represented by SVG illustrations or URL strings.
  - The only file upload mechanism currently implemented is the **Alumni CSV Directory Import** (`alumni_import.py`), which parses CSV files synchronously for institutional directory onboarding.

### 5.2 Proposed Cloudinary Architecture (Competition Requirement)
To support rich media (event posters, campus memories photo documentation, leadership handover attachments, and sponsor logos) in a production deployment, the proposed Cloudinary integration architecture is specified as follows:

```mermaid
sequenceDiagram
    autonumber
    actor User as Authenticated Student / Organizer
    participant Client as EventSignal Frontend (React)
    participant API as Backend API (FastAPI)
    participant Cloudinary as Cloudinary Media Cloud
    participant DB as SQLite / PostgreSQL Database

    User->>Client: Selects media file (e.g. event poster, memory photo)
    Client->>Client: Client-side validation (MIME type: image/jpeg, image/png; size <= 5MB)
    Client->>API: POST /api/v1/media/sign-upload (institution_id, folder, context)
    Note over API: Verifies tenant membership & RBAC permission
    API->>API: Generates SHA-256 HMAC signature using CLOUDINARY_API_SECRET
    API-->>Client: Returns { signature, timestamp, api_key, cloud_name, folder, tags }
    Client->>Cloudinary: POST https://api.cloudinary.com/v1_1/{cloud_name}/image/upload
    Cloudinary-->>Client: Returns { public_id, secure_url, format, bytes, width, height }
    Client->>API: POST /api/v1/institutions/{id}/opportunities (or /memories) with asset payload
    API->>DB: Stores Cloudinary public_id and secure_url in record metadata
    API-->>Client: Confirms record creation
    Client->>Cloudinary: Requests optimized, responsive transformation URL
```

### 5.3 Security Controls for Planned Implementation:
- **Zero Frontend Secret Exposure:** `CLOUDINARY_API_SECRET` must remain strictly server-side in `.env`. The client receives only a short-lived HMAC signature.
- **Tenant-Scoped Upload Folders:** Assets will be stored under folder paths formatted as `eventsignal/{institution_id}/{resource_type}/{uuid}` to ensure multi-tenant media isolation.
- **Signed Transformations & Strict Delivery:** Media delivery URLs will utilize Cloudinary's secure auto-format (`f_auto`) and quality optimization (`q_auto`) with width caps to protect user bandwidth.

---

## 6. Implementation Timeline (Substantiated by Git History)

The development history of EventSignal is substantiated by the 29 sequential commits in the repository:

| Commit Hash | Component / Focus | Description |
| :--- | :--- | :--- |
| `bfebea9` | Foundation | Phase 1 scaffold, typed settings, health API, verify script |
| `03e0f10` | Domain Model | Phase 2 domain entities: Opportunities, Evidence, Profiles |
| `caca22a` | Intake Engine | Phase 3 opportunity intake pipeline, SSRF defense, extraction |
| `a71223a` · `cb357ea` | Assessment | Phase 4 declarative evidence assessment and conflict resolution |
| `207d7d6` | Workspaces | Phase 5 institutional identity, multi-tenant RBAC, audit log |
| `5d7b326` | Networking | Phase 6 student/alumni profiles, privacy gates, help offers |
| `2277cfa` | Matching & Legacy | Phase 7 Gap-to-Helper matching, handovers, memories, tasks |
| `21e94d0` | Partnerships | Phase 8 sponsorships, cross-college campaigns, alumni import |
| `2e7593a` · `38570af` | Quality & Fixes | Phase 8 completion audit and dependency updates |
| `be07614` · `f1c468e` | UI Realignment | 3-column LinkedIn-style campus networking UI and SVG icon system |
| `548c38f` · `36d3a9c` | Access Modes | Authentication-first landing page with Normal, Guest, and Demo modes |
| `89b97f9` · `d64efee` | Synthetic Campus | Apex Tech 8-module interconnected synthetic dataset with SVG avatars |
| `8a902af` · `c3bcb4f` | UI Polish | Persistent sidebar layout, workspace navigation, auth headers |
| `56241db` · `19ae5ca` | User Features | Search bar popover, section navigation, and Settings modal |
| `deedeef` · `a434419` | Demo Isolation | Real Mode isolation tests, collapsible service status widget |
| `c2f6d67` | Security & Tour | Secured demo endpoints, production credential rules, 5-stage tour |

---

## 7. Testing, Verification, and Quality Gate Audit

A fresh, independent execution of the test suites and static analysis tools was performed on October 25, 2026:

### 7.1 Automated Test Execution Results

| Test Suite | Environment / Command | Tests Executed | Passed | Failed | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend Pytest** | Python 3.14.2 · `pytest` | 229 | **229** | 0 | ✅ **PASS** (193.93 s) |
| **Frontend Vitest** | Node.js · `npm test` | 71 | **71** | 0 | ✅ **PASS** (70.84 s) |
| **Combined Test Total** | Automated regression suite | **300** | **300** | **0** | ✅ **100% PASS** |

> **Resolution of Historical Discrepancy:** Earlier documentation reported 214 tests (initial Phase 8), 226 tests (Phase 8 closeout), and 227 tests (initial demo audit). The current test suite contains **229 backend tests across 20 test files** and **71 frontend tests across 14 test files**, reflecting subsequent coverage added for demo isolation, Settings modal tabs, and collision protection.

### 7.2 Quality Gate & Static Analysis Results

| Quality Gate | Tooling | Target | Result | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **TypeScript Strict Check** | `tsc --noEmit` | `frontend/` | ✅ **0 Errors** | Fully strict mode passes clean |
| **Production Build** | `vite build` | `frontend/` | ✅ **PASS** | Bundle: 556 kB JS, 75.8 kB CSS |
| **Frontend ESLint** | `npm run lint` | `frontend/` | ⚠️ **26 Errors** | React hook cascading set-state & explicit `any` in test/legacy components |
| **Backend MyPy (Strict)** | `mypy` | `backend/app` | ⚠️ **11 Errors** | Type annotation gaps in `demo_service.py`, `profiles.py`, and `auth.py` |
| **Backend Ruff Linter** | `ruff check .` | `backend/` | ⚠️ **268 Errors** | Line length (E501) and unused variables in test files |

---

## 8. Known Limitations & Remaining Risks

1. **Cloudinary Integration Outstanding:** Third-party cloud media storage is not yet implemented. All images are rendered through client-side SVGs or standard URL strings.
2. **Local SQLite Concurrency:** SQLite is currently utilized as the default local store. High-concurrency institutional deployment requires switching `DATABASE_URL` to PostgreSQL.
3. **Synchronous CSV Processing:** The Alumni Directory Import processes rows synchronously on the request thread. Large enterprise CSV files should be offloaded to an asynchronous task queue (e.g., Celery/Redis).
4. **Email & Payment Stubs:** Outbound transactional emails and payment gateway checkouts operate as graceful mock stubs without real third-party dispatch.

---

## 9. References & Documentation Index

- [Project Overview & Setup Guide](../README.md): Primary entry point with architectural summary, quickstart, and workflows.
- [Authoritative MVP Specification](MVP_SPEC.md): Full product specification, domain rules, and scope boundaries.
- [Final Comprehensive Audit Report](FINAL_AUDIT_REPORT.md): Technical audit report covering code health, security, and quality gates.
- [Demo Mode Verification Report](DEMO_MODE_AUDIT_REPORT.md): In-depth audit of 3-mode access separation, tenant isolation, and synthetic datasets.
- [Phase 1 Completion Report](PHASE1_REPORT.md): Historical milestone report for initial repository foundation.
- [Phase 4 Completion Report](PHASE4_REPORT.md): Historical milestone report for evidence assessment engine.
