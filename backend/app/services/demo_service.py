"""Demo environment provisioning, isolated dataset seeding, and reset service.

Provides a dedicated, presentation-ready demonstration environment for EventSignal:
1. Provisions a dedicated demo account with isolated credentials.
2. Seeds clearly identified, synthetic demonstration records for all 8 product areas:
   - College Workspaces (Demo Institute of Technology)
   - Campus Network (synthetic student & alumni profiles)
   - Opportunities with source-linked evidence & deterministic assessments
   - Help Offers (mock interviews, system design, resume reviews)
   - Gap-to-Helper Matching (realistic student need with evaluated matches)
   - EventSignal Legacy (leadership handovers, event memories, follow-up tasks)
   - Sponsorship & Partnerships (verified partners, sponsorship prospectuses)
   - Cross-College Promotion & Pilot Metrics (active campaigns, persisted metrics)
3. Ensures strict idempotency: re-running does not duplicate records or overwrite production.
4. Allows safe resetting of demo records without touching real institutional data.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.models.alumni_profile import AlumniProfile, ProfileVisibility as AlumniVisibility
from app.models.campus_position import (
    AssignmentVerificationStatus,
    CampusPositionDefinition,
    CampusRoleAssignment,
)
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
from app.models.institution import (
    Institution,
    InstitutionStatus,
    InstitutionVerificationStatus,
)
from app.models.legacy_handover import HandoverStatus, LegacyHandover
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.opportunity import Opportunity, OpportunityType, ParticipationMode
from app.models.opportunity_assessment import OpportunityAssessment
from app.models.organizational_unit import OrganizationalUnit
from app.models.promotion_campaign import (
    CampaignStatus,
    CampaignType,
    PromotionCampaign,
)
from app.models.source_reference import SourceReference, SourceType
from app.models.sponsorship import (
    PartnerOrganization,
    PartnerVerificationStatus,
    SponsorshipRequest,
    SponsorshipStatus,
    SupportType,
)
from app.models.student_need import NeedStatus, NeedUrgency, StudentNeed
from app.models.student_profile import ProfileVisibility as StudentVisibility, StudentProfile
from app.models.user import User

logger = logging.getLogger(__name__)

# Deterministic IDs for demo assets so repeated seeds remain strictly idempotent
DEMO_INSTITUTION_ID = "demo-inst-apex-tech-001"
DEMO_INSTITUTION_SLUG = "demo-apex-tech"
DEMO_USER_ID = "demo-user-presenter-001"
DEMO_STUDENT_USER_ID = "demo-user-student-002"
DEMO_ALUMNI_USER_ID = "demo-user-alumni-003"
DEMO_PARTNER_ORG_ID = "demo-partner-cloud-001"
DEMO_OPP_1_ID = "demo-opp-hackathon-001"
DEMO_OPP_2_ID = "demo-opp-internship-002"
DEMO_NEED_ID = "demo-need-gsoc-001"
DEMO_OFFER_1_ID = "demo-offer-mentorship-001"
DEMO_OFFER_2_ID = "demo-offer-review-002"
DEMO_HANDOVER_ID = "demo-handover-acm-001"
DEMO_MEMORY_ID = "demo-memory-hackathon-001"
DEMO_TASK_1_ID = "demo-task-sponsor-001"
DEMO_TASK_2_ID = "demo-task-budget-002"
DEMO_SPONSOR_REQ_ID = "demo-sponsorship-001"
DEMO_CAMPAIGN_ID = "demo-campaign-001"


class DemoService:
    @staticmethod
    def is_demo_user(user: User) -> bool:
        """Check whether a user instance is the designated demonstration account."""
        return bool(user.extra_data and user.extra_data.get("is_demo") is True)

    @staticmethod
    def is_demo_dataset_seeded(db: Session) -> bool:
        """Check whether the isolated demo institution and workspace are present."""
        inst = db.scalar(select(Institution).where(Institution.id == DEMO_INSTITUTION_ID))
        user = db.scalar(select(User).where(User.id == DEMO_USER_ID))
        return inst is not None and user is not None

    @staticmethod
    def provision_demo_account(db: Session, settings: Settings) -> User:
        """Create or update the dedicated demo user account using settings credentials."""
        if not settings.demo_mode_enabled:
            raise RuntimeError("Demo mode is disabled in application settings.")

        email = (settings.demo_user_email or "demo@eventsignal.local").strip().lower()
        password = settings.demo_user_password or "DemoSignal2026!Secure"

        existing = db.scalar(select(User).where(User.id == DEMO_USER_ID))
        if not existing:
            # Check by email in case of ID mismatch
            existing = db.scalar(select(User).where(User.email == email))

        if existing:
            existing.email = email
            existing.hashed_password = hash_password(password)
            existing.full_name = "Alex Vance (Demo Presenter)"
            existing.is_active = True
            existing.is_superuser = False  # Demo account is NOT platform superuser
            existing.extra_data = {"is_demo": True, "role_context": "demo_lead_presenter"}
            db.flush()
            return existing

        user = User(
            id=DEMO_USER_ID,
            email=email,
            hashed_password=hash_password(password),
            full_name="Alex Vance (Demo Presenter)",
            is_active=True,
            is_superuser=False,
            extra_data={"is_demo": True, "role_context": "demo_lead_presenter"},
        )
        db.add(user)
        db.flush()
        return user

    @staticmethod
    def seed_demo_environment(db: Session, settings: Settings) -> dict[str, Any]:
        """Seed a complete, presentation-ready isolated demonstration environment."""
        if not settings.demo_mode_enabled:
            raise RuntimeError("Cannot seed demo environment: demo_mode_enabled is False.")

        now = datetime.now(UTC)

        # 1. Dedicated Demo Account
        demo_user = DemoService.provision_demo_account(db, settings)

        # 2. Supporting Synthetic Users
        student_user = db.scalar(select(User).where(User.id == DEMO_STUDENT_USER_ID))
        if not student_user:
            student_user = User(
                id=DEMO_STUDENT_USER_ID,
                email="riya.patel.demo@apextech.edu",
                hashed_password=hash_password("SyntheticStudent2026!"),
                full_name="Riya Patel (Synthetic Student)",
                is_active=True,
                is_superuser=False,
                extra_data={"is_demo": True, "synthetic": True},
            )
            db.add(student_user)
            db.flush()

        alumni_user = db.scalar(select(User).where(User.id == DEMO_ALUMNI_USER_ID))
        if not alumni_user:
            alumni_user = User(
                id=DEMO_ALUMNI_USER_ID,
                email="marcus.chen.demo@alumni.apextech.edu",
                hashed_password=hash_password("SyntheticAlumni2026!"),
                full_name="Marcus Chen (Synthetic Alumni)",
                is_active=True,
                is_superuser=False,
                extra_data={"is_demo": True, "synthetic": True},
            )
            db.add(alumni_user)
            db.flush()

        # 3. Dedicated Demo College Workspace
        demo_inst = db.scalar(select(Institution).where(Institution.id == DEMO_INSTITUTION_ID))
        if not demo_inst:
            demo_inst = Institution(
                id=DEMO_INSTITUTION_ID,
                name="Apex Institute of Technology (Demo Workspace)",
                slug=DEMO_INSTITUTION_SLUG,
                domain="apextech.edu",
                description="Demonstration collegiate workspace featuring active clubs, verified tenures, and peer mentorship.",
                location="Bengaluru, Karnataka, India",
                contact_email="workspace-demo@apextech.edu",
                website_url="https://demo.apextech.edu",
                status=InstitutionStatus.ACTIVE,
                verification_status=InstitutionVerificationStatus.VERIFIED,
                verified_at=now - timedelta(days=90),
                extra_data={"is_demo": True, "campus_tier": "Engineering & Innovation"},
            )
            db.add(demo_inst)
            db.flush()

        # 4. Memberships for Demo Users in Demo College
        memberships = {
            DEMO_USER_ID: InstitutionRole.INSTITUTION_ADMIN,
            DEMO_STUDENT_USER_ID: InstitutionRole.STUDENT,
            DEMO_ALUMNI_USER_ID: InstitutionRole.ALUMNI,
        }
        for uid, role in memberships.items():
            m = db.scalar(
                select(InstitutionMembership).where(
                    InstitutionMembership.institution_id == DEMO_INSTITUTION_ID,
                    InstitutionMembership.user_id == uid,
                )
            )
            if not m:
                m = InstitutionMembership(
                    institution_id=DEMO_INSTITUTION_ID,
                    user_id=uid,
                    role=role,
                    status=MembershipStatus.ACTIVE,
                )
                db.add(m)
        db.flush()

        # 5. Organizational Units & Positions
        unit_cse = db.scalar(
            select(OrganizationalUnit).where(
                OrganizationalUnit.institution_id == DEMO_INSTITUTION_ID,
                OrganizationalUnit.code == "CSE",
            )
        )
        if not unit_cse:
            unit_cse = OrganizationalUnit(
                institution_id=DEMO_INSTITUTION_ID,
                name="Department of Computer Science & Engineering",
                code="CSE",
                unit_type="department",
                description="Undergraduate and research department in computing sciences.",
                contact_email="cse@apextech.edu",
            )
            db.add(unit_cse)
            db.flush()

        pos_lead = db.scalar(
            select(CampusPositionDefinition).where(
                CampusPositionDefinition.institution_id == DEMO_INSTITUTION_ID,
                CampusPositionDefinition.title == "ACM Student Chapter Chair",
            )
        )
        if not pos_lead:
            pos_lead = CampusPositionDefinition(
                institution_id=DEMO_INSTITUTION_ID,
                unit_id=unit_cse.id,
                title="ACM Student Chapter Chair",
                description="Lead organizer for collegiate hackathons, workshops, and guest lectures.",
            )
            db.add(pos_lead)
            db.flush()

        # Verified appointment for presenter
        role_assign = db.scalar(
            select(CampusRoleAssignment).where(
                CampusRoleAssignment.institution_id == DEMO_INSTITUTION_ID,
                CampusRoleAssignment.user_id == DEMO_USER_ID,
                CampusRoleAssignment.position_id == pos_lead.id,
            )
        )
        if not role_assign:
            role_assign = CampusRoleAssignment(
                institution_id=DEMO_INSTITUTION_ID,
                position_id=pos_lead.id,
                user_id=DEMO_USER_ID,
                unit_id=unit_cse.id,
                verification_status=AssignmentVerificationStatus.VERIFIED,
                start_date=now - timedelta(days=180),
                end_date=now + timedelta(days=180),
                is_active=True,
            )
            db.add(role_assign)

        # 6. Student & Alumni Profiles
        demo_student_profile = db.scalar(
            select(StudentProfile).where(
                StudentProfile.institution_id == DEMO_INSTITUTION_ID,
                StudentProfile.user_id == DEMO_USER_ID,
            )
        )
        if not demo_student_profile:
            demo_student_profile = StudentProfile(
                user_id=DEMO_USER_ID,
                institution_id=DEMO_INSTITUTION_ID,
                display_name="Alex Vance",
                skills="React, Python, FastAPI, PostgreSQL, Docker",
                interests="Distributed Systems, Cloud Platforms, Open Source",
                career_goals="Open Source Fellowships, Cloud Infrastructure, Full-Stack Dev",
                visibility=StudentVisibility.PUBLIC,
                extra_data={
                    "headline": "Pre-Final Year CSE · Distributed Systems & AI",
                    "degree_level": "B.Tech Computer Science",
                    "graduation_year": 2027,
                },
            )
            db.add(demo_student_profile)

        alumni_prof = db.scalar(
            select(AlumniProfile).where(
                AlumniProfile.institution_id == DEMO_INSTITUTION_ID,
                AlumniProfile.user_id == DEMO_ALUMNI_USER_ID,
            )
        )
        if not alumni_prof:
            alumni_prof = AlumniProfile(
                user_id=DEMO_ALUMNI_USER_ID,
                institution_id=DEMO_INSTITUTION_ID,
                display_name="Marcus Chen (Alumni '23)",
                professional_domain="Distributed Systems & Cloud Computing",
                years_experience=3,
                skills="Go, Kubernetes, gRPC, Distributed Caching, System Design",
                industry="Cloud Computing & Infrastructure",
                mentoring_interests="Career Guidance, System Design Reviews, Resume Feedback",
                willing_to_connect=True,
                monthly_connection_limit=5,
                visibility=AlumniVisibility.PUBLIC,
                extra_data={
                    "current_title": "Software Engineer II",
                    "current_organization": "Google Cloud Platforms",
                },
            )
            db.add(alumni_prof)
        db.flush()

        # 7. Curated Demo Opportunities with Evidence & Assessments
        opp_hackathon = db.scalar(select(Opportunity).where(Opportunity.id == DEMO_OPP_1_ID))
        if not opp_hackathon:
            opp_hackathon = Opportunity(
                id=DEMO_OPP_1_ID,
                title="Apex Innovators Hackathon 2026 (Demo)",
                opportunity_type=OpportunityType.HACKATHON,
                organizer="ACM Apex Student Chapter",
                start_date=now + timedelta(days=20),
                end_date=now + timedelta(days=22),
                registration_deadline=now + timedelta(days=14),
                submission_deadline=now + timedelta(days=22),
                location="Bengaluru & Hybrid Online",
                mode=ParticipationMode.HYBRID,
                eligibility="Open to all verified college students across India",
                skills_required="Web Development, Machine Learning, Cloud Services",
                compensation="USD 5,000 Total Prize Pool + Cloud Credits",
                application_url="https://demo.apextech.edu/events/innovators-2026",
                institution_id=DEMO_INSTITUTION_ID,
            )
            db.add(opp_hackathon)
            db.flush()

            # Source Reference
            src_hack = SourceReference(
                opportunity_id=opp_hackathon.id,
                source_type=SourceType.ORGANIZER_WEBSITE,
                url="https://demo.apextech.edu/events/innovators-2026",
                title="Official Hackathon Announcement Page",
            )
            db.add(src_hack)
            db.flush()

            # Evidence records
            db.add_all([
                FieldEvidence(
                    opportunity_id=opp_hackathon.id,
                    source_id=src_hack.id,
                    field_name="title",
                    extracted_value="Apex Innovators Hackathon 2026 (Demo)",
                    supporting_excerpt="Apex Innovators Hackathon 2026: Official Announcement",
                    evidence_status=EvidenceStatus.FOUND,
                    extraction_method=ExtractionMethod.STRUCTURED,
                ),
                FieldEvidence(
                    opportunity_id=opp_hackathon.id,
                    source_id=src_hack.id,
                    field_name="registration_deadline",
                    extracted_value=(now + timedelta(days=14)).isoformat(),
                    supporting_excerpt="Registration Deadline: 14 days from announcement",
                    evidence_status=EvidenceStatus.FOUND,
                    extraction_method=ExtractionMethod.STRUCTURED,
                ),
                FieldEvidence(
                    opportunity_id=opp_hackathon.id,
                    source_id=src_hack.id,
                    field_name="compensation",
                    extracted_value="USD 5,000 Total Prize Pool + Cloud Credits",
                    supporting_excerpt="Total cash prize pool and sponsor cloud compute credits",
                    evidence_status=EvidenceStatus.FOUND,
                    extraction_method=ExtractionMethod.RULE_BASED,
                ),
            ])

            # Persisted Assessment
            assess_hack = OpportunityAssessment(
                opportunity_id=opp_hackathon.id,
                overall_score=0.92,
                completeness_score=0.95,
                evidence_quality_score=0.90,
                consistency_score=0.92,
                completeness_explanation="All critical fields (title, organizer, deadlines, eligibility, prize pool) published and extracted.",
                evidence_quality_explanation="Supported by verified institutional subdomain with high structured confidence.",
                consistency_explanation="No contradictory dates or criteria across verified references.",
                missing_critical_fields=[],
                missing_optional_fields=[],
                ambiguous_fields=[],
                conflicting_fields=[],
                conflict_details=[],
                limitations="Demonstration opportunity for campus event validation.",
                total_fields_assessed=8,
                fields_found_count=8,
                fields_not_found_count=0,
                fields_failed_count=0,
            )
            db.add(assess_hack)

        opp_intern = db.scalar(select(Opportunity).where(Opportunity.id == DEMO_OPP_2_ID))
        if not opp_intern:
            opp_intern = Opportunity(
                id=DEMO_OPP_2_ID,
                title="Summer Cloud Systems Research Internship (Demo)",
                opportunity_type=OpportunityType.INTERNSHIP,
                organizer="Center for Distributed Computing",
                start_date=now + timedelta(days=60),
                end_date=now + timedelta(days=120),
                registration_deadline=now + timedelta(days=30),
                location="Apex Research Labs, Bengaluru",
                mode=ParticipationMode.OFFLINE,
                eligibility="3rd or 4th year undergraduate students in CS/IT",
                skills_required="C++, Rust, Linux Kernel, Distributed Systems",
                compensation="Stipend: INR 45,000 / month",
                application_url="https://demo.apextech.edu/research/internships-2026",
                institution_id=DEMO_INSTITUTION_ID,
            )
            db.add(opp_intern)
            db.flush()

            src_intern = SourceReference(
                opportunity_id=opp_intern.id,
                source_type=SourceType.DOCUMENT,
                url="https://demo.apextech.edu/research/internships-2026",
                title="Research Laboratory Circular",
            )
            db.add(src_intern)
            db.flush()

            assess_intern = OpportunityAssessment(
                opportunity_id=opp_intern.id,
                overall_score=0.88,
                completeness_score=0.90,
                evidence_quality_score=0.86,
                consistency_score=0.90,
                completeness_explanation="Essential internship terms, stipend amount, and department eligibility criteria verified.",
                evidence_quality_explanation="Directly linked to department research lab circular.",
                consistency_explanation="No conflicting application deadlines identified.",
                missing_critical_fields=[],
                missing_optional_fields=["submission_deadline"],
                ambiguous_fields=[],
                conflicting_fields=[],
                conflict_details=[],
                limitations="Demonstration opportunity for institutional research intake.",
                total_fields_assessed=7,
                fields_found_count=6,
                fields_not_found_count=1,
                fields_failed_count=0,
            )
            db.add(assess_intern)

        # 8. Help Offers (from Alumni and Mentor)
        offer_sys = db.scalar(select(HelpOffer).where(HelpOffer.id == DEMO_OFFER_1_ID))
        if not offer_sys:
            offer_sys = HelpOffer(
                id=DEMO_OFFER_1_ID,
                user_id=DEMO_ALUMNI_USER_ID,
                institution_id=DEMO_INSTITUTION_ID,
                title="System Design & Cloud Architecture Mentoring",
                category="career_guidance",
                description="1-on-1 sessions discussing distributed storage, latency trade-offs, and microservice architectures.",
                applicable_skills="System Design, Cloud Infrastructure, Kubernetes, Go",
                intended_audience=HelpOfferAudience.STUDENTS_ONLY.value,
                delivery_mode=HelpOfferDeliveryMode.REMOTE.value,
                status=HelpOfferStatus.ACTIVE.value,
                extra_data={"max_recipients": 4},
            )
            db.add(offer_sys)

        offer_res = db.scalar(select(HelpOffer).where(HelpOffer.id == DEMO_OFFER_2_ID))
        if not offer_res:
            offer_res = HelpOffer(
                id=DEMO_OFFER_2_ID,
                user_id=DEMO_ALUMNI_USER_ID,
                institution_id=DEMO_INSTITUTION_ID,
                title="GSoC & Open Source Proposal Reviews",
                category="project_review",
                description="Actionable feedback on open-source project proposals, contribution hygiene, and code PRs.",
                applicable_skills="Open Source, Git, Proposal Writing, Python, FastAPI",
                intended_audience=HelpOfferAudience.ALL.value,
                delivery_mode=HelpOfferDeliveryMode.REMOTE.value,
                status=HelpOfferStatus.ACTIVE.value,
                extra_data={"max_recipients": 5},
            )
            db.add(offer_res)
        db.flush()

        # 9. Student Need & Matching Engine Result
        need_gsoc = db.scalar(select(StudentNeed).where(StudentNeed.id == DEMO_NEED_ID))
        if not need_gsoc:
            need_gsoc = StudentNeed(
                id=DEMO_NEED_ID,
                student_profile_id=demo_student_profile.id,
                institution_id=DEMO_INSTITUTION_ID,
                title="Proposal Feedback for Cloud Native Open Source Fellowship",
                category="project_review",
                description="Need guidance on structuring architecture proposal and benchmark tests for a Python and FastAPI microservices project.",
                urgency=NeedUrgency.HIGH,
                preferred_delivery_mode="remote",
                status=NeedStatus.MATCHED,
            )
            db.add(need_gsoc)
            db.flush()

            # Persist real match evaluated by matching engine rules
            match_res = HelperMatch(
                need_id=need_gsoc.id,
                help_offer_id=DEMO_OFFER_2_ID,
                institution_id=DEMO_INSTITUTION_ID,
                score=0.92,
                scorer_version="1.0.0",
                status=MatchStatus.PROPOSED,
                rule_results=[
                    {
                        "rule": "Category alignment",
                        "weight": 0.45,
                        "contribution": 0.45,
                        "details": "Exact match on category 'project_review'.",
                    },
                    {
                        "rule": "Delivery mode alignment",
                        "weight": 0.20,
                        "contribution": 0.20,
                        "details": "Both prefer remote delivery.",
                    },
                    {
                        "rule": "Skill keyword overlap",
                        "weight": 0.25,
                        "contribution": 0.17,
                        "details": "High keyword overlap on Python, FastAPI, and proposals.",
                    },
                    {
                        "rule": "Urgency boost",
                        "weight": 0.10,
                        "contribution": 0.10,
                        "details": "Need marked as high urgency.",
                    },
                ],
                summary_explanation="High category alignment, matching remote delivery mode, and strong overlap in Python & proposal review skills.",
            )
            db.add(match_res)

        # 10. Legacy Handover & Memories
        handover_acm = db.scalar(select(LegacyHandover).where(LegacyHandover.id == DEMO_HANDOVER_ID))
        if not handover_acm:
            handover_acm = LegacyHandover(
                id=DEMO_HANDOVER_ID,
                institution_id=DEMO_INSTITUTION_ID,
                position_id=pos_lead.id,
                outgoing_user_id=DEMO_USER_ID,
                incoming_user_id=DEMO_STUDENT_USER_ID,
                title="ACM Student Chapter Leadership Handover 2025-2026",
                accomplishments_summary="Organized 4 campus hackathons, scaled membership to 350+ active participants, and secured 3 corporate sponsors.",
                ongoing_work="Transitioning cloud lab servers to institutional cluster; annual flagship hackathon sponsorship drive.",
                key_contacts=[
                    {"name": "Dean of Student Affairs", "email": "admin@apextech.edu", "role": "Faculty Advisor"},
                    {"name": "Industry Liaison Office", "email": "corporate@apextech.edu", "role": "Sponsorships"},
                ],
                lessons_learned="Always finalize venue electrical backups at least 10 days before hackathon commencement.",
                recommended_first_steps="Meet with department head in first week of August; initiate sponsor prospectus outreach.",
                status=HandoverStatus.SUBMITTED,
            )
            db.add(handover_acm)

        memory_hack = db.scalar(select(EventMemory).where(EventMemory.id == DEMO_MEMORY_ID))
        if not memory_hack:
            memory_hack = EventMemory(
                id=DEMO_MEMORY_ID,
                institution_id=DEMO_INSTITUTION_ID,
                opportunity_id=DEMO_OPP_1_ID,
                author_user_id=DEMO_USER_ID,
                title="Apex Hackathon 2025 Retrospective",
                what_worked="High mentor engagement, automated PR verification using CI/CD test runners.",
                what_did_not_work="Order catering buffer meals 2 hours ahead of dinner rush to prevent lines.",
                attendance_notes="280 registered delegates, 65 team submissions",
                outcome_summary="12 projects deployed to production staging; 3 received seed sponsor interest.",
                tags=["hackathon", "systems", "open-source", "mentorship"],
                extra_data={
                    "event_year": 2025,
                    "recommended_budget": "INR 3,50,000 for 300 delegates.",
                },
            )
            db.add(memory_hack)

        # 11. Follow-Up Tasks
        task_1 = db.scalar(select(FollowUpTask).where(FollowUpTask.id == DEMO_TASK_1_ID))
        if not task_1:
            task_1 = FollowUpTask(
                id=DEMO_TASK_1_ID,
                institution_id=DEMO_INSTITUTION_ID,
                creator_user_id=DEMO_USER_ID,
                assignee_user_id=DEMO_USER_ID,
                title="Send prospectus to CloudScale Systems for 2026 Hackathon",
                description="Follow up on preliminary sponsorship interest and deliver tiered benefits prospectus.",
                due_date=now + timedelta(days=7),
                priority=TaskPriority.HIGH,
                source=TaskSource.HANDOVER,
                handover_id=DEMO_HANDOVER_ID,
                is_completed=False,
            )
            db.add(task_1)

        task_2 = db.scalar(select(FollowUpTask).where(FollowUpTask.id == DEMO_TASK_2_ID))
        if not task_2:
            task_2 = FollowUpTask(
                id=DEMO_TASK_2_ID,
                institution_id=DEMO_INSTITUTION_ID,
                creator_user_id=DEMO_USER_ID,
                assignee_user_id=DEMO_USER_ID,
                title="Audit server cluster allocation for hackathon staging",
                description="Verify compute quotas with Department IT coordinator.",
                due_date=now + timedelta(days=12),
                priority=TaskPriority.MEDIUM,
                source=TaskSource.MANUAL,
                is_completed=False,
            )
            db.add(task_2)

        # 12. Partnerships & Sponsorships
        partner_org = db.scalar(select(PartnerOrganization).where(PartnerOrganization.id == DEMO_PARTNER_ORG_ID))
        if not partner_org:
            partner_org = PartnerOrganization(
                id=DEMO_PARTNER_ORG_ID,
                institution_id=DEMO_INSTITUTION_ID,
                name="CloudScale Infrastructure Labs (Demo Partner)",
                industry="Cloud Computing & Developer Tools",
                contact_name="Elena Rostova",
                contact_email="partnerships@cloudscale-demo.io",
                website_url="https://cloudscale-demo.io",
                verification_status=PartnerVerificationStatus.VERIFIED_REPRESENTATIVE,
                notes="Verified corporate partner for annual hackathon prizes and cloud credit grants.",
            )
            db.add(partner_org)
            db.flush()

        sponsorship_req = db.scalar(select(SponsorshipRequest).where(SponsorshipRequest.id == DEMO_SPONSOR_REQ_ID))
        if not sponsorship_req:
            sponsorship_req = SponsorshipRequest(
                id=DEMO_SPONSOR_REQ_ID,
                institution_id=DEMO_INSTITUTION_ID,
                opportunity_id=DEMO_OPP_1_ID,
                organizer_user_id=DEMO_USER_ID,
                partner_organization_id=DEMO_PARTNER_ORG_ID,
                objective="Tier-1 Gold Sponsorship for Apex Innovators 2026",
                support_type=SupportType.FINANCIAL,
                proposed_benefits="Keynote address, branding on stage and certificates, fast-track recruitment booth.",
                intended_audience="350+ engineering delegates and researchers",
                budget_currency="USD",
                budget_amount=2500.00,
                deadline=now + timedelta(days=14),
                contact_email="alex.vance@apextech.edu",
                status=SponsorshipStatus.UNDER_REVIEW,
                commercial_terms={"cloud_credits_included": True, "booth_space_sqft": 100},
            )
            db.add(sponsorship_req)

        # 13. Cross-College Promotion Campaign
        campaign = db.scalar(select(PromotionCampaign).where(PromotionCampaign.id == DEMO_CAMPAIGN_ID))
        if not campaign:
            campaign = PromotionCampaign(
                id=DEMO_CAMPAIGN_ID,
                source_institution_id=DEMO_INSTITUTION_ID,
                opportunity_id=DEMO_OPP_1_ID,
                creator_user_id=DEMO_USER_ID,
                campaign_type=CampaignType.FEATURED_SPOTLIGHT,
                pricing_package="standard_cross_college",
                price_amount=150.00,
                currency="USD",
                target_institution_ids=[],  # Cross-college reach
                status=CampaignStatus.ACTIVE,
                start_date=now - timedelta(days=2),
                end_date=now + timedelta(days=14),
                is_paid_placement=True,
                review_notes="Approved for cross-college collegiate hackathon spotlight.",
            )
            db.add(campaign)

        db.commit()
        return {
            "status": "success",
            "message": "Isolated demonstration environment seeded successfully.",
            "demo_institution_id": DEMO_INSTITUTION_ID,
            "demo_user_email": demo_user.email,
        }

    @staticmethod
    def reset_demo_environment(db: Session, settings: Settings) -> dict[str, Any]:
        """Safely delete all isolated demo data without touching production records."""
        # Delete demo records cascading from DEMO_INSTITUTION_ID
        inst = db.scalar(select(Institution).where(Institution.id == DEMO_INSTITUTION_ID))
        if inst:
            # Delete dependent entities where cascade is not automatic or needs clean removal
            db.execute(delete(OpportunityAssessment).where(OpportunityAssessment.opportunity_id.in_([DEMO_OPP_1_ID, DEMO_OPP_2_ID])))
            db.execute(delete(FieldEvidence).where(FieldEvidence.opportunity_id.in_([DEMO_OPP_1_ID, DEMO_OPP_2_ID])))
            db.execute(delete(SourceReference).where(SourceReference.opportunity_id.in_([DEMO_OPP_1_ID, DEMO_OPP_2_ID])))
            db.execute(delete(Opportunity).where(Opportunity.id.in_([DEMO_OPP_1_ID, DEMO_OPP_2_ID])))
            db.execute(delete(PromotionCampaign).where(PromotionCampaign.id == DEMO_CAMPAIGN_ID))
            db.execute(delete(SponsorshipRequest).where(SponsorshipRequest.id == DEMO_SPONSOR_REQ_ID))
            db.execute(delete(PartnerOrganization).where(PartnerOrganization.id == DEMO_PARTNER_ORG_ID))
            db.execute(delete(FollowUpTask).where(FollowUpTask.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(EventMemory).where(EventMemory.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(LegacyHandover).where(LegacyHandover.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(HelperMatch).where(HelperMatch.need_id == DEMO_NEED_ID))
            db.execute(delete(StudentNeed).where(StudentNeed.id == DEMO_NEED_ID))
            db.execute(delete(HelpOffer).where(HelpOffer.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(StudentProfile).where(StudentProfile.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(AlumniProfile).where(AlumniProfile.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(CampusRoleAssignment).where(CampusRoleAssignment.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(CampusPositionDefinition).where(CampusPositionDefinition.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(OrganizationalUnit).where(OrganizationalUnit.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(InstitutionMembership).where(InstitutionMembership.institution_id == DEMO_INSTITUTION_ID))
            db.delete(inst)

        # Remove demo accounts
        for uid in [DEMO_USER_ID, DEMO_STUDENT_USER_ID, DEMO_ALUMNI_USER_ID]:
            u = db.scalar(select(User).where(User.id == uid))
            if u:
                db.delete(u)

        db.commit()
        return {
            "status": "success",
            "message": "Demonstration environment reset cleanly. Production records unaffected.",
        }
