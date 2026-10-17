# EventSignal - MVP Specification (Phase 0 Baseline)

This document preserves the Phase 0 requirements and MVP definition. It is the authoritative product baseline for every later phase. It describes the intended product. It does not describe what is implemented; see the README for the current implementation status.

## 1. Project identity

| Item | Value |
| --- | --- |
| Project name | EventSignal |
| Tagline | Evidence Before You Register. |
| Team | NeuroIgniter |
| Competition | HackShift - Cmd+Shift+Create 2026, IIIT Delhi |
| Online-round problem statement | PS3 - EventRank: Discover What's Worth Attending |
| Category | AI-powered event intelligence, explainable event assessment, evidence tracking, comparison, and personalised recommendations |

The offline-round requirements must be checked against the organisers' latest instructions. Infrastructure built in earlier phases is deliberately reusable and does not assume an offline challenge has been finalised.

## 2. The problem

Students find hackathons, workshops, conferences, competitions and other learning opportunities across many platforms. Information about one event can be scattered across listings, organiser websites, announcements, PDFs, social media posts and registration pages. Students may need to investigate several sources to understand:

- Which essential details are available.
- Whether advertised claims have supporting information.
- Whether different sources disagree.
- Whether the opportunity aligns with their interests and goals.
- What needs to be verified before registration.

Manually comparing several events is time-consuming.

## 3. The proposed solution

EventSignal helps students evaluate, compare and choose events through source-linked evidence and explainable assessments.

**Submit Event -> Extract Information -> Trace Evidence -> Assess -> Compare -> Make an Informed Decision**

A student submits an event URL or supplies event information. The application extracts relevant information, associates findings with their sources, identifies missing or inconsistent details, assesses relevance to the student's goals, and presents results in an explainable format. The system distinguishes between information found in a source, conclusions derived from that information, and details that remain uncertain.

## 4. Core product principle

> **AI extracts. Rules evaluate. Evidence explains. Students decide.**

- An event is never classified as fraudulent merely because information is missing.
- Sources, organiser credentials, prizes, reviews, deadlines and verification results are never fabricated.
- An event is never described as verified unless an actual verification process supports that specific claim.

These principles guide architecture, data models, API contracts and assessment logic.

## 5. Target users

Primary: college students, hackathon participants, students exploring technical workshops and competitions, students evaluating conferences and research opportunities, and students looking for skill-building events.

Potential future: career and placement cells, student clubs and societies, educational institutions, and organisers who want to improve the completeness of what they publish.

## 6. Feature priorities

| ID | Feature | Priority |
| --- | --- | --- |
| F01 | Event URL submission and manual text-input fallback | Critical |
| F02 | Structured event information extraction | Critical |
| F03 | Source-linked evidence records | Critical |
| F04 | Information completeness assessment | Critical |
| F05 | Evidence availability assessment | Critical |
| F06 | Comparison of at least two events | Critical |
| F07 | Goal-based relevance assessment | High |
| F08 | Cross-source consistency checks | High |
| F09 | Explainable findings | Critical |
| F10 | Reliable error handling without fabricated results | Critical |

## 7. Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, TypeScript |
| Styling | Tailwind CSS |
| Backend | Python, FastAPI |
| API and domain validation | Pydantic |
| Database | SQLite |
| ORM | SQLAlchemy |
| Backend configuration | Pydantic Settings |
| HTTP client for future ingestion | HTTPX |
| HTML parsing for future ingestion | BeautifulSoup |
| AI extraction (later phase) | Configurable LLM API |
| Assessment engine (later phase) | Transparent Python rules |
| Backend testing | Pytest |
| Version control | Git |

PostgreSQL, Redis, Celery, Kubernetes, microservices and other additional infrastructure are not introduced without a demonstrated need.

## 8. Event information schema

| Field | Description |
| --- | --- |
| `event_name` | Published event name |
| `organizer` | Named organiser, if available |
| `start_date` | Published start date |
| `end_date` | Published end date, if applicable |
| `registration_deadline` | Registration closing date, if published |
| `submission_deadline` | Project or deliverable deadline, if applicable |
| `venue` | Published venue, if available |
| `mode` | Online, offline or hybrid, if stated |
| `eligibility` | Published participation requirements |
| `participation_fee` | Published fee information, if stated |
| `agenda` | Published activities or event format |
| `prizes_and_benefits` | Advertised prizes, mentorship, certificates or other benefits |
| `registration_url` | Registration link, if available |
| `source_urls` | Sources associated with the event |

A field being important to check does not mean every event has a value for it. The application must distinguish between missing values, inapplicable fields, extraction failures and conflicting values.

## 9. Evidence system requirements

The evidence system associates extracted information with:

- The relevant event.
- The field being supported.
- The extracted value.
- The source URL or other source reference, where applicable.
- A supporting excerpt, when available.
- The retrieval timestamp, when applicable.
- The extraction method.
- The evidence or extraction status.
- Any applicable validation issues.

Evidence statuses: found in source; supported by multiple sources; needs verification; not found; sources disagree; not assessed.

These statuses describe the application's evidence state. They do not establish that an event is legitimate or fraudulent.

## 10. Assessment dimensions (later phases)

1. Information completeness.
2. Evidence availability.
3. Cross-source consistency.
4. Goal-based relevance.
5. Assessment uncertainty.

### Proposed completeness weights

These are a proposed baseline for a future phase, not an implemented scoring system. When implemented, weights and applicability rules must be configurable and documented, never embedded as unexplained constants.

| Information group | Proposed weight |
| --- | ---: |
| Event name | 10 |
| Organizer | 10 |
| Event dates | 15 |
| Registration or submission deadlines | 15 |
| Eligibility | 15 |
| Venue or participation mode | 10 |
| Participation fee or cost information | 10 |
| Agenda or event rules | 10 |
| Registration or official information link | 5 |
| **Total** | **100** |

## 11. MVP testing requirements

The eventual MVP is tested for: complete event information; missing deadlines; failed source retrieval; conflicting information across sources; sparse event information; goal-based relevance; unsafe URLs; partial extraction failures.

## 12. Scope exclusions for Phase 1

General-purpose web crawling, event-page scraping, OCR or document extraction, LLM integration, credibility scoring, event comparison logic, user authentication, user profiles and preferences, review analysis, payment processing, production deployment, sophisticated analytics, and large-scale infrastructure.

## 13. Phase roadmap

| Phase | Scope | Status |
| --- | --- | --- |
| 0 | Requirements and MVP definition | Complete (this document) |
| 1 | Project foundation | Implemented and verified |
| 2 | Event ingestion and information extraction (F01, F02) | Not started |
| 3 | Source-linked evidence records (F03, F09) | Not started |
| 4 | Assessment engine (F04, F05, F08) | Not started |
| 5 | Comparison and goal-based relevance (F06, F07) | Not started |

Phases 2 onward are a planning outline derived from the feature priorities, not a committed schedule.

## 14. Phase 1 acceptance criteria

Phase 1 is complete when all of the following are implemented and verified.

**Project foundation:** repository inspected before modification; structure established; frontend and backend configured; dependency manifests created; environment configuration implemented; `.env.example` created; `.gitignore` configured; README written; this specification preserved.

**Backend:** FastAPI starts; configuration loads through the settings module; SQLAlchemy connection works; event and source-reference models exist; ORM tables initialise; no event data is seeded; the health endpoint returns actual status; database failures are never reported as healthy; Pydantic schemas are separate from ORM models; automated tests pass.

**Frontend:** React app starts; strict TypeScript passes; Tailwind works; the shell renders with correct branding and tagline; health is fetched from the real API; loading, success and error states work; the empty state shows no fictional events; the production build succeeds; tests pass.

**Integration:** the frontend talks to the real backend; the API base URL is configured; CORS is configurable; API failures are handled; database health is checked; no fake success responses; full integration tested.

**Configuration and security:** no hardcoded secrets; no environment-specific values scattered through code; local database and `.env` ignored by Git; no fictional runtime event data; test fixtures isolated; configuration errors understandable; error responses expose no secrets or stack traces.

**Documentation:** setup instructions accurate and tested; test commands run; production build run; limitations documented; implemented and unimplemented features clearly distinguished.
