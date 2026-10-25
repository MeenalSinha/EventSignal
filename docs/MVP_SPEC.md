# EventSignal — Authoritative MVP Specification

**Document Version:** 2.0  
**Target Competition:** Hacktober HackDays 2026 — SheBuilds, Tech for Social Good  
**Tagline:** Evidence Before You Register. Connections Grounded in Purpose.  
**Core Product Workflow:** Discover → Connect → Preserve  
**Original Provenance:** HackShift — Cmd+Shift+Create 2026, IIIT Delhi (Team NeuroIgniter)  
**Historical References:** Preserved at [`docs/archive/MVP_SPEC_PHASE1.md`](archive/MVP_SPEC_PHASE1.md) and [`docs/HACKTOBER_HACKDAYS_2026.md`](HACKTOBER_HACKDAYS_2026.md).  

---

## 1. Executive Summary & Social Good Vision

EventSignal is an intelligent campus opportunity discovery and purpose-driven networking platform designed to eliminate information inequality, replace static directories with explainable mentorship matching, and halt institutional knowledge loss across student leadership cycles.

### 1.1 The Social Good Problem

College campuses are vibrant centers of opportunity, but access to these opportunities is highly uneven:

1. **Information Inequality in Opportunity Discovery:** High-impact hackathons, research fellowships, mutual aid grants, and internships are fragmented across disparate WhatsApp groups, Discord servers, personal LinkedIn posts, and unindexed departmental webpages. Junior students and students from outside well-connected social circles frequently miss deadlines or waste effort on unverified, predatory events.
2. **Superficial, Directory-Style Networking:** Conventional university alumni directories function as static rosters. Students make blind outreach attempts with low response rates, while alumni suffer from untargeted, uncontextualized requests that ignore their availability and domain interest.
3. **Institutional Amnesia (Campus Brain Drain):** Student organizations and campus clubs suffer severe operational amnesia every 1–2 years when senior leaders graduate. Retrospectives, vendor contacts, sponsor relationships, and leadership lessons are lost, forcing incoming teams to start from scratch.

### 1.2 Proposed Outcomes & Core Principles

EventSignal addresses these challenges through a unified three-pillar workflow:

```
┌─────────────────┐       ┌─────────────────┐       ┌──────────────────┐
│    DISCOVER     │  ───▶ │     CONNECT     │  ───▶ │     PRESERVE     │
│ Evidence-backed │       │ Purpose-grounded│       │ Institutional    │
│  opportunities  │       │  Gap-to-Helper  │       │  memory & legacy │
└─────────────────┘       └─────────────────┘       └──────────────────┘
```

The platform operates on an unbending architectural principle:

> **"AI extracts. Rules evaluate. Evidence explains. Students decide."**

- **Source Provenance:** Every opportunity requirement, prize, fee, and deadline links back to source evidence (`FieldEvidence`).
- **Honest Uncertainty:** Missing or conflicting details are explicitly surfaced as `NOT_FOUND` or `SOURCES_DISAGREE`—never masked as clean nulls.
- **Zero Hallucination:** The platform never fabricates opportunities, member credentials, verification claims, or match rationales.
- **Privacy by Default:** Student profiles default to private visibility; alumni outreach is strictly blocked unless the mentor has set `willing_to_connect = true`.

---

## 2. Target Users

1. **Students:** Exploring verified hackathons, fellowships, and internships; seeking targeted, purpose-specific guidance from mentors and peers.
2. **Seniors & Alumni Mentors:** Sharing domain knowledge, offering contextual help, and controlling availability via explicit capacity thresholds and consent toggles.
3. **Campus Club Leaders & Organizers:** Managing student organizations, conducting structured handovers, documenting event retrospectives, and tracking follow-up commitments.
4. **Faculty & Institutional Administrators:** Overseeing campus workspaces, monitoring organizational units, appointing official campus positions, and reviewing pilot metrics.
5. **Corporate & Community Partners:** Sponsoring student initiatives via structured prospectuses and cross-college campaigns with conspicuous disclosure.
6. **Hackathon Judges & Evaluators:** Exploring platform workflows via an isolated presentation environment (**Demo Mode**) populated with an interconnected synthetic college community.

---

## 3. Core MVP Capabilities (The 3 Pillars + Institutional Suite)

### Pillar 1: Opportunity Discovery (Discover)
- **Secure Public URL Ingestion:** Validates submitted URLs with robust Server-Side Request Forgery (SSRF) defense (blocking loopback, link-local, and private RFC-1918 IPv4/IPv6 ranges), enforces port allowlists (80/443), and inspects content types.
- **Generic 3-Stage Content Extraction:** Extracts event metadata across JSON-LD structured data, OpenGraph tags, and semantic heuristic trees without hardcoded domain scrapers.
- **Field-Level Provenance (`FieldEvidence`):** Tracks the exact extraction confidence for every critical attribute (`FOUND`, `NOT_FOUND`, `SOURCES_DISAGREE`, `EXTRACTION_FAILED`).
- **Deterministic Deduplication:** Canonicalizes URLs to prevent duplicate listings while permitting administrative `force_refresh`.
- **Declarative Evidence Assessment:** Policy-driven rules engine that evaluates opportunity completeness, verification tiers (High, Moderate, Speculative), and multi-source conflict records.

### Pillar 2: Gap-to-Helper Engine (Connect)
- **Student Need Declaration:** Students articulate specific challenges, required skill domains, urgency, and privacy scope.
- **Deterministic Eligibility & Matching Engine:** Evaluates student needs against available help offers and profiles using an auditable, rule-based scoring engine (no black-box scoring).
- **Grounded Match Explanations (`MatchExplanation`):** Generates transparent explanations showing exactly why a match was recommended (domain overlap, skill synergy, availability).
- **Explicit Help Offers (`HelpOffer`):** Seniors and alumni publish structured offers (Career Advice, Technical Mentorship, Research Support) with explicit delivery formats and monthly capacities.
- **Consent-Gated Connection Routing:** Prevents unprompted outreach by enforcing `willing_to_connect = true` and monthly connection limits.

### Pillar 3: EventSignal Legacy (Preserve)
- **Leadership Handovers (`LegacyHandover`):** Incoming and outgoing student leaders record official transition documents, operational checklists, credentials references, and continuity advice across a 4-state lifecycle (`draft`, `submitted`, `acknowledged`, `superseded`).
- **Institutional Event Memories (`EventMemory`):** Post-event retrospectives capturing event achievements, operational failures, vendor contacts, and institutional lessons learned.
- **Accountable Follow-up Tasks (`FollowUpTask`):** Post-event commitments assigned to responsible parties with priority scoring and completion locks preventing re-opening closed tasks.

### Institutional Operations & Partnerships (Phases 5 & 8)
- **Multi-Tenant Workspaces & RBAC:** Complete tenant isolation across colleges, departments, and official campus positions (`PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `MEMBER`).
- **Partner Verification & Sponsorship Prospectuses:** Tiered sponsorship requests with manual commercial status tracking.
- **Cross-College Promotion Campaigns:** Multi-campus feed broadcasts with conspicuous "Featured — Sponsored" disclosures.
- **Alumni CSV Directory Import:** Institutional CSV onboarding with pre-commit dry-run validation and strict zero-default consent guarantees.
- **Auditable Pilot Analytics:** Real measurable operational metrics derived dynamically from database records.

---

## 4. Application Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React 19 + TypeScript)                  │
│   Vite Bundler · Tailwind CSS v4 · Dynamic SVG Avatars · React ErrorBoundary│
│             3-Column Layout: Profile Sidebar · Main Content · Discovery     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST (apiClient with timeout)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND (FastAPI 0.143)                          │
│   ├── Ingestion Pipeline & SSRF Protection                                  │
│   ├── Declarative Evidence Assessment Engine                                │
│   ├── PBKDF2 Hashing & HS256 JWT Authentication                             │
│   ├── Multi-Tenant Institutional RBAC Middleware                            │
│   ├── Deterministic Gap-to-Helper Matching Engine                           │
│   └── Idempotent Presentation Demo Service                                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ SQLAlchemy 2.0 ORM
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATABASE & STORAGE                              │
│   SQLite (Default Local) / PostgreSQL · 7 Linear Alembic Migrations         │
│   [PLANNED] Cloudinary Cloud Media Service (Signed Uploads, CDN Delivery)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Three-Mode Access Model & Presentation Demo Mode

EventSignal enforces a strict 3-mode access boundary across the entire application:

| Mode | Authentication Mechanism | Tenant Scope | Access Permissions |
| :--- | :--- | :--- | :--- |
| **Normal User Mode** | Email/Password with PBKDF2-SHA256 & JWT | Real institutional workspace | Scoped strictly to user's authorized college; zero visibility into demo records. |
| **Guest Mode** | Unauthenticated ("Continue as Guest") | Global public feed | Read-only browsing of public opportunities; all institutional endpoints return 401/403. |
| **Demo Mode** | Dedicated JWT (`is_demo: true`) | `demo-inst-apex-tech-001` | Isolated to fictional **Apex Institute of Technology**; cannot mutate real data. |

### 5.1 Synthetic College Community (Apex Institute of Technology)
When `DEMO_MODE_ENABLED=true`, the backend automatically seeds a realistic, fully interconnected 8-module dataset:
- **13 Academic Units & Clubs:** Engineering departments, ACM chapter, Robotics club, E-Cell, etc.
- **10 Official Campus Positions:** Club presidents, vice-presidents, and secretaries.
- **30 Synthetic Members:** Fully profiled students, alumni mentors, and faculty advisors.
- **12 Curated Opportunities:** Hackathons, fellowships, and internships with field-level evidence.
- **12 Active Help Offers:** Multi-track mentorship offers.
- **4 Student Needs & 3+ Helper Matches:** Real deterministic match scores with explanations.
- **3 Handovers, 3 Event Memories, 6 Follow-Up Tasks:** Rich institutional continuity records.
- **3 Corporate Partners, 3 Sponsorships, 2 Campaigns, 1 CSV Import Job.**

---

## 6. Cloudinary Media Storage — Implementation Specification

### 6.1 Status: **COMPLETE — LIVE INTEGRATION AND ALL REQUIRED CHECKS VERIFIED**
- **Implementation State:** Full end-to-end integration is implemented and verified with live Cloudinary provider execution (`snwg6j7w`).
- **Backend:** Official `cloudinary>=1.46.0` SDK installed (`cloudinary 1.46.3`); typed settings in `config.py`; `MediaAsset` model and Alembic migration `0008_cloudinary_media_assets.py`; `media_service.py` with HMAC-SHA256 signature generation, asset verification, and transformed delivery URLs; API routes at `/api/v1/media/*`.
- **Frontend:** `mediaService.ts` and `MediaUploadWidget.tsx` supporting drag/drop, progress bar, preview, replace, and remove; integrated into `OpportunityFeed.tsx`, `OpportunityIntakeForm.tsx`, `EventWorkspace.tsx`, and `LegacyMatchingPanel.tsx`.
- **Avatars:** `Avatar.tsx` supports optional `src` image with automatic fallback to deterministic SVG identicons.
- **Graceful Fallback:** When `CLOUDINARY_ENABLED=false` or credentials are unset, media upload widgets display an informative disabled state while non-media workflows operate normally.
- **Verification:** 13 backend unit/integration tests (`tests/test_cloudinary_media.py`), 4 frontend component tests (`MediaUploadWidget.test.tsx`), and full live provider acceptance testing against live account `snwg6j7w` passing clean.

### 6.2 Implemented Cloudinary Architecture & Workflow
For production deployment, Cloudinary provides cloud storage, transformations, and global CDN delivery for event posters and memory photos:

1. **Client Request:** An authorized user selects an image file. The client verifies size (≤ 10 MB) and format (`jpg`, `jpeg`, `png`, `webp`, `gif`).
2. **Signature Request:** The client requests upload authorization from `POST /api/v1/media/authorize-upload`.
3. **Backend Authorization:** The backend verifies institutional membership and RBAC role, then generates an HMAC-SHA256 signature using `CLOUDINARY_API_SECRET` and a strict timestamp. The API secret never leaves the server.
4. **Direct Client Upload:** The client uploads directly to Cloudinary using the signature, public API key, folder, and tags via XMLHttpRequest with upload progress tracking.
5. **Association & Verification:** The client submits the returned `public_id` and metadata to `POST /api/v1/media/complete-upload`. The backend verifies the asset and persists a normalized `MediaAsset` record.
6. **Optimized Delivery:** Transformed URLs (`f_auto,q_auto,w_800,c_limit`) are generated for web display without modifying the original asset.

### 6.3 Acceptance Criteria for Cloudinary Implementation:
- [x] Backend declares `cloudinary>=1.46.0` in `requirements.txt`.
- [x] Server environment schema declares `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET`.
- [x] Server never exposes `CLOUDINARY_API_SECRET` to the frontend or in API responses.
- [x] `POST /api/v1/media/authorize-upload` enforces active institutional membership and tenant scoping.
- [x] Assets are organized under tenant folders: `eventsignal/{institution_id}/{resource_type}/`.
- [x] Delivered media URLs apply `f_auto,q_auto` responsive transformations.
- [x] Automated tests verify signature generation, unauthorized rejection, and URL association (13 backend + 4 frontend tests passing).
- [x] Live provider acceptance executed and verified against live Cloudinary account `snwg6j7w` (direct upload HTTP 200, Admin API verification, CDN delivery HTTP 200, database association, and destroy).

---

## 7. Security, Privacy, and Ethical Constraints

1. **Passwords:** Hashed with PBKDF2-HMAC-SHA256 and unique per-user salts; plaintext passwords are never logged or stored.
2. **Tokens:** Signed with HS256 and validated against server expiration times.
3. **SSRF Hardening:** Private IP networks, link-local addresses, and non-HTTP schemes are rejected at the network layer.
4. **Data Minimization & Privacy:** Student profiles default to `PRIVATE`. Student contact details are never exposed to scrapers or search engines.
5. **Mandatory Consent Gates:** An alumnus or senior can never receive unsolicited connection requests unless `willing_to_connect = true`.
6. **Paid Placement Transparency:** Any sponsored opportunity or cross-college campaign must carry conspicuous disclosure badges (`Featured — Sponsored`).
7. **Demo Metric Honesty:** All metrics in Demo Mode carry explicit `DEMONSTRATION METRICS` labels and make no false claims of commercial revenue.

---

## 8. Explicit Exclusions from the MVP

To maintain high technical rigor, the following capabilities are explicitly excluded from this MVP:

1. **Infinite-Scroll Social Feeds:** No algorithmic engagement traps, vanity likes, or follower counts.
2. **Real-Time WebRTC / WebSocket Chat:** Networking initiates structured contact; real-time messaging is deferred until purpose-grounded connection utility is proven.
3. **Black-Box Neural Ranking:** No unexplainable deep-learning recommendation models; all matching relies on transparent, verifiable rule sets.
4. **Unsanctioned Web Scraping:** No automated scraping of external personal student/alumni directories without explicit institutional consent.
5. **Live Outbound Email / Payment Dispatch in Demo:** Transactional emails and payment transactions operate as graceful mock stubs during evaluator demonstrations.

---

## 9. Automated Quality Gates

All releases and evaluator builds must satisfy the automated quality gates:

| Quality Gate | Tooling | Target | Status |
| :--- | :--- | :--- | :--- |
| **Backend Pytest Suite** | `pytest` | 20 test files in `backend/tests/` | ✅ **229 / 229 Passing** |
| **Frontend Vitest Suite** | `vitest` | 14 test files in `frontend/src/` | ✅ **71 / 71 Passing** |
| **Strict TypeScript Check** | `tsc --noEmit` | Strict mode across `frontend/` | ✅ **0 Errors** |
| **Production Build** | `vite build` | Production minification & assets | ✅ **PASS (556 kB JS)** |
| **Linear Migration Chain** | Alembic | Migrations 0001 through 0007 | ✅ **Linear & Complete** |
| **Tenant & SSRF Isolation** | Pytest security fixtures | Multi-tenant route dependencies | ✅ **Verified Secure** |

> **Note on Test-Status Consistency:** Historical documentation recorded 214 tests (Phase 8 initial commit `21e94d0`) and 226 tests (Phase 8 closeout). The current test suite contains **229 backend tests** and **71 frontend tests** (**300 total passing automated tests**), reflecting phased test expansion for demo isolation, account collision protection, and Settings modal verification. All 300 tests were freshly verified on October 25, 2026.
