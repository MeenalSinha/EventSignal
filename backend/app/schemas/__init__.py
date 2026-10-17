"""Pydantic schemas: validated API contracts, separate from ORM models.

Phase 2 note: EventCreate/EventRead are superseded by OpportunityCreate/OpportunityRead.
The old event.py file is retained as docs/archive/schemas_event_phase1.py for reference.
"""

from app.schemas.connection import ConnectionRequestCreate, ConnectionRequestRead
from app.schemas.health import ComponentHealth, HealthResponse, HealthStatus
from app.schemas.ingest import OpportunityIngestRequest, OpportunityIngestResponse
from app.schemas.opportunity import (
    FieldEvidenceRead,
    OpportunityCreate,
    OpportunityList,
    OpportunityRead,
    SourceReferenceCreate,
    SourceReferenceRead,
)
from app.schemas.profile import (
    AlumniProfileCreate,
    AlumniProfileRead,
    StudentProfileCreate,
    StudentProfileRead,
)

__all__ = [
    "AlumniProfileCreate",
    "AlumniProfileRead",
    "ComponentHealth",
    "ConnectionRequestCreate",
    "ConnectionRequestRead",
    "FieldEvidenceRead",
    "HealthResponse",
    "HealthStatus",
    "OpportunityCreate",
    "OpportunityIngestRequest",
    "OpportunityIngestResponse",
    "OpportunityList",
    "OpportunityRead",
    "SourceReferenceCreate",
    "SourceReferenceRead",
    "StudentProfileCreate",
    "StudentProfileRead",
]
