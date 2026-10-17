# EventSignal - MVP Specification (Adapted for Phase 2: Alumni Network & Professional Connections)

> **Theme**: Alumni Network & Professional Connections  
> **Emphasis**: Building a Network, Not a Directory  
> **Tagline**: Evidence Before You Register. Connections Grounded in Purpose.  
> **Team**: NeuroIgniter  
> **Competition**: HackShift - Cmd+Shift+Create 2026, IIIT Delhi  
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

The platform's distinguishing principle remains:

> **"AI extracts. Rules evaluate. Evidence explains. Students decide."**

- Opportunities have source-linked information wherever applicable.
- Unknown or conflicting information remains explicitly identifiable.
- The platform never invents qualifications, evidence, verification results, opportunities, alumni identities, or recommendation explanations.

---

## 2. Target Users

### Primary Users
1. **Students**: Seeking career, research, internship, and learning opportunities, along with alumni who share relevant expertise and can provide guidance.
2. **Alumni and Mentors**: Willing to offer domain expertise, review opportunities, provide industry insight, and mentor students within explicit availability and consent boundaries.

### Potential Future Participants
3. **Recruiters & Founders**: Sponsoring opportunities or looking for talent aligned with specific challenges.
4. **Faculty & Educational Institutions**: Guiding research, institutional collaborations, and career mentoring programs.

---

## 3. User Journeys

### 3.1 Primary Student Journey
1. **Describe Intent & Goals**: Declare interests, skills, career aspirations, and preferred opportunity types (self-reported, private by default).
2. **Discover Opportunities**: Explore opportunities (hackathons, fellowships, internships, research) with transparent evidence statuses for key requirements and dates.
3. **Understand Match Rationale**: Read explainable recommendations grounded in actual profile attributes (e.g., skill overlap, declared domain interest).
4. **Find Relevant Alumni/Mentors**: Discover alumni who have relevant experience or offer mentoring related to that opportunity or field.
5. **Evaluate Relevance**: Review explainable match notes without fabricated pedigree or claims.
6. **Initiate Purpose-Specific Connections**: Send targeted, structured connection requests (e.g. career guidance, opportunity-specific advice) respecting alumni consent.

### 3.2 Primary Alumni Journey
1. **Declare Expertise & Domain**: Provide self-reported professional domains, industry background, and skills.
2. **Set Mentoring Availability & Consent**: Declare mentoring interests, set `willing_to_connect` (defaults to False until active consent is given), and define monthly connection thresholds.
3. **Control Visibility**: Choose profile visibility (`private`, `students_only`, or `public`).
4. **Manage Connection Requests**: Receive, review, accept, or decline purpose-specific connection requests with clear contextual messages.

---

## 4. Core MVP Capabilities

| Capability | Description | Phase |
| --- | --- | --- |
| **Opportunity Intake** | Secure public URL ingestion, SSRF protection, redirect verification, body limit streaming | Implemented in Phase 3 |
| **Generic Content Extraction** | Multi-stage extraction (JSON-LD, OpenGraph, semantic heuristics) without hardcoding | Implemented in Phase 3 |
| **Evidence Collection** | Field-level provenance (`FieldEvidence`) separating FOUND, NOT_FOUND, and technical failures | Implemented in Phase 3 |
| **Duplicate Prevention** | Deterministic URL normalization preventing silent duplicates with force_refresh | Implemented in Phase 3 |
| **Opportunity Discovery** | Filter and explore opportunities with date/mode validation and evidence cards | Implemented in Phase 3 |
| **Student Profiles** | Self-reported skills, interests, and preferences with strict privacy controls | Implemented in Phase 2; UI in Phase 4 |
| **Alumni Profiles** | Expertise, mentoring interests, and explicit consent gates (`willing_to_connect`) | Implemented in Phase 2; UI in Phase 4 |
| **Explainable Matching** | Traceable match explanations (`MatchExplanation`) referencing specific profile attributes | Implemented in Phase 2; Scorer in Phase 4 |
| **Purpose-Specific Connections** | Non-spam connection requests (`ConnectionRequest`) requiring explicit purpose categories | Implemented in Phase 2; UI in Phase 4 |

---

## 5. Explicit Exclusions from Initial MVP

To preserve engineering focus and integrity, the following are explicitly out of scope for the initial MVP:

1. **Full Social Networking Feed**: No endless scroll, timeline feeds, vanity likes, or algorithmic engagement loops.
2. **Real-Time Instant Messaging**: Connections initiate contact; real-time chat infrastructure is deferred to prevent complexity before core match value is proven.
3. **Unnecessary Microservices**: Monolithic, well-structured FastAPI service with clean modular boundaries.
4. **Opaque Recommendation Models**: No black-box neural ranking without human-auditable reasons; all recommendations must link to explicit attributes.
5. **Mass Web Scraping of Personal Profiles**: No scraping of LinkedIn or personal student/alumni records without explicit user submission.
6. **Unverified Credential Claims**: Self-reported claims are explicitly identified as self-reported; no fake "verified" badges.
7. **Premature Production Infrastructure**: Retain lightweight, isolated local database (SQLite/Alembic) until deployment scale necessitates external clusters.

---

## 6. Evidence, Privacy, and Security Rules

1. **Missing Information Is Not Fraud**: An opportunity missing a registration fee or organizer venue is recorded as `NOT_FOUND` or `NEEDS_VERIFICATION`, never branded as fraudulent.
2. **Conflicting Claims Must Be Explicit**: Where multiple sources disagree (e.g., different prize amounts or deadlines), status `SOURCES_DISAGREE` is recorded.
3. **Extraction Failures Recorded Honestly**: Technical errors during extraction are recorded as `EXTRACTION_FAILED`, never disguised as successful nulls.
4. **No Verification Without Process**: Profiles and opportunities remain unverified unless an authentic audit process was executed.
5. **Self-Reported vs. Independently Verified**: Clear distinction in schemas and data presentation.
6. **No Synthetic Hallucinations**: System never fabricates real alumni profiles, qualifications, or opportunities.
7. **Explicit Connection Consent**: Connection requests cannot be routed to alumni profiles unless `willing_to_connect = True`.
8. **Data Minimization**: Collect only what is necessary for matching and connection purposes.
9. **Private By Default**: Student profiles default to `PRIVATE` visibility.
10. **Clear Data Boundaries**: Distinct separation between source-published information, user-declared preferences, rule assessments, and unresolved uncertainty.
