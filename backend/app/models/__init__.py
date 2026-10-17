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

Phase 4 models added:
  - OpportunityAssessment (evaluation results per opportunity)

Phase 5 models added:
  - User                 (identity, credentials, global roles)
  - Institution          (colleges, workspaces, institutional identity)
  - InstitutionMembership (authorized members, status, RBAC)
  - OrganizationalUnit   (departments, centers, placement/alumni offices)
  - CampusPositionDefinition (official campus positions & leadership)
  - CampusRoleAssignment (time-bounded appointments & verified tenures)
  - AuditLog             (immutable security and governance trail)
"""

from app.models.alumni_profile import AlumniProfile
from app.models.alumni_profile import ProfileVisibility as AlumniProfileVisibility
from app.models.audit_log import AuditLog
from app.models.base import Base, TimestampMixin, UTCDateTime, new_id, utcnow
from app.models.campus_position import (
    AssignmentVerificationStatus,
    CampusPositionDefinition,
    CampusRoleAssignment,
)
from app.models.connection_request import ConnectionPurpose, ConnectionRequest, RequestStatus
from app.models.field_evidence import EvidenceStatus, ExtractionMethod, FieldEvidence
from app.models.institution import Institution, InstitutionStatus, InstitutionVerificationStatus
from app.models.match_explanation import MatchedEntityType, MatchExplanation
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.opportunity import Opportunity, OpportunityType, ParticipationMode
from app.models.opportunity_assessment import OpportunityAssessment
from app.models.organizational_unit import OrganizationalUnit
from app.models.source_reference import SourceReference, SourceType
from app.models.student_profile import ProfileVisibility as StudentProfileVisibility
from app.models.student_profile import StudentProfile
from app.models.user import User

__all__ = [
    "AlumniProfile",
    "AlumniProfileVisibility",
    "AssignmentVerificationStatus",
    "AuditLog",
    "Base",
    "CampusPositionDefinition",
    "CampusRoleAssignment",
    "ConnectionPurpose",
    "ConnectionRequest",
    "EvidenceStatus",
    "ExtractionMethod",
    "FieldEvidence",
    "Institution",
    "InstitutionMembership",
    "InstitutionRole",
    "InstitutionStatus",
    "InstitutionVerificationStatus",
    "MatchExplanation",
    "MatchedEntityType",
    "MembershipStatus",
    "Opportunity",
    "OpportunityAssessment",
    "OpportunityType",
    "OrganizationalUnit",
    "ParticipationMode",
    "RequestStatus",
    "SourceReference",
    "SourceType",
    "StudentProfile",
    "StudentProfileVisibility",
    "TimestampMixin",
    "UTCDateTime",
    "User",
    "new_id",
    "utcnow",
]
