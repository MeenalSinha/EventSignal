"""SQLAlchemy domain models.

Importing this package registers every model on ``Base.metadata``.

Phase 1 models retained (renamed):
  - Event          → Opportunity
  - SourceReference (foreign key updated to opportunities.id)

Phase 2 models added:
  - FieldEvidence        (source-linked extraction layer)
  - StudentProfile       (self-reported student preferences)
  - AlumniProfile        (self-reported alumni expertise and availability)
  - MatchExplanation     (explainable recommendation records)
  - ConnectionRequest    (purpose-specific professional connections)
"""

from app.models.alumni_profile import AlumniProfile
from app.models.alumni_profile import ProfileVisibility as AlumniProfileVisibility
from app.models.base import Base, TimestampMixin
from app.models.connection_request import ConnectionPurpose, ConnectionRequest, RequestStatus
from app.models.field_evidence import EvidenceStatus, ExtractionMethod, FieldEvidence
from app.models.match_explanation import MatchedEntityType, MatchExplanation
from app.models.opportunity import Opportunity, OpportunityType, ParticipationMode
from app.models.source_reference import SourceReference, SourceType
from app.models.student_profile import ProfileVisibility as StudentProfileVisibility
from app.models.student_profile import StudentProfile

__all__ = [
    "AlumniProfile",
    "AlumniProfileVisibility",
    "Base",
    "ConnectionPurpose",
    "ConnectionRequest",
    "EvidenceStatus",
    "ExtractionMethod",
    "FieldEvidence",
    "MatchExplanation",
    "MatchedEntityType",
    "Opportunity",
    "OpportunityType",
    "ParticipationMode",
    "RequestStatus",
    "SourceReference",
    "SourceType",
    "StudentProfile",
    "StudentProfileVisibility",
    "TimestampMixin",
]
