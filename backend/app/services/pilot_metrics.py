"""Pilot & release evaluation metrics service for EventSignal Phase 8.

Calculates observable operational metrics from actual persisted database records.
No simulated data or fabricated counts.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alumni_import import AlumniImportJob
from app.models.base import utcnow
from app.models.event_memory import EventMemory
from app.models.follow_up_task import FollowUpTask
from app.models.helper_match import HelperMatch, MatchStatus
from app.models.institution import Institution
from app.models.legacy_handover import HandoverStatus, LegacyHandover
from app.models.membership import InstitutionMembership, InstitutionRole
from app.models.opportunity import Opportunity
from app.models.opportunity_assessment import OpportunityAssessment
from app.models.promotion_campaign import CampaignStatus, PromotionCampaign
from app.models.sponsorship import SponsorshipRequest, SponsorshipStatus
from app.models.student_need import NeedStatus, StudentNeed
from app.schemas.phase8 import PilotMetricsResponse


class PilotMetricsService:
    @staticmethod
    def calculate_metrics(db: Session, institution_id: str) -> PilotMetricsResponse:
        inst = db.scalar(select(Institution).where(Institution.id == institution_id))
        if not inst:
            raise LookupError(f"Institution '{institution_id}' not found")

        # 1. Opportunities & Evidence Assessments
        total_opps = (
            db.scalar(
                select(func.count(Opportunity.id)).where(
                    Opportunity.institution_id == institution_id
                )
            )
            or 0
        )
        assessments = db.scalars(
            select(OpportunityAssessment)
            .join(Opportunity, Opportunity.id == OpportunityAssessment.opportunity_id)
            .where(Opportunity.institution_id == institution_id)
        ).all()

        opp_stats = {
            "total": total_opps,
            "assessed": len(assessments),
            "high_evidence": sum(1 for a in assessments if a.overall_score >= 0.8),
            "moderate_evidence": sum(1 for a in assessments if 0.5 <= a.overall_score < 0.8),
            "low_evidence": sum(1 for a in assessments if a.overall_score < 0.5),
        }

        # 2. Student Needs
        needs = db.scalars(
            select(StudentNeed).where(StudentNeed.institution_id == institution_id)
        ).all()
        need_stats = {
            "total": len(needs),
            "open": sum(1 for n in needs if n.status == NeedStatus.OPEN),
            "matched": sum(1 for n in needs if n.status == NeedStatus.MATCHED),
            "resolved": sum(1 for n in needs if n.status == NeedStatus.RESOLVED),
        }

        # 3. Helper Matches
        need_ids = [n.id for n in needs]
        if need_ids:
            matches = db.scalars(select(HelperMatch).where(HelperMatch.need_id.in_(need_ids))).all()
        else:
            matches = []

        match_stats = {
            "total_evaluated": len(matches),
            "accepted": sum(1 for m in matches if m.status == MatchStatus.ACCEPTED),
            "pending": sum(1 for m in matches if m.status == MatchStatus.PROPOSED),
            "dismissed": sum(1 for m in matches if m.status == MatchStatus.DISMISSED),
        }

        # 4. Legacy Knowledge
        handovers = db.scalars(
            select(LegacyHandover).where(LegacyHandover.institution_id == institution_id)
        ).all()
        memories_count = (
            db.scalar(
                select(func.count(EventMemory.id)).where(
                    EventMemory.institution_id == institution_id
                )
            )
            or 0
        )
        tasks = db.scalars(
            select(FollowUpTask).where(FollowUpTask.institution_id == institution_id)
        ).all()

        legacy_stats = {
            "handovers_total": len(handovers),
            "handovers_acknowledged": sum(
                1 for h in handovers if h.status == HandoverStatus.ACKNOWLEDGED
            ),
            "memories_total": memories_count,
            "tasks_total": len(tasks),
            "tasks_completed": sum(1 for t in tasks if t.is_completed),
        }

        # 5. Sponsorship Requests
        sponsorships = db.scalars(
            select(SponsorshipRequest).where(SponsorshipRequest.institution_id == institution_id)
        ).all()
        sponsor_stats = {
            "requests_total": len(sponsorships),
            "draft": sum(1 for s in sponsorships if s.status == SponsorshipStatus.DRAFT),
            "submitted": sum(1 for s in sponsorships if s.status == SponsorshipStatus.SUBMITTED),
            "under_review": sum(
                1 for s in sponsorships if s.status == SponsorshipStatus.UNDER_REVIEW
            ),
            "accepted": sum(1 for s in sponsorships if s.status == SponsorshipStatus.ACCEPTED),
            "declined": sum(1 for s in sponsorships if s.status == SponsorshipStatus.DECLINED),
            "closed": sum(1 for s in sponsorships if s.status == SponsorshipStatus.CLOSED),
        }

        # 6. Cross-College Campaigns
        campaigns = db.scalars(
            select(PromotionCampaign).where(
                PromotionCampaign.source_institution_id == institution_id
            )
        ).all()
        campaign_stats = {
            "campaigns_created": len(campaigns),
            "campaigns_approved": sum(
                1 for c in campaigns if c.status in (CampaignStatus.APPROVED, CampaignStatus.ACTIVE)
            ),
            "campaigns_active": sum(1 for c in campaigns if c.status == CampaignStatus.ACTIVE),
        }

        # 7. Alumni Network & Import Jobs
        memberships = db.scalars(
            select(InstitutionMembership).where(
                InstitutionMembership.institution_id == institution_id
            )
        ).all()
        import_jobs = db.scalars(
            select(AlumniImportJob).where(AlumniImportJob.institution_id == institution_id)
        ).all()

        alumni_stats = {
            "total_members": len(memberships),
            "student_count": sum(1 for m in memberships if m.role == InstitutionRole.STUDENT),
            "alumni_count": sum(1 for m in memberships if m.role == InstitutionRole.ALUMNI),
            "import_jobs_count": len(import_jobs),
            "imported_rows_accepted": sum(j.accepted_rows for j in import_jobs),
        }

        readiness = (
            "ready_for_controlled_pilot" if len(memberships) > 0 else "pilot_validation_pending"
        )

        return PilotMetricsResponse(
            institution_id=inst.id,
            institution_name=inst.name,
            generated_at=utcnow(),
            opportunities=opp_stats,
            student_needs=need_stats,
            helper_matches=match_stats,
            legacy_knowledge=legacy_stats,
            sponsorship=sponsor_stats,
            cross_college_promotion=campaign_stats,
            alumni_network=alumni_stats,
            readiness_status=readiness,
            notes=[
                "Metrics reflect strictly persisted and auditable database records.",
                (
                    "Sponsorship revenue records agreed commercial terms, "
                    "not automated payment verification."
                ),
                "Cross-college campaigns preserve distinct 'Featured — Sponsored' disclosures.",
            ],
        )
