# EventSignal — MVP Specification (Phase 8: Partnerships, Cross-College Promotion, Pilot & Release Readiness)

> **Theme**: Alumni Network & Professional Connections
> **Emphasis**: Building a Network, Not a Directory
> **Tagline**: Evidence Before You Register. Connections Grounded in Purpose.
> **Team**: NeuroIgniter
> **Competition**: HackShift — Cmd+Shift+Create 2026, IIIT Delhi
> **Historical Reference**: The original EventRank specification is preserved at [`docs/archive/MVP_SPEC_PHASE1.md`](docs/archive/MVP_SPEC_PHASE1.md).

---

## 1. Executive Summary & Vision

EventSignal is an intelligent professional networking platform connecting students with relevant opportunities and the alumni and mentors who can help them pursue those opportunities.

Unlike static directories, EventSignal operates on a structured, intent-driven workflow:

```
Student Intent
    -> Relevant Opportunities
    -> Relevant Alumni and Mentors
    -> Explainable Recommendations
    -> Purpose-Specific Connection Requests
```

The platform's distinguishing principle:

> **"AI extracts. Rules evaluate. Evidence explains. Students decide."**

- Opportunities have source-linked information wherever applicable.
- Unknown or conflicting information is explicitly identifiable (never presented as clean nulls).
- The platform never invents qualifications, evidence, verification results, opportunities, alumni identities, or recommendation explanations.
- In Demo Mode, synthetic data is clearly identified and isolated from real institutional data.

---

## 2. Target Users

### Primary Users
1. **Students**: Seeking career, research, internship, and learning opportunities, along with alumni who share relevant expertise and can provide guidance.
2. **Alumni and Mentors**: Willing to offer domain expertise, review opportunities, provide industry insight, and mentor students within explicit availability and consent boundaries.

### Additional Stakeholders
3. **Institutional Administrators**: Managing college workspaces, RBAC memberships, campus positions, and organizational units.
4. **Recruiters & Founding Partners**: Sponsoring opportunities or seeking talent aligned with specific challenges.
5. **Faculty & Advisors**: Guiding research, institutional collaborations, and mentoring programs.
6. **Demo Presenters / Evaluators**: Using the dedicated Demo Mode to explore the full platform experience without creating real data.

---

## 3. User Journeys

### 3.1 Primary Student Journey
1. **Describe Intent & Goals**: Declare interests, skills, career aspirations, and preferred opportunity types (self-reported, private by default).
2. **Discover Opportunities**: Explore hackathons, fellowships, internships, and research calls with transparent evidence statuses for key requirements and dates.
3. **Understand Match Rationale**: Read explainable recommendations grounded in actual profile attributes (skill overlap, declared domain interest).
4. **Find Relevant Alumni/Mentors**: Discover alumni with relevant experience or active help offers related to that opportunity or field.
5. **Evaluate Relevance**: Review explainable match notes without fabricated pedigree or claims.
6. **Initiate Purpose-Specific Connections**: Send structured connection requests respecting alumni consent thresholds.

### 3.2 Primary Alumni Journey
1. **Declare Expertise & Domain**: Provide self-reported professional domains, industry background, and skills.
2. **Set Mentoring Availability & Consent**: Set `willing_to_connect` (defaults to `false`) and define monthly connection thresholds.
3. **Control Visibility**: Choose profile visibility (`PRIVATE`, `STUDENTS_ONLY`, or `PUBLIC`).
4. **Publish Help Offers**: Create configurable `HelpOffer` records with topics, delivery mode, and capacity.
5. **Manage Connection Requests**: Receive, review, accept, or decline purpose-specific requests with contextual messages.

### 3.3 Demo Presenter Journey
1. **Sign In via Demo Mode Tab**: Use dedicated credentials (`demo@eventsignal.local`).
2. **Explore Dashboard**: View amber demo banner, college workspace, and synthetic opportunity feed.
3. **Navigate All 8 Modules**: Every platform section is pre-populated with realistic synthetic data.
4. **Demonstrate Key Workflows**: Ingest an opportunity URL, run the matching engine, review a legacy handover, and inspect a sponsorship prospectus.
5. **Reset Data**: Restore pristine demo state via the reset API or by restarting the backend.

---

## 4. Core MVP Capabilities

| Capability | Description | Phase |
| --- | --- | --- |
| **Opportunity Intake** | Secure public URL ingestion, SSRF protection, redirect verification, body-limit streaming | Phase 3 |
| **Generic Content Extraction** | Multi-stage extraction (JSON-LD, OpenGraph, semantic heuristics) without site-specific hardcoding | Phase 3 |
| **Evidence Collection** | Field-level provenance (`FieldEvidence`) separating `FOUND`, `NOT_FOUND`, `SOURCES_DISAGREE`, and `EXTRACTION_FAILED` | Phase 3 |
| **Duplicate Prevention** | Deterministic URL normalization preventing silent duplicates; `force_refresh` to re-extract | Phase 3 |
| **Opportunity Discovery** | Filter and explore opportunities with date/mode validation and evidence tier cards | Phase 3 |
| **Evidence Assessment Engine** | Declarative policy-driven scoring (completeness, evidence quality, source consistency) | Phase 4 |
| **Multi-Source Evaluation** | Cross-source conflict detection, competing values analysis, and source attribution | Phase 4 |
| **Institutional Workspaces & RBAC** | Multi-college workspaces, tenant isolation, official campus positions, and immutable audit logging | Phase 5 |
| **Student Profiles** | Self-reported skills, interests, and preferences with server-enforced privacy controls | Phase 6 |
| **Alumni Profiles** | Expertise, mentoring topics, and explicit consent gates (`willing_to_connect`) | Phase 6 |
| **Explicit Help Offers** | Configurable help offers, lifecycle management (`active`, `paused`, `archived`), and discovery | Phase 6 |
| **Campus Network Discovery** | Privacy-aware, institution-scoped discovery of people and active help offers | Phase 6 |
| **Purpose-Specific Help Requests** | Structured requests on published help offers with introductory intent | Phase 6 |
| **Gap-to-Helper Matching** | Student needs, deterministic eligibility filtering, grounded explanations, and honest no-match handling | Phase 7 |
| **EventSignal Legacy & Handovers** | Preserving institutional memory across leadership transitions, retrospective event memories, and follow-up commitments | Phase 7 |
| **Sponsorship Facilitation** | Structured event sponsorship prospectuses, honest partner verification, and manual commercial terms tracking | Phase 8 |
| **Cross-College Promotion** | Configurable pricing packages, multi-campus feed targeting, admin review, and conspicuous "Featured — Sponsored" disclosure | Phase 8 |
| **Approved Alumni Directory Import** | Secure CSV import, pre-commit dry-run validation, and strict zero-default consent guarantees | Phase 8 |
| **Pilot Evaluation & Operational Metrics** | Live measurable indicators from stored records across all 8 modules with `DEMONSTRATION METRICS` disclosure in Demo Mode | Phase 8 |
| **Dedicated Demo Mode** | Isolated synthetic college community, dedicated credentials, automatic seeding, idempotent reset, and strict tenant isolation | Phase 8 |

---

## 5. Demo Mode Specification

### 5.1 Design Principles

- Demo Mode is an **isolated presentation environment**, not a bypass of authentication or authorization.
- All demo data flows through the **same backend API endpoints**, ORM models, and database tables as real data; there are no mock responses or hardcoded frontend arrays.
- Synthetic records are clearly separated from real institutional data by `institution_id = "demo-inst-apex-tech-001"` and `extra_data["is_demo"] = true`.
- **Pilot and sponsorship metrics** displayed in Demo Mode are explicitly badged as `DEMONSTRATION METRICS` and are calculated from the persisted synthetic records — they make no claim of real commercial revenue.

### 5.2 Three-Mode Access Model

| Mode | Entry Point | Authentication | Data Access |
| --- | --- | --- | --- |
| **Normal User Mode** | Email/password on Normal tab | Full JWT auth | Scoped to real institutional workspaces (no demo records) |
| **Guest Mode** | "Continue as Guest" | None | Public opportunity listings only; institutional endpoints return HTTP 401/403 |
| **Demo Mode** | Dedicated Demo tab | Full JWT auth (`is_demo: true`) | Isolated to `demo-inst-apex-tech-001`; cannot access or modify real tenant records |

### 5.3 Demo Mode Activation

Controlled by environment variables in `.env`:

```env
DEMO_MODE_ENABLED=true
DEMO_USER_EMAIL=demo@eventsignal.local
DEMO_USER_PASSWORD=<strong local secret — never commit>
```

When `DEMO_MODE_ENABLED=false`:
- The Demo tab is hidden on the landing page.
- Demo login attempts return `403 Forbidden`.
- Demo seeding/reset endpoints are disabled.
- No demo records are seeded on startup.

### 5.4 Synthetic College Community

The demo institution **Apex Institute of Technology** (`demo-inst-apex-tech-001`) is populated by `backend/app/services/demo_service.py` on application startup:

- **13 Academic Units & Clubs**: CSE, AI/DS, ECE, Design, Management departments; ACM Chapter, Robotics Club, Photography Society, Entrepreneurship Cell, Research Cell, Cultural Committee, Sports Council, Alumni Relations Cell.
- **10 Official Campus Positions**: Club Presidents, Vice-Presidents, and Secretary roles with institutional appointment records.
- **30 Synthetic Members**: Students across all years, student leaders, alumni mentors, and faculty advisors — each with a full profile, tags, and help offers where applicable.
- **12 Curated Opportunities**: Hackathons, fellowships, internships, and research calls with structured `FieldEvidence` and `OpportunityAssessment` records.
- **12 Active Help Offers**: Career guidance, technical mentorship, and research support offers across peer and alumni categories.
- **4 Student Needs**: Declared challenges with eligibility-filtered helper matches and deterministic score explanations.
- **3 Legacy Handovers**: Leadership transition records from outgoing to incoming club officers.
- **3 Event Memories**: Institutional retrospectives capturing lessons, successes, and institutional knowledge.
- **6 Follow-up Tasks**: Post-event commitments with priority classification and status tracking.
- **3 Verified Partner Organizations**: Corporate sponsors with brand verification and prospectuses.
- **3 Sponsorship Requests**: Tiered financial or in-kind sponsorship requests at varying lifecycle states.
- **2 Cross-College Promotion Campaigns**: Active and approved promotional campaigns with "Featured — Sponsored" disclosure.
- **1 Alumni Directory Import Job**: Committed CSV import record demonstrating the dry-run → commit workflow.

### 5.5 Seeding & Reset

- Seeding is triggered automatically on backend startup when `DEMO_MODE_ENABLED=true`.
- The `DemoService.seed_demo_environment(db, settings)` method uses **fixed UUIDs** and `db.merge()` to ensure fully idempotent behaviour — rerunning the seed updates existing records rather than creating duplicates.
- Safe reset: `POST /api/v1/auth/demo/reset` deletes records scoped to `demo-inst-apex-tech-001` only, with no risk of touching real institutional data.

---

## 6. Evidence, Privacy, and Security Rules

1. **Missing Information Is Not Fraud**: An opportunity missing a registration fee or venue is recorded as `NOT_FOUND` or `NEEDS_VERIFICATION`, never labelled fraudulent.
2. **Conflicting Claims Must Be Explicit**: Where multiple sources disagree (e.g., different prize amounts or deadlines), status `SOURCES_DISAGREE` is recorded.
3. **Extraction Failures Recorded Honestly**: Technical errors during extraction are recorded as `EXTRACTION_FAILED`, never disguised as successful nulls.
4. **No Verification Without Process**: Profiles and opportunities remain unverified unless an authentic audit process was executed.
5. **Self-Reported vs. Independently Verified**: Clear distinction in schemas and data presentation at all times.
6. **No Synthetic Hallucinations in Production**: The system never fabricates real alumni profiles, qualifications, or opportunities. Synthetic data exists only in the isolated Demo Mode environment.
7. **Explicit Connection Consent**: Connection requests cannot be routed to alumni profiles unless `willing_to_connect = true`.
8. **Data Minimization**: Collect only what is necessary for matching and connection purposes.
9. **Private By Default**: Student profiles default to `PRIVATE` visibility.
10. **Clear Data Boundaries**: Explicit separation between source-published information, user-declared preferences, rule assessments, and unresolved uncertainty.
11. **Demo Data Disclosure**: All demo metric panels and promotional materials carry a visible `DEMONSTRATION DATA` or `DEMONSTRATION METRICS` badge. No false commercial claims are made.

---

## 7. Explicit Exclusions from Initial MVP

To preserve engineering focus and integrity, the following are explicitly out of scope:

1. **Full Social Networking Feed**: No endless scroll, timeline feeds, vanity likes, or algorithmic engagement loops.
2. **Real-Time Instant Messaging**: Connections initiate contact; real-time chat infrastructure is deferred until core match value is proven.
3. **Unnecessary Microservices**: Monolithic, well-structured FastAPI service with clean modular boundaries.
4. **Opaque Recommendation Models**: No black-box neural ranking without human-auditable reasons; all recommendations link to explicit attributes.
5. **Mass Web Scraping of Personal Profiles**: No scraping of LinkedIn or personal student/alumni records without explicit user submission.
6. **Unverified Credential Claims**: Self-reported claims are explicitly identified as self-reported; no fake "verified" badges.
7. **Premature Production Infrastructure**: Lightweight, isolated local database (SQLite/Alembic) until deployment scale necessitates external clusters.
8. **Automated External Email in Demo Mode**: No live SMTP dispatch during demo presentations; email integrations are graceful stubs.

---

## 8. Quality Gates

All capabilities must satisfy the following automated quality gates before release:

| Gate | Tooling | Latest Result |
| --- | --- | --- |
| Backend unit & integration tests | Pytest | ✅ 226 tests passing |
| Backend demo integration tests | Pytest (`test_demo.py`) | ✅ 12 tests passing (community, isolation, idempotency, sponsorships, matching) |
| Frontend component & service tests | Vitest | ✅ 60 tests passing (12 files) |
| TypeScript strict type checking | `tsc --noEmit` | ✅ 0 errors |
| Frontend production build | Vite | ✅ 0 errors, ~501 kB JS bundle |
| SSRF protection | Manual + test | ✅ Private IP ranges blocked |
| Tenant isolation | Pytest security fixtures | ✅ Cross-tenant access returns HTTP 403 |
| Demo mode isolation | Pytest + manual | ✅ Demo records invisible to normal tenants |
