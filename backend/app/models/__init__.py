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

Phase 6 models added:
  - HelpOffer            (declared assistance by institution members)
  - ConnectionRequest    (purpose-specific connection requests)

Phase 7 models added:
  - StudentNeed          (declared student gap or blocker)
  - HelperMatch          (rule-based match between need and offer)
  - LegacyHandover       (structured knowledge transfer on role transition)
  - EventMemory          (institutional memory for events/opportunities)
  - FollowUpTask         (actionable tasks from handovers and matches)
"""

from app.models.alumni_import import AlumniImportJob, ImportJobStatus
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
from app.models.event_memory import EventMemory
from app.models.field_evidence import EvidenceStatus, ExtractionMethod, FieldEvidence
from app.models.follow_up_task import FollowUpTask, TaskPriority, TaskSource
from app.models.help_offer import (
    HelpOffer,
    HelpOfferAudience,
    HelpOfferDeliveryMode,
    HelpOfferStatus,
)
from app.models.helper_match import HelperMatch, MatchStatus
from app.models.institution import Institution, InstitutionStatus, InstitutionVerificationStatus
from app.models.legacy_handover import HandoverStatus, LegacyHandover
from app.models.match_explanation import MatchedEntityType, MatchExplanation
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.opportunity import Opportunity, OpportunityType, ParticipationMode
from app.models.opportunity_assessment import OpportunityAssessment
from app.models.organizational_unit import OrganizationalUnit
from app.models.promotion_campaign import CampaignStatus, CampaignType, PromotionCampaign
from app.models.source_reference import SourceReference, SourceType
from app.models.sponsorship import (
    PartnerOrganization,
    PartnerVerificationStatus,
    SponsorshipRequest,
    SponsorshipStatus,
    SupportType,
)
from app.models.student_need import NeedStatus, NeedUrgency, StudentNeed
from app.models.student_profile import ProfileVisibility as StudentProfileVisibility
from app.models.student_profile import StudentProfile
from app.models.user import User

__all__ = [
    "AlumniImportJob",
    "AlumniProfile",
    "AlumniProfileVisibility",
    "AssignmentVerificationStatus",
    "AuditLog",
    "Base",
    "CampaignStatus",
    "CampaignType",
    "CampusPositionDefinition",
    "CampusRoleAssignment",
    "ConnectionPurpose",
    "ConnectionRequest",
    "EventMemory",
    "EvidenceStatus",
    "ExtractionMethod",
    "FieldEvidence",
    "FollowUpTask",
    "HandoverStatus",
    "HelpOffer",
    "HelpOfferAudience",
    "HelpOfferDeliveryMode",
    "HelpOfferStatus",
    "HelperMatch",
    "ImportJobStatus",
    "Institution",
    "InstitutionMembership",
    "InstitutionRole",
    "InstitutionStatus",
    "InstitutionVerificationStatus",
    "LegacyHandover",
    "MatchExplanation",
    "MatchStatus",
    "MatchedEntityType",
    "MembershipStatus",
    "NeedStatus",
    "NeedUrgency",
    "Opportunity",
    "OpportunityAssessment",
    "OpportunityType",
    "OrganizationalUnit",
    "ParticipationMode",
    "PartnerOrganization",
    "PartnerVerificationStatus",
    "PromotionCampaign",
    "RequestStatus",
    "SourceReference",
    "SourceType",
    "SponsorshipRequest",
    "SponsorshipStatus",
    "StudentNeed",
    "StudentProfile",
    "StudentProfileVisibility",
    "SupportType",
    "TaskPriority",
    "TaskSource",
    "TimestampMixin",
    "UTCDateTime",
    "User",
    "new_id",
    "utcnow",
]
