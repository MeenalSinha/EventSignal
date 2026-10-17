# EventSignal — Phase 4 Audit and Implementation Report

**Project**: EventSignal  
**Competition**: HackShift — Cmd+Shift+Create 2026, IIIT Delhi  
**Theme**: Alumni Network & Professional Connections: Building a Network, Not a Directory  
**Core Principle**: "AI extracts. Rules evaluate. Evidence explains. Students decide."  
**Milestone**: Phase 4 — Evidence Assessment & Opportunity Evaluation  

---

## 1. Executive Summary

- **Initial State**: Phases 1–3 had established a solid technical foundation (FastAPI + React/Vite/Tailwind), a comprehensive domain model (Opportunity, SourceReference, FieldEvidence, StudentProfile, AlumniProfile), and a safe, real-web opportunity ingestion pipeline with robust SSRF protections. However, Phase 4 (Evidence Assessment & Evaluation) was partially mocked or missing critical features:
  - Assessment weights and thresholds had risk of being hardcoded.
  - Multi-source evaluation was incomplete; secondary sources could not be attached to an existing opportunity via API/UI.
  - Cross-source conflicts lacked structured tracking of competing values and source attribution.
  - Database schema had not yet migrated the necessary columns (`policy_version`, `conflict_details`).
- **Repairs & Enhancements Made**:
  1. Implemented a fully declarative, validated `AssessmentPolicy` (`backend/app/core/assessment_policy.py`) backed by `default_assessment_policy.json` and configurable via `ASSESSMENT_POLICY_PATH`. No hardcoded weights or thresholds.
  2. Enhanced `assessment.py` engine to calculate completeness, evidence quality, and cross-source consistency dynamically from policy and persisted database records (`FieldEvidence`, `SourceReference`).
  3. Added structured conflict detection recording `conflict_details` with competing values, source attribution, and excerpts.
  4. Added multi-source ingestion support (`POST /api/v1/opportunities/{id}/sources`) in both backend and frontend.
  5. Implemented safe, forward-compatible Alembic migrations (`0002_phase4_opportunity_assessments` and `0003_phase4_policy_and_conflicts`).
  6. Updated frontend `AssessmentPanel.tsx` and `EventWorkspace.tsx` to render policy version, score ring, dimension explanations, missing field tags, cross-source conflict cards, and inline source attachment.
  7. Added comprehensive unit, integration, and API tests bringing total backend test count to 159 and frontend test count to 36.
- **Final State**: **PASS**. All 10 quality gates pass cleanly across backend and frontend.

---

## 2. Phase-by-Phase Audit Summary

| Phase | Description | Audit Status | Key Verifications & Repairs |
|---|---|---|---|
| **Phase 1: Project Foundation** | FastAPI app factory, configuration, SQLite DB lifecycle, health check, CORS, React shell, error sanitization. | **PASS** | Strict mypy passed (0 errors across 34 files), Ruff format and lint clean, isolated temp DB tests, health endpoint verified. |
| **Phase 2: Domain Models & Integrity** | Opportunity, SourceReference, FieldEvidence, StudentProfile, AlumniProfile, MatchExplanation, ConnectionRequest. | **PASS** | Validated foreign key relationships, privacy controls (willing_to_connect consent gate), versioned Alembic migration history (`0001` -> `0002` -> `0003`). |
| **Phase 3: Opportunity Intake & Evidence** | Safe URL retrieval, SSRF defense, 3-stage generic extractor, duplicate detection, field-level evidence. | **PASS** | Outbound SSRF protection blocks loopback/private/metadata destinations; honest statuses (`FOUND`, `NOT_FOUND`, `EXTRACTION_FAILED`). |
| **Phase 4: Assessment & Evaluation** | Declarative assessment policy, multi-dimensional scoring, cross-source conflict detection, multi-source attachment UI/API. | **PASS** | Policy-driven assessment engine, persistent assessment records, structured conflict cards with competing source claims, zero hardcoded scores. |

---

## 3. Implementation Details

### A. Declarative Assessment Policy
- **Policy Schema**: Defined in `backend/app/core/assessment_policy.py` using Pydantic v2 with strict validation:
  - Dimension weights (completeness, evidence quality, consistency summing to 1.0).
  - Field groups (`critical`, `important`, `standard`).
  - Opportunity-type applicability rules (e.g. `COMPENSATION` applies to internships/fellowships, `ORGANIZER` applies to all).
  - Method weights (structured = 1.0, opengraph = 0.85, rule_based = 0.7).
  - Evaluation thresholds.
- **Configuration File**: `backend/app/core/default_assessment_policy.json`.

### B. Assessment Engine (`backend/app/services/assessment.py`)
- **Completeness**: Evaluates applicable fields for the opportunity type against persisted `FieldEvidence` records.
- **Evidence Quality**: Evaluates extraction methods, supporting excerpts, and provenance.
- **Cross-Source Consistency**: When multiple sources are attached to an opportunity, normalizes values and checks for agreement or disagreement across sources. If values disagree, constructs a structured `ConflictDetail` capturing the competing values from each source URL.
- **Persistence**: Persists `OpportunityAssessment` records including `policy_version` and `conflict_details`.

### C. Multi-Source Attachment API & UI
- **Backend**: `POST /api/v1/opportunities/{id}/sources` attaches an additional source to an existing opportunity, extracts field evidence tagged with the new `source_id`, appends to the opportunity, and commits safely without overwriting earlier evidence.
- **Frontend**: `EventWorkspace.tsx` offers an inline "+ Add Source" action on each opportunity card, enabling real-time submission of secondary links.
- **Assessment Panel**: `AssessmentPanel.tsx` displays the active `Policy v{version}` tag, dimension score bars, counters snapshot, missing field chips, and expandable cross-source conflict cards.

---

## 4. Quality Gate Verification Results

All checks executed from repository root using `python scripts/verify.py`:

```
=== Backend: ruff lint ===
All checks passed!

=== Backend: ruff format check ===
51 files already formatted

=== Backend: mypy (strict) ===
Success: no issues found in 34 source files

=== Backend: compile check ===

=== Backend: pytest ===
159 passed, 6069 warnings in 14.34s

=== Frontend: TypeScript (strict) ===
> tsc --noEmit (0 errors)

=== Frontend: ESLint ===
> eslint . (0 errors)

=== Frontend: component tests ===
36 passed in 3.94s

=== Frontend: production build ===
✓ built in 210ms

=== Integration: live backend + frontend ===
[PASS] health returns 200 healthy
[PASS] version comes from configuration
[PASS] database component is ok
[PASS] configured SQLite file and directory were created
[PASS] event database starts empty
[PASS] CORS allows the configured origin
[PASS] CORS rejects other origins
[PASS] real React app: connected, empty state, and unreachable-backend state
[PASS] unusable database yields 503 unhealthy
[PASS] failure response exposes no filesystem paths
[PASS] failure response exposes no stack trace
All integration checks passed.

=== Summary ===
[PASS] Backend: ruff lint
[PASS] Backend: ruff format check
[PASS] Backend: mypy (strict)
[PASS] Backend: compile check
[PASS] Backend: pytest
[PASS] Frontend: TypeScript (strict)
[PASS] Frontend: ESLint
[PASS] Frontend: component tests
[PASS] Frontend: production build
[PASS] Integration: live backend + frontend
```

---

## 5. Security and Data Integrity Audits

1. **SSRF Protections**: Verified in `test_retrieval.py` and `test_ingestion_api.py`. Blocks loopback (`127.0.0.1`, `::1`), private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local, cloud metadata IP (`169.254.169.254`), and port anomalies.
2. **Database Integrity**: Preserved existing data and supported migration rollback/upgrade via Alembic `0001`, `0002`, and `0003`.
3. **No Secret Disclosure**: Health and error endpoints never disclose database connection strings, stack traces, or internal server paths.
4. **Zero Production Hardcoding**: No hardcoded opportunities, fake assessment scores, synthetic sources, or fabricated evidence exist in production code paths.
