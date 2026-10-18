"""Demo environment provisioning, isolated dataset seeding, and reset service.

Provides a dedicated, presentation-ready demonstration environment for EventSignal:
1. Provisions a dedicated demo account with isolated credentials.
2. Seeds a realistic, fully interconnected college community for Apex Institute of Technology:
   - 13 Academic Departments and Student Organizations (CSE, AI/DS, ECE, Design, Management, ACM, Robotics, etc.)
   - 10 Official Campus Positions with verified institutional appointments.
   - 30 Synthetic Campus Members (Students across all years, Student Leaders, Alumni Mentors, Faculty Advisors).
   - 12 Curated Opportunities & Campus Events with structured evidence and assessments.
   - 12 Peer & Alumni Help Offers across career, technical, and research topics.
   - 4 Student Needs with explainable rule-derived Helper Matches.
   - 3 Legacy Leadership Handovers, 3 Event Memories, and 6 Follow-Up Tasks.
   - 3 Verified Corporate Partners, 3 Tiered Sponsorship Requests, and 2 Cross-College Promotion Campaigns.
   - 1 Committed Alumni Directory CSV Import Job.
3. Strict idempotency: re-running does not duplicate records or overwrite production data.
4. Clean reset: removes all synthetic demo records safely without touching real institutional tenants.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.models.alumni_import import AlumniImportJob, ImportJobStatus
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

# All synthetic user IDs for deterministic tracking and clean cascading reset
ALL_DEMO_USER_IDS = [
    DEMO_USER_ID,
    DEMO_STUDENT_USER_ID,
    DEMO_ALUMNI_USER_ID,
    "demo-user-faculty-004",
    "demo-user-student-005",
    "demo-user-student-006",
    "demo-user-student-007",
    "demo-user-student-008",
    "demo-user-alumni-009",
    "demo-user-student-010",
    "demo-user-student-011",
    "demo-user-student-012",
    "demo-user-student-013",
    "demo-user-alumni-014",
    "demo-user-student-015",
    "demo-user-faculty-016",
    "demo-user-student-017",
    "demo-user-student-018",
    "demo-user-alumni-019",
    "demo-user-student-020",
    "demo-user-student-021",
    "demo-user-alumni-022",
    "demo-user-student-023",
    "demo-user-student-024",
    "demo-user-student-025",
    "demo-user-faculty-026",
    "demo-user-alumni-027",
    "demo-user-student-028",
    "demo-user-student-029",
    "demo-user-alumni-030",
]

ALL_DEMO_OPPORTUNITY_IDS = [
    DEMO_OPP_1_ID,
    DEMO_OPP_2_ID,
    "demo-opp-event-003",
    "demo-opp-fellowship-004",
    "demo-opp-workshop-005",
    "demo-opp-competition-006",
    "demo-opp-workshop-007",
    "demo-opp-competition-008",
    "demo-opp-sprint-009",
    "demo-opp-research-010",
    "demo-opp-event-011",
    "demo-opp-internship-012",
]


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

        existing_by_id = db.scalar(select(User).where(User.id == DEMO_USER_ID))
        existing_by_email = db.scalar(select(User).where(User.email == email))

        # Collision guard: If email is registered to a user that is NOT DEMO_USER_ID and not marked as demo:
        if existing_by_email and existing_by_email.id != DEMO_USER_ID:
            is_demo = bool(existing_by_email.extra_data and existing_by_email.extra_data.get("is_demo") is True)
            if not is_demo:
                raise RuntimeError(
                    f"Account collision: Demo email '{email}' is already registered to a real user account. "
                    "Cannot overwrite real user records for demo mode."
                )

        existing = existing_by_id or existing_by_email
        if existing:
            existing.email = email
            existing.hashed_password = hash_password(password)
            existing.full_name = "Alex Vance (Demo Presenter)"
            existing.is_active = True
            existing.is_superuser = False
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
        """Seed a complete, interconnected, presentation-ready demonstration environment."""
        if not settings.demo_mode_enabled:
            raise RuntimeError("Cannot seed demo environment: demo_mode_enabled is False.")

        now = datetime.now(UTC)
        default_pwd_hash = hash_password("SyntheticCampus2026!")

        # =====================================================================
        # 1. PRIMARY INSTITUTION: APEX INSTITUTE OF TECHNOLOGY
        # =====================================================================
        demo_inst = db.scalar(select(Institution).where(Institution.id == DEMO_INSTITUTION_ID))
        if not demo_inst:
            demo_inst = Institution(
                id=DEMO_INSTITUTION_ID,
                name="Apex Institute of Technology (Demo Workspace)",
                slug=DEMO_INSTITUTION_SLUG,
                domain="apextech.edu",
                description="Premier collegiate engineering campus featuring collaborative student chapters, interdisciplinary research centers, and verified alumni mentorship.",
                location="Bengaluru, Karnataka, India",
                contact_email="workspace-demo@apextech.edu",
                website_url="https://demo.apextech.edu",
                status=InstitutionStatus.ACTIVE,
                verification_status=InstitutionVerificationStatus.VERIFIED,
                verified_at=now - timedelta(days=120),
                extra_data={
                    "is_demo": True,
                    "campus_tier": "Tier-1 Engineering & Innovation",
                    "student_enrollment": 4200,
                    "established_year": 2004,
                },
            )
            db.add(demo_inst)
            db.flush()

        # =====================================================================
        # 2. ACADEMIC DEPARTMENTS & STUDENT ORGANIZATIONS (ORGANIZATIONAL UNITS)
        # =====================================================================
        units_data = [
            # Academic Departments
            ("demo-unit-cse", "Department of Computer Science & Engineering", "CSE", "department", None, "Undergraduate & postgraduate computing sciences with active systems and AI labs.", "cse@apextech.edu"),
            ("demo-unit-aids", "Department of Artificial Intelligence & Data Science", "AIDS", "department", None, "Specialized division in deep learning, computer vision, and foundation models.", "aids@apextech.edu"),
            ("demo-unit-ece", "Department of Electronics & Communication Engineering", "ECE", "department", None, "Embedded systems, robotics, IoT telemetry, and signal processing.", "ece@apextech.edu"),
            ("demo-unit-des", "Department of Design & Digital Innovation", "DES", "department", None, "Human-centered design, UI/UX systems, and product ergonomics.", "design@apextech.edu"),
            ("demo-unit-mgmt", "Center for Entrepreneurship & Management", "MGMT", "center", None, "Incubation cell, venture capital workshops, and student startup mentoring.", "ecell@apextech.edu"),
            # Student Organizations (linked to parent departments)
            ("demo-unit-acm", "ACM Student Chapter", "ACM", "club", "demo-unit-cse", "Collegiate chapter promoting systems engineering, open source, and campus hackathons.", "acm@apextech.edu"),
            ("demo-unit-aiml", "AI & Machine Learning Society", "AIML", "club", "demo-unit-aids", "Student research group advancing generative models, PyTorch projects, and paper reading circles.", "aiml-club@apextech.edu"),
            ("demo-unit-robo", "Robotics & Autonomous Systems Club", "ROBO", "club", "demo-unit-ece", "Hardware prototyping, micro-controller firmware, ROS2, and competitive robotics.", "robotics@apextech.edu"),
            ("demo-unit-osc", "Web Dev & Open Source Community", "OSC", "club", "demo-unit-cse", "Collaborative student developers contributing to upstream open source and full-stack web applications.", "opensource@apextech.edu"),
            ("demo-unit-cpc", "Competitive Programming Club", "CPC", "club", "demo-unit-cse", "Algorithmic problem-solving, graph algorithms, and ICPC regional training.", "cp-club@apextech.edu"),
            ("demo-unit-ecell", "Student Entrepreneurship Cell", "ECELL", "club", "demo-unit-mgmt", "Connecting student innovators with venture capital, seed grants, and pitch competitions.", "ecell-students@apextech.edu"),
            ("demo-unit-hack", "Apex Hackathon Organizing Committee", "HACK", "committee", "demo-unit-cse", "Standing committee dedicated to planning and hosting the flagship annual campus hackathon.", "hackathon@apextech.edu"),
            ("demo-unit-cult", "Design & Creative Arts Society", "CULT", "club", "demo-unit-des", "UI/UX design sprints, visual branding, and accessible product development.", "creatives@apextech.edu"),
        ]

        for uid, name, code, utype, parent_id, desc, email in units_data:
            existing_unit = db.scalar(select(OrganizationalUnit).where(OrganizationalUnit.id == uid))
            if not existing_unit:
                db.add(
                    OrganizationalUnit(
                        id=uid,
                        institution_id=DEMO_INSTITUTION_ID,
                        name=name,
                        code=code,
                        unit_type=utype,
                        parent_id=parent_id,
                        description=desc,
                        contact_email=email,
                    )
                )
        db.flush()

        # =====================================================================
        # 3. CAMPUS POSITION DEFINITIONS
        # =====================================================================
        positions_data = [
            ("demo-pos-acm-chair", "demo-unit-acm", "ACM Student Chapter Chair", "Lead executive overseeing technical workshops, guest lectures, and campus outreach.", True),
            ("demo-pos-acm-tech", "demo-unit-acm", "ACM Technical Lead", "Architect of chapter engineering projects, infrastructure, and technical hackathon tracks.", False),
            ("demo-pos-aiml-pres", "demo-unit-aiml", "AIML Society President", "Director of machine learning study groups, research paper sessions, and model deployments.", True),
            ("demo-pos-aiml-res", "demo-unit-aiml", "AIML Research Coordinator", "Coordinates undergraduate research papers, dataset curation, and conference submissions.", False),
            ("demo-pos-robo-lead", "demo-unit-robo", "Robotics Club Lead", "Manages hardware lab equipment, microcontroller inventory, and robotics competition teams.", True),
            ("demo-pos-osc-coord", "demo-unit-osc", "Open Source Community Coordinator", "Drives GSoC preparation, good-first-issue onboarding, and git hygiene workshops.", False),
            ("demo-pos-ecell-lead", "demo-unit-ecell", "E-Cell Convener", "Organizes annual pitch competitions, angel investor visits, and startup grants.", True),
            ("demo-pos-hack-dir", "demo-unit-hack", "Hackathon Director", "General chair for the Apex Innovators flagship 36-hour hackathon.", True),
            ("demo-pos-hack-spons", "demo-unit-hack", "Hackathon Sponsorship Lead", "Leads corporate outreach, tier-benefit prospectuses, and sponsor relations.", False),
            ("demo-pos-fac-advisor", "demo-unit-cse", "Faculty Research Advisor", "Faculty sponsor overseeing academic integrity, laboratory facilities, and grant funding.", True),
        ]

        for pid, unit_id, title, desc, is_lead in positions_data:
            existing_pos = db.scalar(select(CampusPositionDefinition).where(CampusPositionDefinition.id == pid))
            if not existing_pos:
                db.add(
                    CampusPositionDefinition(
                        id=pid,
                        institution_id=DEMO_INSTITUTION_ID,
                        unit_id=unit_id,
                        title=title,
                        description=desc,
                        is_leadership=is_lead,
                    )
                )
        db.flush()

        # =====================================================================
        # 4. CAMPUS POPULATION: 30 SYNTHETIC PEOPLE
        # (Students across years 1-4, Student Leaders, Alumni Mentors, Faculty)
        # =====================================================================
        # User definitions: (id, email, full_name, membership_role, is_demo_account)
        users_specs = [
            # 1. Lead Presenter
            (DEMO_USER_ID, (settings.demo_user_email or "demo@eventsignal.local").strip().lower(), "Alex Vance (Demo Presenter)", InstitutionRole.INSTITUTION_ADMIN, True),
            # 2-20: Students & Leaders
            (DEMO_STUDENT_USER_ID, "riya.patel.demo@apextech.edu", "Riya Patel", InstitutionRole.STUDENT, True),
            ("demo-user-student-005", "kavya.sharma.demo@apextech.edu", "Kavya Sharma", InstitutionRole.STUDENT, True),
            ("demo-user-student-006", "devansh.joshi.demo@apextech.edu", "Devansh Joshi", InstitutionRole.STUDENT, True),
            ("demo-user-student-007", "aditya.nair.demo@apextech.edu", "Aditya Nair", InstitutionRole.STUDENT, True),
            ("demo-user-student-008", "sneha.kulkarni.demo@apextech.edu", "Sneha Kulkarni", InstitutionRole.STUDENT, True),
            ("demo-user-student-010", "pooja.sundaram.demo@apextech.edu", "Pooja Sundaram", InstitutionRole.STUDENT, True),
            ("demo-user-student-011", "arjun.mehta.demo@apextech.edu", "Arjun Mehta", InstitutionRole.STUDENT, True),
            ("demo-user-student-012", "neha.verma.demo@apextech.edu", "Neha Verma", InstitutionRole.STUDENT, True),
            ("demo-user-student-013", "rohan.deshmukh.demo@apextech.edu", "Rohan Deshmukh", InstitutionRole.STUDENT, True),
            ("demo-user-student-015", "siddharth.rao.demo@apextech.edu", "Siddharth Rao", InstitutionRole.STUDENT, True),
            ("demo-user-student-017", "tanvi.bhatia.demo@apextech.edu", "Tanvi Bhatia", InstitutionRole.STUDENT, True),
            ("demo-user-student-018", "harsh.vardhan.demo@apextech.edu", "Harsh Vardhan", InstitutionRole.STUDENT, True),
            ("demo-user-student-020", "karan.malhotra.demo@apextech.edu", "Karan Malhotra", InstitutionRole.STUDENT, True),
            ("demo-user-student-021", "divya.nambiar.demo@apextech.edu", "Divya Nambiar", InstitutionRole.STUDENT, True),
            ("demo-user-student-023", "swati.bansal.demo@apextech.edu", "Swati Bansal", InstitutionRole.STUDENT, True),
            ("demo-user-student-024", "aman.khan.demo@apextech.edu", "Aman Khan", InstitutionRole.STUDENT, True),
            ("demo-user-student-025", "shreya.pillai.demo@apextech.edu", "Shreya Pillai", InstitutionRole.STUDENT, True),
            ("demo-user-student-028", "tara.sen.demo@apextech.edu", "Tara Sen", InstitutionRole.STUDENT, True),
            ("demo-user-student-029", "varun.chawla.demo@apextech.edu", "Varun Chawla", InstitutionRole.STUDENT, True),
            # 21-27: Alumni Mentors
            (DEMO_ALUMNI_USER_ID, "marcus.chen.demo@alumni.apextech.edu", "Marcus Chen", InstitutionRole.ALUMNI, True),
            ("demo-user-alumni-009", "vikram.sengupta.demo@alumni.apextech.edu", "Vikram Sengupta", InstitutionRole.ALUMNI, True),
            ("demo-user-alumni-014", "priya.raghavan.demo@alumni.apextech.edu", "Priya Raghavan", InstitutionRole.ALUMNI, True),
            ("demo-user-alumni-019", "ananya.gupta.demo@alumni.apextech.edu", "Ananya Gupta", InstitutionRole.ALUMNI, True),
            ("demo-user-alumni-022", "nikhil.saxena.demo@alumni.apextech.edu", "Nikhil Saxena", InstitutionRole.ALUMNI, True),
            ("demo-user-alumni-027", "gaurav.taneja.demo@alumni.apextech.edu", "Gaurav Taneja", InstitutionRole.ALUMNI, True),
            ("demo-user-alumni-030", "ishaan.bahl.demo@alumni.apextech.edu", "Ishaan Bahl", InstitutionRole.ALUMNI, True),
            # 28-30: Faculty Advisors
            ("demo-user-faculty-004", "anita.roy.demo@apextech.edu", "Dr. Anita Roy", InstitutionRole.FACULTY, True),
            ("demo-user-faculty-016", "meera.iyer.demo@apextech.edu", "Dr. Meera Iyer", InstitutionRole.FACULTY, True),
            ("demo-user-faculty-026", "rajesh.murthy.demo@apextech.edu", "Dr. Rajesh Murthy", InstitutionRole.FACULTY, True),
        ]

        # Provision Users & Memberships
        for uid, email, full_name, m_role, is_demo in users_specs:
            u = db.scalar(select(User).where(User.id == uid))
            if not u:
                existing_email_user = db.scalar(select(User).where(User.email == email))
                if existing_email_user:
                    is_demo_rec = bool(
                        existing_email_user.extra_data and existing_email_user.extra_data.get("is_demo") is True
                    )
                    if not is_demo_rec:
                        raise RuntimeError(
                            f"Account collision during demo seeding: Email '{email}' is registered to a real user. "
                            "Aborting seed to protect real user records."
                        )
                    u = existing_email_user
            if not u:
                u = User(
                    id=uid,
                    email=email,
                    hashed_password=default_pwd_hash if uid != DEMO_USER_ID else hash_password(settings.demo_user_password or "DemoSignal2026!Secure"),
                    full_name=full_name,
                    is_active=True,
                    is_superuser=False,
                    extra_data={"is_demo": True, "synthetic": True},
                )
                db.add(u)
                db.flush()

            # Membership
            m = db.scalar(
                select(InstitutionMembership).where(
                    InstitutionMembership.institution_id == DEMO_INSTITUTION_ID,
                    InstitutionMembership.user_id == u.id,
                )
            )
            if not m:
                db.add(
                    InstitutionMembership(
                        institution_id=DEMO_INSTITUTION_ID,
                        user_id=u.id,
                        role=m_role,
                        status=MembershipStatus.ACTIVE,
                    )
                )
        db.flush()

        # =====================================================================
        # 5. VERIFIED CAMPUS ROLE APPOINTMENTS
        # =====================================================================
        appointments = [
            (DEMO_USER_ID, "demo-pos-acm-chair", "demo-unit-acm"),
            (DEMO_USER_ID, "demo-pos-hack-dir", "demo-unit-hack"),
            (DEMO_STUDENT_USER_ID, "demo-pos-acm-tech", "demo-unit-acm"),
            ("demo-user-student-005", "demo-pos-aiml-pres", "demo-unit-aiml"),
            ("demo-user-student-023", "demo-pos-aiml-res", "demo-unit-aiml"),
            ("demo-user-student-007", "demo-pos-robo-lead", "demo-unit-robo"),
            ("demo-user-student-013", "demo-pos-osc-coord", "demo-unit-osc"),
            ("demo-user-student-012", "demo-pos-ecell-lead", "demo-unit-ecell"),
            ("demo-user-student-015", "demo-pos-hack-spons", "demo-unit-hack"),
            ("demo-user-faculty-004", "demo-pos-fac-advisor", "demo-unit-cse"),
        ]

        for uid, pid, unit_id in appointments:
            assign = db.scalar(
                select(CampusRoleAssignment).where(
                    CampusRoleAssignment.institution_id == DEMO_INSTITUTION_ID,
                    CampusRoleAssignment.user_id == uid,
                    CampusRoleAssignment.position_id == pid,
                )
            )
            if not assign:
                db.add(
                    CampusRoleAssignment(
                        institution_id=DEMO_INSTITUTION_ID,
                        user_id=uid,
                        position_id=pid,
                        unit_id=unit_id,
                        verification_status=AssignmentVerificationStatus.VERIFIED,
                        start_date=now - timedelta(days=180),
                        end_date=now + timedelta(days=185),
                        is_active=True,
                    )
                )
        db.flush()

        # =====================================================================
        # 6. STUDENT & FACULTY PROFILES (INTERCONNECTED CAREER & ACADEMIC DATA)
        # =====================================================================
        students_profiles_data = [
            (DEMO_USER_ID, "Alex Vance", "React, Python, FastAPI, PostgreSQL, Docker, Microservices", "Distributed Systems, Cloud Platforms, Open Source, High-Scale APIs", "Cloud Infrastructure, Distributed Systems Engineering", "Pre-Final Year CSE · Distributed Systems & AI Chapter Lead", "B.Tech Computer Science", 2027),
            (DEMO_STUDENT_USER_ID, "Riya Patel", "Python, FastAPI, Docker, Linux, Git, Unit Testing", "Cloud Native Tooling, Open Source Fellowships, API Benchmarking", "Open Source Software Engineer, Backend Systems", "3rd Year CSE · Incoming ACM Chapter Lead", "B.Tech Computer Science", 2027),
            ("demo-user-student-005", "Kavya Sharma", "PyTorch, Computer Vision, Transformers, NumPy, CUDA", "Generative AI, Vision Transformers, Model Quantization", "AI Research Scientist, Machine Learning Engineer", "4th Year AI/DS · AIML Society President", "B.Tech Artificial Intelligence", 2026),
            ("demo-user-student-006", "Devansh Joshi", "Python, Pandas, Scikit-learn, Seaborn, SQL", "Applied Machine Learning, Data Analytics, Kaggle Challenges", "Data Scientist, Machine Learning Intern", "2nd Year AI/DS · Competitive ML Aspirant", "B.Tech Data Science", 2028),
            ("demo-user-student-007", "Aditya Nair", "Embedded C, C++, ROS2, FreeRTOS, Arduino, PCB Design", "Autonomous Navigation, Robotics Swarms, Edge Computing", "Robotics Hardware Engineer, Autonomous Systems", "3rd Year ECE · Robotics Club Lead", "B.Tech Electronics & Communication", 2027),
            ("demo-user-student-008", "Sneha Kulkarni", "C++, Data Structures, Algorithms, STL, Problem Solving", "Competitive Programming, Graph Theory, Number Theory", "Software Development Engineer, Big Tech Placements", "1st Year CSE · Competitive Programming Novice", "B.Tech Computer Science", 2029),
            ("demo-user-student-010", "Pooja Sundaram", "Figma, UI/UX, Design Systems, Tailwind CSS, Accessibility", "Design Systems, User Research, Micro-interactions, Typography", "Product Designer, Design Systems Lead", "3rd Year Design · Creative Arts Society Lead", "B.Des Digital Product Design", 2027),
            ("demo-user-student-011", "Arjun Mehta", "C++, Algorithms, Dynamic Programming, Segment Trees, Graph Theory", "ICPC Competitions, Math Puzzles, Low Latency Coding", "Quant Developer, High Frequency Trading SWE", "4th Year CSE · Candidate Master (Codeforces)", "B.Tech Computer Science", 2026),
            ("demo-user-student-012", "Neha Verma", "Product Discovery, Pitch Decks, Financial Modeling, Agile", "Tech Startups, Venture Capital, Growth Marketing", "Associate Product Manager, Venture Fellow", "3rd Year MGMT · Student E-Cell Convener", "B.Tech & Management Dual Degree", 2027),
            ("demo-user-student-013", "Rohan Deshmukh", "Rust, Linux Kernel, Systems C, Git, Concurrency", "Operating Systems, Rust Async Runtimes, Open Source", "Systems Programmer, Kernel Developer", "2nd Year CSE · Open Source Community Coordinator", "B.Tech Computer Science", 2028),
            ("demo-user-student-015", "Siddharth Rao", "Corporate Partnerships, Event Sponsorships, Public Speaking", "DevRel, Technical Marketing, Community Management", "Developer Relations Engineer, Technical Program Manager", "4th Year CSE · Hackathon Sponsorship Lead", "B.Tech Computer Science", 2026),
            ("demo-user-student-017", "Tanvi Bhatia", "Python, Linear Algebra, Calculus, Jupyter, Markdown", "AI Ethics, Statistics, Exploratory Data Analysis", "AI Product Specialist, Computational Researcher", "1st Year AI/DS · Student Researcher", "B.Tech Artificial Intelligence", 2029),
            ("demo-user-student-018", "Harsh Vardhan", "Next.js, TypeScript, Node.js, GraphQL, WebSockets, Tailwind", "Modern Frontend Architectures, Real-Time Collaboration, SSR", "Full-Stack Software Engineer, Frontend Architect", "3rd Year CSE · Web Development Lead", "B.Tech Computer Science", 2027),
            ("demo-user-student-020", "Karan Malhotra", "STM32, MicroPython, I2C/SPI, Sensor Fusion, KiCAD", "Drone Firmware, Motor Controllers, Embedded Linux", "Firmware Engineer, Embedded Systems Specialist", "2nd Year ECE · Robotics Firmware Member", "B.Tech Electronics & Communication", 2028),
            ("demo-user-student-021", "Divya Nambiar", "Kubernetes, Go, Prometheus, CI/CD, Terraform, Cloud Native", "Site Reliability Engineering, Platform DevOps, Cloud Native", "Site Reliability Engineer, Cloud Infrastructure SWE", "4th Year CSE · ACM Technical Lead", "B.Tech Computer Science", 2026),
            ("demo-user-student-023", "Swati Bansal", "Graph Neural Networks, PyTorch Geometric, Bioinformatics, Python", "Computational Biology, Graph Learning, Medical AI", "Bioinformatics Researcher, AI Research Fellow", "3rd Year AI/DS · AIML Research Coordinator", "B.Tech Artificial Intelligence", 2027),
            ("demo-user-student-024", "Aman Khan", "Financial Forecasting, Growth Analytics, SaaS Metrics, Excel", "FinTech, Seed Valuation, Corporate Partnerships", "Venture Capital Analyst, FinTech Product Manager", "2nd Year MGMT · E-Cell Sponsorship Associate", "B.Tech & Management Dual Degree", 2028),
            ("demo-user-student-025", "Shreya Pillai", "Design Research, Usability Testing, Information Architecture", "Accessible Web Design, Mobile Product UX, Design Systems", "UX Researcher, Interaction Designer", "3rd Year Design · UX Society Member", "B.Des Digital Product Design", 2027),
            ("demo-user-student-028", "Tara Sen", "Circuit Simulation, Raspberry Pi, Python, Sensor Interfacing", "Internet of Things, Smart Agriculture, Robotics", "Hardware Design Engineer, IoT Specialist", "1st Year ECE · Electronics Enthusiast", "B.Tech Electronics & Communication", 2029),
            ("demo-user-student-029", "Varun Chawla", "Network Security, Cryptography, Reverse Engineering, C, Python", "Capture The Flag (CTF), Vulnerability Research, DevSecOps", "Security Engineer, Penetration Tester", "4th Year CSE · Campus CTF Captain", "B.Tech Computer Science", 2026),
            # Faculty Advisors as academic mentors
            ("demo-user-faculty-004", "Dr. Anita Roy", "Distributed Computing, Machine Learning, Research Methodologies, Peer Review", "Academic Publishing, Systems Research, National Science Grants", "Professor & Head of Computer Science & Engineering", "Professor & HOD, Computer Science & Engineering", "Ph.D. Computer Science (Carnegie Mellon)", 2008),
            ("demo-user-faculty-016", "Dr. Meera Iyer", "Robotics, Control Systems, Edge Computing, Embedded Telemetry", "Autonomous Drone Swarms, Micro-actuators, Robotics Patents", "Associate Professor, Electronics & Communication", "Associate Professor, ECE Dept · Robotics Faculty Advisor", "Ph.D. Robotics & Automation (IISc)", 2012),
            ("demo-user-faculty-026", "Dr. Rajesh Murthy", "Technology Incubation, Intellectual Property, Venture Strategy", "Campus Incubators, Seed Grants, DeepTech Spinouts", "Dean of Innovation & Entrepreneurship", "Dean of Innovation · Director of Campus Incubation Cell", "Ph.D. Technology Management (IIM)", 2005),
        ]

        for uid, dname, skills, interests, goals, headline, deg, yr in students_profiles_data:
            sp = db.scalar(select(StudentProfile).where(StudentProfile.institution_id == DEMO_INSTITUTION_ID, StudentProfile.user_id == uid))
            if not sp:
                db.add(
                    StudentProfile(
                        user_id=uid,
                        institution_id=DEMO_INSTITUTION_ID,
                        display_name=dname,
                        skills=skills,
                        interests=interests,
                        career_goals=goals,
                        visibility=StudentVisibility.PUBLIC,
                        extra_data={
                            "headline": headline,
                            "degree_level": deg,
                            "graduation_year": yr,
                            "bio": f"Active academic member in {headline} at Apex Institute of Technology.",
                        },
                    )
                )
        db.flush()

        # =====================================================================
        # 7. ALUMNI PROFILES (EXPERIENCED INDUSTRY MENTORS)
        # =====================================================================
        alumni_profiles_data = [
            (DEMO_ALUMNI_USER_ID, "Marcus Chen", "Cloud Infrastructure & Distributed Systems", "Go, Kubernetes, gRPC, Distributed Caching, System Design", "Cloud Platforms", 3, "Career Guidance, System Design Reviews, GSoC Proposal Feedback", "Software Engineer II", "Google Cloud Platforms", 2023, "B.Tech CSE"),
            ("demo-user-alumni-009", "Vikram Sengupta", "FinTech & High Scale Payments", "Java, Go, Kafka, Cassandra, High-Concurrency APIs, Latency Tuning", "Financial Technology", 5, "Resume Reviews, SWE Interview Teardowns, Distributed Systems Architecture", "Staff Software Engineer", "Stripe", 2021, "B.Tech CSE"),
            ("demo-user-alumni-014", "Priya Raghavan", "Product Management & Discovery", "Product Discovery, Metrics Analysis, Wireframing, User Interviews, Growth", "Enterprise Software", 4, "APM Case Interviews, Product Portfolio Reviews, Tech-to-PM Transitions", "Senior Product Manager", "Microsoft Cloud Solutions", 2022, "B.Tech ECE"),
            ("demo-user-alumni-019", "Ananya Gupta", "Artificial Intelligence & NLP Research", "PyTorch, Transformers, LLM Alignment, JAX, Mathematical Foundations", "AI & Machine Learning", 6, "Graduate School SOP Reviews, AI Lab Applications, Top-Tier Research Mentorship", "Senior Research Scientist", "DeepMind Technologies", 2020, "B.Tech CSE"),
            ("demo-user-alumni-022", "Nikhil Saxena", "Payments Platform Engineering", "Distributed Transactions, PostgreSQL, Redis, Team Leadership, System Reliability", "Payment Gateways", 7, "Engineering Management, Backend Career Trajectories, Production Incident Reviews", "Director of Engineering", "Razorpay Engineering", 2019, "B.Tech CSE"),
            ("demo-user-alumni-027", "Gaurav Taneja", "Early-Stage Startups & AI Products", "Founding Engineering, Seed Fundraising, Pitch Decks, Customer Development", "Venture-backed Startups", 2, "Startup Pitch Teardowns, Founder Office Hours, First-Check Venture Strategy", "Co-Founder & CEO", "Stealth AI Infrastructure", 2024, "B.Tech AI/DS"),
            ("demo-user-alumni-030", "Ishaan Bahl", "Cloud Security & Zero-Trust Architecture", "AWS IAM, DevSecOps, Threat Modeling, Container Security, ISO Compliance", "Cloud Security", 8, "Cloud Security Careers, DevSecOps Roadmaps, Security Certification Guidance", "Senior Principal Security Architect", "Amazon Web Services", 2018, "B.Tech ECE"),
        ]

        for uid, dname, domain, skills, ind, exp, ment_int, title, org, yr, deg in alumni_profiles_data:
            ap = db.scalar(select(AlumniProfile).where(AlumniProfile.institution_id == DEMO_INSTITUTION_ID, AlumniProfile.user_id == uid))
            if not ap:
                db.add(
                    AlumniProfile(
                        user_id=uid,
                        institution_id=DEMO_INSTITUTION_ID,
                        display_name=dname,
                        professional_domain=domain,
                        skills=skills,
                        industry=ind,
                        years_experience=exp,
                        mentoring_interests=ment_int,
                        willing_to_connect=True,
                        monthly_connection_limit=6,
                        visibility=AlumniVisibility.PUBLIC,
                        extra_data={
                            "current_title": title,
                            "current_organization": org,
                            "graduation_year": yr,
                            "degree_level": deg,
                            "bio": f"{title} at {org}. Alumnus of Apex Institute of Technology ('{str(yr)[2:]}).",
                        },
                    )
                )
        db.flush()

        # =====================================================================
        # 8. CONNECTED OPPORTUNITIES & EVIDENCE ASSESSMENTS (12 RECORDS)
        # =====================================================================
        opportunities_data = [
            (
                DEMO_OPP_1_ID,
                "Apex Innovators Flagship Hackathon 2026 (Demo)",
                OpportunityType.HACKATHON,
                "Apex Hackathon Organizing Committee & ACM Chapter",
                now + timedelta(days=20),
                now + timedelta(days=22),
                now + timedelta(days=14),
                now + timedelta(days=22),
                "Bengaluru Campus Auditorium & Online Virtual Tracks",
                ParticipationMode.HYBRID,
                "Open to all verified collegiate teams across Indian engineering institutes",
                "Full-Stack Web Development, Machine Learning, Cloud Services, Rust",
                "USD 5,000 Total Prize Pool + Cloud Credits from CloudScale Labs",
                "https://demo.apextech.edu/events/innovators-2026",
                "Official Hackathon Announcement Page",
                0.95,
            ),
            (
                DEMO_OPP_2_ID,
                "Summer Cloud Systems Research Internship (Demo)",
                OpportunityType.INTERNSHIP,
                "Department of CSE & Center for Distributed Computing",
                now + timedelta(days=60),
                now + timedelta(days=120),
                now + timedelta(days=30),
                None,
                "Apex Research Laboratories, Bengaluru",
                ParticipationMode.OFFLINE,
                "Pre-final and final-year undergraduate students in CSE/IT",
                "C++, Rust, Linux Kernel Internals, Distributed Systems, gRPC",
                "Stipend: INR 45,000 / month + Lab Compute Quota",
                "https://demo.apextech.edu/research/internships-2026",
                "Department Laboratory Circular",
                0.90,
            ),
            (
                "demo-opp-event-003",
                "Autonomous Robotics Grand Prix 2026 (Demo)",
                OpportunityType.COMPETITION,
                "Robotics & Autonomous Systems Club",
                now + timedelta(days=35),
                now + timedelta(days=36),
                now + timedelta(days=25),
                now + timedelta(days=36),
                "Apex Outdoor Arena & Indoor Obstacle Track",
                ParticipationMode.OFFLINE,
                "Registered collegiate robotics teams with verified safety clearance",
                "ROS2, Embedded C, Computer Vision, Lidar Mapping, Motor Control",
                "INR 2,50,000 Cash Awards + Hardware Starter Kits from DevTools Global",
                "https://demo.apextech.edu/robotics/grand-prix-2026",
                "Robotics Club Official Portal",
                0.92,
            ),
            (
                "demo-opp-fellowship-004",
                "Google Summer of Code Mentorship Cohort (Demo)",
                OpportunityType.FELLOWSHIP,
                "Web Dev & Open Source Community",
                now + timedelta(days=45),
                now + timedelta(days=135),
                now + timedelta(days=21),
                None,
                "Remote Community Mentorship Program",
                ParticipationMode.ONLINE,
                "Enrolled students preparing upstream open source project proposals",
                "Python, FastAPI, Rust, Go, Git, Unit Testing, Proposal Writing",
                "Stipend funded by participating open source foundations",
                "https://demo.apextech.edu/opensource/gsoc-cohort-2026",
                "Open Source Chapter Handbook",
                0.88,
            ),
            (
                "demo-opp-workshop-005",
                "Deep Learning & Generative Models Workshop (Demo)",
                OpportunityType.WORKSHOP,
                "AI & Machine Learning Society & Dr. Anita Roy",
                now + timedelta(days=10),
                now + timedelta(days=12),
                now + timedelta(days=7),
                None,
                "Apex Turing Computing Laboratory & Live Stream",
                ParticipationMode.HYBRID,
                "Open to all students with introductory Python and linear algebra background",
                "PyTorch, Transformers, Hugging Face, Model Fine-tuning, LoRA",
                "Complimentary GPU Compute Cluster Access for Participants",
                "https://demo.apextech.edu/aiml/generative-workshop-2026",
                "AIML Society Workshop Schedule",
                0.94,
            ),
            (
                "demo-opp-competition-006",
                "Apex Campus Startup Pitch Fest 2026 (Demo)",
                OpportunityType.COMPETITION,
                "Student Entrepreneurship Cell & Bharat Tech Ventures",
                now + timedelta(days=50),
                now + timedelta(days=51),
                now + timedelta(days=35),
                now + timedelta(days=51),
                "Apex Incubation Hall, Bengaluru",
                ParticipationMode.OFFLINE,
                "Student and alumni founders building prototype-stage tech products",
                "Pitch Deck, Market Research, Unit Economics, MVP Prototyping",
                "INR 5,00,000 Seed Grant Pool + Angel Incubation Advisory",
                "https://demo.apextech.edu/ecell/pitchfest-2026",
                "E-Cell Official Prospectus",
                0.91,
            ),
            (
                "demo-opp-workshop-007",
                "Full-Stack Web Performance & SSR Masterclass (Demo)",
                OpportunityType.WORKSHOP,
                "Web Development Community & Harsh Vardhan",
                now + timedelta(days=18),
                now + timedelta(days=19),
                now + timedelta(days=15),
                None,
                "Online Interactive Masterclass",
                ParticipationMode.ONLINE,
                "All campus students interested in modern React and Next.js architectures",
                "Next.js, TypeScript, Server Components, Core Web Vitals, CDN Edge",
                "Certificate of Completion + Production Boilerplate Codebase",
                "https://demo.apextech.edu/dev/performance-masterclass-2026",
                "Web Dev Community Calendar",
                0.89,
            ),
            (
                "demo-opp-competition-008",
                "Global ACM ICPC Regional Qualifier Mock Camp (Demo)",
                OpportunityType.COMPETITION,
                "Competitive Programming Club & Arjun Mehta",
                now + timedelta(days=28),
                now + timedelta(days=29),
                now + timedelta(days=22),
                None,
                "Apex Online Judge Server",
                ParticipationMode.ONLINE,
                "3-member collegiate teams registered for ICPC prelims",
                "Advanced Dynamic Programming, Flow Networks, Suffix Automata, C++",
                "Contest Badges + Fast-Track Interview Referrals",
                "https://demo.apextech.edu/cpc/mock-icpc-2026",
                "Competitive Programming Club Contest Announcement",
                0.93,
            ),
            (
                "demo-opp-sprint-009",
                "Human-Centered UI/UX Design Sprint (Demo)",
                OpportunityType.WORKSHOP,
                "Design & Creative Arts Society & Pooja Sundaram",
                now + timedelta(days=40),
                now + timedelta(days=44),
                now + timedelta(days=32),
                now + timedelta(days=44),
                "Apex Design Studio, 3rd Floor",
                ParticipationMode.OFFLINE,
                "Students passionate about product design, Figma, and accessibility",
                "Figma, Wireframing, Usability Auditing, Design Tokens, Microcopy",
                "Top designs showcased in the campus digital showcase gallery",
                "https://demo.apextech.edu/design/sprint-2026",
                "Design Society Sprint Brief",
                0.87,
            ),
            (
                "demo-opp-research-010",
                "Embedded Firmware & IoT Security Fellowship (Demo)",
                OpportunityType.FELLOWSHIP,
                "Department of ECE & Dr. Meera Iyer",
                now + timedelta(days=70),
                now + timedelta(days=160),
                now + timedelta(days=45),
                None,
                "Advanced Telemetry Research Lab",
                ParticipationMode.OFFLINE,
                "ECE and CSE students with microprocessor and cryptography coursework",
                "Firmware Reverse Engineering, CAN-bus Telemetry, Cryptographic Coprocessors",
                "INR 35,000 / month Fellowship Award + Conference Travel Grant",
                "https://demo.apextech.edu/ece/iot-fellowship-2026",
                "Department of ECE Research Circular",
                0.91,
            ),
            (
                "demo-opp-event-011",
                "Annual Campus Technology Day 2026 (Demo)",
                OpportunityType.CONFERENCE,
                "Dean of Innovation & Student Clubs Federation",
                now + timedelta(days=65),
                now + timedelta(days=66),
                now + timedelta(days=50),
                None,
                "Apex Main Campus Grounds, Bengaluru",
                ParticipationMode.OFFLINE,
                "Open to all students, alumni, faculty, and visiting industry guests",
                "Project Demos, Technical Keynotes, Club Expositions, Networking",
                "Campus Project Awards + Verified Event Credentials",
                "https://demo.apextech.edu/events/techday-2026",
                "Campus-wide Dean Announcement",
                0.96,
            ),
            (
                "demo-opp-internship-012",
                "FinTech Distributed Infrastructure Graduate Internship (Demo)",
                OpportunityType.INTERNSHIP,
                "Bharat Tech Ventures & Apex Placement Cell",
                now + timedelta(days=80),
                now + timedelta(days=170),
                now + timedelta(days=40),
                None,
                "Bengaluru FinTech Center & Hybrid",
                ParticipationMode.HYBRID,
                "Graduating final-year B.Tech students in CSE/IT/ECE",
                "Java, Go, Kafka, Distributed SQL, Event-Driven Architecture, Microservices",
                "Stipend: INR 60,000 / month with full-time PPO conversion path",
                "https://demo.apextech.edu/placements/fintech-internship-2026",
                "Training & Placement Cell Verified Bulletin",
                0.94,
            ),
        ]

        for (
            oid,
            title,
            otype,
            org,
            sdate,
            edate,
            rdate,
            subdate,
            loc,
            mode,
            elig,
            skills,
            comp,
            app_url,
            src_title,
            score,
        ) in opportunities_data:
            existing_opp = db.scalar(select(Opportunity).where(Opportunity.id == oid))
            if not existing_opp:
                opp = Opportunity(
                    id=oid,
                    title=title,
                    opportunity_type=otype,
                    organizer=org,
                    start_date=sdate,
                    end_date=edate,
                    registration_deadline=rdate,
                    submission_deadline=subdate,
                    location=loc,
                    mode=mode,
                    eligibility=elig,
                    skills_required=skills,
                    compensation=comp,
                    application_url=app_url,
                    institution_id=DEMO_INSTITUTION_ID,
                )
                db.add(opp)
                db.flush()

                # Source Reference
                src = SourceReference(
                    opportunity_id=opp.id,
                    source_type=SourceType.ORGANIZER_WEBSITE,
                    url=app_url,
                    title=src_title,
                )
                db.add(src)
                db.flush()

                # Structured Evidence
                db.add_all([
                    FieldEvidence(
                        opportunity_id=opp.id,
                        source_id=src.id,
                        field_name="title",
                        extracted_value=title,
                        supporting_excerpt=f"{title}: Verified Announcement",
                        evidence_status=EvidenceStatus.FOUND,
                        extraction_method=ExtractionMethod.STRUCTURED,
                    ),
                    FieldEvidence(
                        opportunity_id=opp.id,
                        source_id=src.id,
                        field_name="organizer",
                        extracted_value=org,
                        supporting_excerpt=f"Hosted and organized by {org}.",
                        evidence_status=EvidenceStatus.FOUND,
                        extraction_method=ExtractionMethod.STRUCTURED,
                    ),
                    FieldEvidence(
                        opportunity_id=opp.id,
                        source_id=src.id,
                        field_name="compensation",
                        extracted_value=comp,
                        supporting_excerpt=f"Awards and benefits: {comp}",
                        evidence_status=EvidenceStatus.FOUND,
                        extraction_method=ExtractionMethod.RULE_BASED,
                    ),
                ])

                # Assessment
                db.add(
                    OpportunityAssessment(
                        opportunity_id=opp.id,
                        overall_score=score,
                        completeness_score=min(1.0, score + 0.03),
                        evidence_quality_score=min(1.0, score - 0.02),
                        consistency_score=min(1.0, score + 0.01),
                        completeness_explanation="Critical fields including deadlines, organizers, eligibility, and benefits extracted with high structured fidelity.",
                        evidence_quality_explanation="Supported by institutional domain references and verified circulars.",
                        consistency_explanation="No contradictory dates, terms, or conflicting participant requirements found.",
                        missing_critical_fields=[],
                        missing_optional_fields=[],
                        ambiguous_fields=[],
                        conflicting_fields=[],
                        conflict_details=[],
                        limitations="Demonstration opportunity for campus verification auditing.",
                        total_fields_assessed=8,
                        fields_found_count=8,
                        fields_not_found_count=0,
                        fields_failed_count=0,
                    )
                )
        db.flush()

        # =====================================================================
        # 9. FUNCTIONAL MENTORSHIP COMMUNITY (12 HELP OFFERS)
        # =====================================================================
        help_offers_data = [
            (
                DEMO_OFFER_1_ID,
                DEMO_ALUMNI_USER_ID,
                "System Design & Cloud Architecture Mentoring",
                "career_guidance",
                "1-on-1 sessions on distributed storage, latency trade-offs, microservice design, and production incident management.",
                "System Design, Cloud Infrastructure, Kubernetes, Go, Distributed Caching",
                HelpOfferAudience.STUDENTS_ONLY.value,
                HelpOfferDeliveryMode.REMOTE.value,
            ),
            (
                DEMO_OFFER_2_ID,
                DEMO_ALUMNI_USER_ID,
                "GSoC & Open Source Proposal Reviews",
                "project_review",
                "Actionable feedback on open source project architecture proposals, contribution hygiene, and clean git pull requests.",
                "Open Source, Git, Proposal Writing, Python, FastAPI, Docker",
                HelpOfferAudience.ALL.value,
                HelpOfferDeliveryMode.REMOTE.value,
            ),
            (
                "demo-offer-research-003",
                "demo-user-faculty-004",
                "Undergraduate Research Lab Guidance & Paper Reviews",
                "research_guidance",
                "Advising undergraduate research scholars on experimental design, dataset benchmarks, and academic paper submissions.",
                "Research Methodologies, Academic Publishing, Experimental Design, Distributed Systems",
                HelpOfferAudience.STUDENTS_ONLY.value,
                HelpOfferDeliveryMode.IN_PERSON.value,
            ),
            (
                "demo-offer-ai-004",
                "demo-user-student-005",
                "Machine Learning & PyTorch Project Office Hours",
                "technical_mentorship",
                "Weekly peer office hours reviewing PyTorch model training loops, loss curve debugging, and Hugging Face pipelines.",
                "PyTorch, Computer Vision, Transformers, NumPy, CUDA Optimization",
                HelpOfferAudience.ALL.value,
                HelpOfferDeliveryMode.HYBRID.value,
            ),
            (
                "demo-offer-placement-005",
                "demo-user-alumni-009",
                "Tier-1 SWE Placement & Resume Teardowns",
                "career_guidance",
                "Comprehensive line-by-line engineering resume critique, STAR-method interview walkthroughs, and Big Tech placement tips.",
                "Resume Review, Coding Interviews, Distributed Systems, Java, Go",
                HelpOfferAudience.STUDENTS_ONLY.value,
                HelpOfferDeliveryMode.REMOTE.value,
            ),
            (
                "demo-offer-design-006",
                "demo-user-student-010",
                "UI/UX Portfolio & Design System Feedback",
                "portfolio_review",
                "Design audits for student apps, Figma component libraries, typography scale, and WCAG accessibility standards.",
                "Figma, UI/UX, Design Systems, Usability Auditing, Tailwind CSS",
                HelpOfferAudience.ALL.value,
                HelpOfferDeliveryMode.HYBRID.value,
            ),
            (
                "demo-offer-cp-007",
                "demo-user-student-011",
                "Competitive Programming & Advanced DSA Mentoring",
                "technical_mentorship",
                "Intensive problem walkthroughs on graph algorithms, segment trees, and contest strategy for ICPC and Codeforces.",
                "C++, Dynamic Programming, Graph Theory, Number Theory, Algorithms",
                HelpOfferAudience.STUDENTS_ONLY.value,
                HelpOfferDeliveryMode.REMOTE.value,
            ),
            (
                "demo-offer-apm-008",
                "demo-user-alumni-014",
                "APM Product Management Case Interview Prep",
                "career_guidance",
                "Interactive mock case interviews focusing on product design questions, root cause metrics analysis, and GTM strategy.",
                "Product Discovery, Case Interviews, Metrics Analysis, Tech-to-PM Transition",
                HelpOfferAudience.STUDENTS_ONLY.value,
                HelpOfferDeliveryMode.REMOTE.value,
            ),
            (
                "demo-offer-web-009",
                "demo-user-student-018",
                "Full-Stack Architecture & API Design Code Reviews",
                "technical_mentorship",
                "Code reviews focusing on Next.js 14 App Router, REST/GraphQL API contracts, TypeScript types, and database indexing.",
                "Next.js, TypeScript, GraphQL, Node.js, REST APIs, Database Optimization",
                HelpOfferAudience.ALL.value,
                HelpOfferDeliveryMode.REMOTE.value,
            ),
            (
                "demo-offer-grad-010",
                "demo-user-alumni-019",
                "Top-tier AI Graduate School & Research Statement Reviews",
                "research_guidance",
                "Guidance on writing competitive Statements of Purpose (SOP) and connecting with prospective advisors at top global AI labs.",
                "Graduate School SOP, Research Statements, Deep Learning, Academic Networking",
                HelpOfferAudience.STUDENTS_ONLY.value,
                HelpOfferDeliveryMode.REMOTE.value,
            ),
            (
                "demo-offer-hardware-011",
                "demo-user-faculty-016",
                "Hardware Prototyping & PCB Design Lab Hours",
                "technical_mentorship",
                "Hands-on lab sessions debugging microcontroller schematics, KiCAD layouts, and embedded firmware timing.",
                "Embedded Systems, PCB Design, KiCAD, ROS2, Sensor Interfacing",
                HelpOfferAudience.STUDENTS_ONLY.value,
                HelpOfferDeliveryMode.IN_PERSON.value,
            ),
            (
                "demo-offer-security-012",
                "demo-user-alumni-030",
                "Cloud Security & DevSecOps Career Mentoring",
                "career_guidance",
                "Mentorship on cloud threat modeling, container security, IAM architectures, and security engineering roadmaps.",
                "Cloud Security, DevSecOps, AWS IAM, Threat Modeling, Linux Security",
                HelpOfferAudience.STUDENTS_ONLY.value,
                HelpOfferDeliveryMode.REMOTE.value,
            ),
        ]

        for oid, uid, title, cat, desc, skills, aud, dmode in help_offers_data:
            existing_offer = db.scalar(select(HelpOffer).where(HelpOffer.id == oid))
            if not existing_offer:
                db.add(
                    HelpOffer(
                        id=oid,
                        user_id=uid,
                        institution_id=DEMO_INSTITUTION_ID,
                        title=title,
                        category=cat,
                        description=desc,
                        applicable_skills=skills,
                        intended_audience=aud,
                        delivery_mode=dmode,
                        status=HelpOfferStatus.ACTIVE.value,
                        extra_data={"max_recipients": 6, "verified_mentor": True},
                    )
                )
        db.flush()

        # =====================================================================
        # 10. STUDENT NEEDS & RULE-DERIVED HELPER MATCHES (4 NEEDS)
        # =====================================================================
        needs_specs = [
            (
                DEMO_NEED_ID,
                DEMO_STUDENT_USER_ID,
                "Proposal Feedback for Cloud Native Open Source Fellowship",
                "project_review",
                "Need guidance on structuring architecture proposal and benchmark tests for a Python and FastAPI microservices project.",
                NeedUrgency.HIGH,
                "remote",
                NeedStatus.MATCHED,
            ),
            (
                "demo-need-ml-002",
                "demo-user-student-006",
                "Machine Learning Benchmark Guidance for CV Paper",
                "technical_mentorship",
                "Seeking assistance on reproducing baseline Vision Transformer accuracy metrics on limited campus GPU resources.",
                NeedUrgency.MEDIUM,
                "hybrid",
                NeedStatus.MATCHED,
            ),
            (
                "demo-need-swe-003",
                DEMO_USER_ID,
                "Mock Technical Interview for Cloud Infrastructure Role",
                "career_guidance",
                "Preparing for upcoming cloud platforms engineering round. Need realistic mock questions on distributed caching and concurrency.",
                NeedUrgency.HIGH,
                "remote",
                NeedStatus.MATCHED,
            ),
            (
                "demo-need-ui-004",
                "demo-user-student-025",
                "Design System & Usability Audit for Hackathon Web Platform",
                "portfolio_review",
                "Need senior design review for student hackathon portal navigation, color contrast, and component states in Figma.",
                NeedUrgency.LOW,
                "remote",
                NeedStatus.OPEN,  # Leaves open so evaluator can test matching live
            ),
        ]

        for nid, uid, title, cat, desc, urg, dmode, nstatus in needs_specs:
            sp = db.scalar(select(StudentProfile).where(StudentProfile.institution_id == DEMO_INSTITUTION_ID, StudentProfile.user_id == uid))
            if not sp:
                continue
            existing_need = db.scalar(select(StudentNeed).where(StudentNeed.id == nid))
            if not existing_need:
                need_obj = StudentNeed(
                    id=nid,
                    student_profile_id=sp.id,
                    institution_id=DEMO_INSTITUTION_ID,
                    title=title,
                    category=cat,
                    description=desc,
                    urgency=urg,
                    preferred_delivery_mode=dmode,
                    status=nstatus,
                )
                db.add(need_obj)
                db.flush()

                # Add rule-evaluated matches for the matched needs
                if nid == DEMO_NEED_ID:
                    db.add_all([
                        HelperMatch(
                            need_id=need_obj.id,
                            help_offer_id=DEMO_OFFER_2_ID,
                            institution_id=DEMO_INSTITUTION_ID,
                            score=0.92,
                            scorer_version="1.0.0",
                            status=MatchStatus.PROPOSED,
                            rule_results=[
                                {"rule": "Category alignment", "weight": 0.45, "contribution": 0.45, "details": "Exact match on category 'project_review'."},
                                {"rule": "Delivery mode alignment", "weight": 0.20, "contribution": 0.20, "details": "Both parties prefer remote delivery."},
                                {"rule": "Skill keyword overlap", "weight": 0.25, "contribution": 0.17, "details": "Strong overlap on Python, FastAPI, and Git proposals."},
                                {"rule": "Urgency boost", "weight": 0.10, "contribution": 0.10, "details": "Need marked as high urgency."},
                            ],
                            summary_explanation="Exact category alignment on open-source project review, matching remote mode, and high skill overlap with Marcus Chen.",
                        ),
                        HelperMatch(
                            need_id=need_obj.id,
                            help_offer_id="demo-offer-web-009",
                            institution_id=DEMO_INSTITUTION_ID,
                            score=0.85,
                            scorer_version="1.0.0",
                            status=MatchStatus.PROPOSED,
                            rule_results=[
                                {"rule": "Category alignment", "weight": 0.45, "contribution": 0.38, "details": "High technical mentorship and code review alignment."},
                                {"rule": "Delivery mode alignment", "weight": 0.20, "contribution": 0.20, "details": "Both prefer remote delivery."},
                                {"rule": "Skill keyword overlap", "weight": 0.25, "contribution": 0.17, "details": "Strong overlap on Python, APIs, and Web architectures."},
                                {"rule": "Urgency boost", "weight": 0.10, "contribution": 0.10, "details": "Need marked as high urgency."},
                            ],
                            summary_explanation="Strong technical code review overlap with Harsh Vardhan for architecture and API hygiene.",
                        ),
                    ])

                elif nid == "demo-need-ml-002":
                    db.add_all([
                        HelperMatch(
                            need_id=need_obj.id,
                            help_offer_id="demo-offer-ai-004",
                            institution_id=DEMO_INSTITUTION_ID,
                            score=0.94,
                            scorer_version="1.0.0",
                            status=MatchStatus.PROPOSED,
                            rule_results=[
                                {"rule": "Category alignment", "weight": 0.45, "contribution": 0.45, "details": "Exact match on technical machine learning mentorship."},
                                {"rule": "Delivery mode alignment", "weight": 0.20, "contribution": 0.20, "details": "Both agree on hybrid office hours."},
                                {"rule": "Skill keyword overlap", "weight": 0.25, "contribution": 0.21, "details": "PyTorch, Vision Transformers, and benchmark optimization."},
                                {"rule": "Urgency boost", "weight": 0.10, "contribution": 0.08, "details": "Medium urgency requirement."},
                            ],
                            summary_explanation="Exceptional domain match with Kavya Sharma on PyTorch and Vision Transformer benchmarks.",
                        ),
                        HelperMatch(
                            need_id=need_obj.id,
                            help_offer_id="demo-offer-research-003",
                            institution_id=DEMO_INSTITUTION_ID,
                            score=0.88,
                            scorer_version="1.0.0",
                            status=MatchStatus.PROPOSED,
                            rule_results=[
                                {"rule": "Category alignment", "weight": 0.45, "contribution": 0.40, "details": "Research guidance matches paper submission goals."},
                                {"rule": "Delivery mode alignment", "weight": 0.20, "contribution": 0.18, "details": "Campus lab hours support hybrid meetings."},
                                {"rule": "Skill keyword overlap", "weight": 0.25, "contribution": 0.22, "details": "Academic benchmarks and experimental rigor."},
                                {"rule": "Urgency boost", "weight": 0.10, "contribution": 0.08, "details": "Medium urgency requirement."},
                            ],
                            summary_explanation="Academic research advisement from Dr. Anita Roy on experimental baselines and publication rigor.",
                        ),
                    ])

                elif nid == "demo-need-swe-003":
                    db.add_all([
                        HelperMatch(
                            need_id=need_obj.id,
                            help_offer_id=DEMO_OFFER_1_ID,
                            institution_id=DEMO_INSTITUTION_ID,
                            score=0.95,
                            scorer_version="1.0.0",
                            status=MatchStatus.PROPOSED,
                            rule_results=[
                                {"rule": "Category alignment", "weight": 0.45, "contribution": 0.45, "details": "Exact career guidance & systems mentoring match."},
                                {"rule": "Delivery mode alignment", "weight": 0.20, "contribution": 0.20, "details": "Both prefer remote session delivery."},
                                {"rule": "Skill keyword overlap", "weight": 0.25, "contribution": 0.20, "details": "Distributed systems, caching, and cloud infrastructure."},
                                {"rule": "Urgency boost", "weight": 0.10, "contribution": 0.10, "details": "High urgency interview preparation."},
                            ],
                            summary_explanation="Top match with Google Cloud engineer Marcus Chen for cloud infrastructure and distributed systems interview coaching.",
                        ),
                        HelperMatch(
                            need_id=need_obj.id,
                            help_offer_id="demo-offer-placement-005",
                            institution_id=DEMO_INSTITUTION_ID,
                            score=0.91,
                            scorer_version="1.0.0",
                            status=MatchStatus.PROPOSED,
                            rule_results=[
                                {"rule": "Category alignment", "weight": 0.45, "contribution": 0.45, "details": "Exact match on technical placement coaching."},
                                {"rule": "Delivery mode alignment", "weight": 0.20, "contribution": 0.20, "details": "Remote mock interview format."},
                                {"rule": "Skill keyword overlap", "weight": 0.25, "contribution": 0.16, "details": "Distributed systems, concurrency, and architecture."},
                                {"rule": "Urgency boost", "weight": 0.10, "contribution": 0.10, "details": "High urgency interview preparation."},
                            ],
                            summary_explanation="High-concurrency systems interview preparation with Stripe Staff Engineer Vikram Sengupta.",
                        ),
                    ])
        db.flush()

        # =====================================================================
        # 11. INSTITUTIONAL STORY & LEGACY (3 HANDOVERS & 3 MEMORIES)
        # =====================================================================
        # Handovers
        handovers_data = [
            (
                DEMO_HANDOVER_ID,
                "demo-pos-acm-chair",
                DEMO_USER_ID,
                DEMO_STUDENT_USER_ID,
                "ACM Student Chapter Leadership Handover 2025-2026",
                "Organized 4 major campus hackathons, grew active chapter membership to 350+ delegates, and secured 3 corporate sponsors.",
                "Transitioning cluster staging servers; expanding 2026 annual flagship hackathon sponsorship drive with CloudScale Labs.",
                [
                    {"name": "Dean of Student Affairs", "email": "admin@apextech.edu", "role": "Faculty Liaison"},
                    {"name": "Industry Relations Office", "email": "corporate@apextech.edu", "role": "Corporate Outreach"},
                ],
                "Always finalize venue electrical backups and backup Wi-Fi access points at least 10 days before hackathon kick-off.",
                "Meet with CSE Department Head during the first week of August; initiate sponsor prospectus delivery early.",
                HandoverStatus.SUBMITTED,
            ),
            (
                "demo-handover-robo-002",
                "demo-pos-robo-lead",
                "demo-user-student-007",
                "demo-user-student-020",
                "Robotics Club Technical Lead Handover 2025-2026",
                "Constructed 6 competitive maze solvers, hosted the inaugural campus RoboWars, and updated the micro-controller inventory.",
                "Procuring STM32 development boards; preparing the outdoor obstacle course for the 2026 Autonomous Grand Prix.",
                [
                    {"name": "Dr. Meera Iyer", "email": "meera.iyer.demo@apextech.edu", "role": "Faculty Advisor"},
                    {"name": "Hardware Workshop Coordinator", "email": "lab@apextech.edu", "role": "Lab Inventory"},
                ],
                "Ensure all lithium polymer batteries are stored in fire-safe containment cases and checked before any arena testing.",
                "Re-calibrate ultrasonic and lidar sensors on arena track 14 days prior to event day.",
                HandoverStatus.ACKNOWLEDGED,
            ),
            (
                "demo-handover-hack-003",
                "demo-pos-hack-dir",
                DEMO_USER_ID,
                "demo-user-student-015",
                "Apex Hackathon Organizing Committee Handover",
                "Created standardized sponsorship prospectus templates, automated team registration verification, and published rulebooks.",
                "Active outreach to Bharat Tech Ventures and DevTools Global for 2026 prize pool and cloud compute credits.",
                [
                    {"name": "Elena Rostova", "email": "partnerships@cloudscale-demo.io", "role": "Corporate Sponsor Lead"},
                    {"name": "Campus Facilities Manager", "email": "facilities@apextech.edu", "role": "Auditorium Booking"},
                ],
                "Publish evaluation rubrics to teams at check-in to ensure transparent judging and eliminate project scope disputes.",
                "Finalize food and beverage buffers with catering service at least 7 days ahead.",
                HandoverStatus.SUBMITTED,
            ),
        ]

        for hid, pid, out_uid, in_uid, htitle, acc, ongoing, contacts, lessons, next_steps, hstatus in handovers_data:
            existing_handover = db.scalar(select(LegacyHandover).where(LegacyHandover.id == hid))
            if not existing_handover:
                db.add(
                    LegacyHandover(
                        id=hid,
                        institution_id=DEMO_INSTITUTION_ID,
                        position_id=pid,
                        outgoing_user_id=out_uid,
                        incoming_user_id=in_uid,
                        title=htitle,
                        accomplishments_summary=acc,
                        ongoing_work=ongoing,
                        key_contacts=contacts,
                        lessons_learned=lessons,
                        recommended_first_steps=next_steps,
                        status=hstatus,
                    )
                )
        db.flush()

        # Event Memories
        memories_data = [
            (
                DEMO_MEMORY_ID,
                DEMO_OPP_1_ID,
                DEMO_USER_ID,
                "Apex Hackathon 2025 Retrospective",
                "High mentor engagement, automated PR verification using CI/CD test runners, vibrant midnight showcase.",
                "Order catering buffer meals 2 hours ahead of dinner rush to prevent long cafeteria queues.",
                "280 registered delegates, 65 team project submissions, 14 final presentations.",
                "12 projects deployed to production staging; 3 received seed sponsor interest and incubation offers.",
                ["hackathon", "systems", "open-source", "mentorship"],
                {"event_year": 2025, "recommended_budget": "INR 3,50,000 for 300 delegates"},
            ),
            (
                "demo-memory-robo-002",
                "demo-opp-event-003",
                "demo-user-student-007",
                "Annual Robotics Expo 2025 Debrief",
                "Precision obstacle track navigation and strong inter-college participation across 18 institutions.",
                "Arena lighting glare caused lidar reflection artifacts; need non-reflective tape on track borders.",
                "180 participants across 32 teams; 500+ campus student attendees.",
                "4 patents filed on autonomous rover steering; DevTools Global sponsored hardware tools.",
                ["robotics", "hardware", "ros2", "embedded"],
                {"event_year": 2025, "track_specs": "40m obstacle corridor with dynamic barriers"},
            ),
            (
                "demo-memory-osc-003",
                "demo-opp-fellowship-004",
                "demo-user-student-013",
                "Campus Open Source Sprint 2025 Lessons",
                "Pairing first-year contributors with seasoned alumni mentors drove a 75% PR merge completion rate.",
                "Several newcomers struggled with local environment docker installations; recommend devcontainers.",
                "85 participating students across 12 open source repositories.",
                "42 pull requests merged into major open source repositories including FastAPI, Pydantic, and Scikit-learn.",
                ["open-source", "gsoc", "git", "fastapi", "python"],
                {"event_year": 2025, "merged_pr_count": 42},
            ),
        ]

        for mid, opp_id, auth_id, mtitle, worked, did_not, att, outcome, tags, extra in memories_data:
            existing_mem = db.scalar(select(EventMemory).where(EventMemory.id == mid))
            if not existing_mem:
                db.add(
                    EventMemory(
                        id=mid,
                        institution_id=DEMO_INSTITUTION_ID,
                        opportunity_id=opp_id,
                        author_user_id=auth_id,
                        title=mtitle,
                        what_worked=worked,
                        what_did_not_work=did_not,
                        attendance_notes=att,
                        outcome_summary=outcome,
                        tags=tags,
                        extra_data=extra,
                    )
                )
        db.flush()

        # =====================================================================
        # 12. FOLLOW-UP TASKS (CONNECTED ACTION ITEMS ACROSS TEAMS)
        # =====================================================================
        tasks_data = [
            (
                DEMO_TASK_1_ID,
                DEMO_USER_ID,
                DEMO_USER_ID,
                "Send prospectus to CloudScale Systems for 2026 Hackathon",
                "Follow up on preliminary corporate sponsorship interest and deliver tiered benefits prospectus.",
                now + timedelta(days=7),
                TaskPriority.HIGH,
                TaskSource.HANDOVER,
                DEMO_HANDOVER_ID,
                False,
            ),
            (
                DEMO_TASK_2_ID,
                DEMO_USER_ID,
                DEMO_USER_ID,
                "Audit server cluster allocation for hackathon staging",
                "Verify compute quotas and staging access with Department IT coordinator.",
                now + timedelta(days=12),
                TaskPriority.MEDIUM,
                TaskSource.MANUAL,
                None,
                False,
            ),
            (
                "demo-task-arena-003",
                "demo-user-student-007",
                "demo-user-student-020",
                "Calibrate ultrasonic sensors and obstacle course batteries",
                "Inspect lithium battery health in fire-safe containment before robotics grand prix trials.",
                now + timedelta(days=5),
                TaskPriority.HIGH,
                TaskSource.HANDOVER,
                "demo-handover-robo-002",
                False,
            ),
            (
                "demo-task-mentors-004",
                "demo-user-student-011",
                "demo-user-student-011",
                "Onboard alumni mentors for ICPC mock regional contest",
                "Invite Marcus Chen and Vikram Sengupta to review contest problem test cases.",
                now + timedelta(days=10),
                TaskPriority.MEDIUM,
                TaskSource.MANUAL,
                None,
                False,
            ),
            (
                "demo-task-keynote-005",
                "demo-user-student-005",
                "demo-user-student-005",
                "Confirm keynote timing with Dr. Anita Roy for Generative AI Workshop",
                "Align lab schedule for live model inference demo in Turing Laboratory.",
                now + timedelta(days=15),
                TaskPriority.LOW,
                TaskSource.MANUAL,
                None,
                False,
            ),
            (
                "demo-task-venue-006",
                DEMO_USER_ID,
                "demo-user-student-015",
                "Finalize auditorium audio-visual contract with campus facilities",
                "Ensure microphones, livestream switchers, and high-lumen projectors are reserved.",
                now - timedelta(days=2),
                TaskPriority.HIGH,
                TaskSource.HANDOVER,
                "demo-handover-hack-003",
                True,  # Demonstrates a successfully completed task in the history
            ),
        ]

        for tid, cuid, auid, title, desc, due, prio, src, hid, comp in tasks_data:
            existing_task = db.scalar(select(FollowUpTask).where(FollowUpTask.id == tid))
            if not existing_task:
                db.add(
                    FollowUpTask(
                        id=tid,
                        institution_id=DEMO_INSTITUTION_ID,
                        creator_user_id=cuid,
                        assignee_user_id=auid,
                        title=title,
                        description=desc,
                        due_date=due,
                        priority=prio,
                        source=src,
                        handover_id=hid,
                        is_completed=comp,
                    )
                )
        db.flush()

        # =====================================================================
        # 13. PARTNERSHIPS, SPONSORSHIPS & PROMOTION (CONNECTED ECOSYSTEM)
        # =====================================================================
        partners_data = [
            (
                DEMO_PARTNER_ORG_ID,
                "CloudScale Infrastructure Labs (Demo Partner)",
                "Cloud Computing & Developer Tools",
                "Elena Rostova",
                "partnerships@cloudscale-demo.io",
                "https://cloudscale-demo.io",
                PartnerVerificationStatus.VERIFIED_REPRESENTATIVE,
                "Verified corporate partner for annual hackathon cloud credits and compute prize sponsorship.",
            ),
            (
                "demo-partner-devtools-002",
                "DevTools Global India (Demo Partner)",
                "Hardware Prototyping & Developer Hardware",
                "Saurabh Mukhopadhyay",
                "saurabh@devtools-global-demo.in",
                "https://devtools-global-demo.in",
                PartnerVerificationStatus.VERIFIED_REPRESENTATIVE,
                "Official robotics development kit sponsor providing hardware kits for student competitions.",
            ),
            (
                "demo-partner-ventures-003",
                "Bharat Tech Ventures (Demo Partner)",
                "Venture Capital & Early Stage Incubation",
                "Aditi Singhal",
                "aditi@bharatventures-demo.in",
                "https://bharatventures-demo.in",
                PartnerVerificationStatus.VERIFIED_REPRESENTATIVE,
                "Seed investment partner supporting student entrepreneurship pitch prizes and startup fellowships.",
            ),
        ]

        for pid, pname, ind, cname, cemail, purl, vstat, notes in partners_data:
            existing_partner = db.scalar(select(PartnerOrganization).where(PartnerOrganization.id == pid))
            if not existing_partner:
                db.add(
                    PartnerOrganization(
                        id=pid,
                        institution_id=DEMO_INSTITUTION_ID,
                        name=pname,
                        industry=ind,
                        contact_name=cname,
                        contact_email=cemail,
                        website_url=purl,
                        verification_status=vstat,
                        notes=notes,
                    )
                )
        db.flush()

        # Sponsorship Requests
        sponsorships_data = [
            (
                DEMO_SPONSOR_REQ_ID,
                DEMO_OPP_1_ID,
                DEMO_USER_ID,
                DEMO_PARTNER_ORG_ID,
                "Tier-1 Gold Sponsorship for Apex Innovators 2026",
                SupportType.FINANCIAL,
                "Keynote address, prominent stage branding, dedicated recruiter fast-track booth, participant resume access.",
                "350+ engineering delegates and researchers",
                "USD",
                2500.00,
                now + timedelta(days=14),
                "alex.vance@apextech.edu",
                SponsorshipStatus.UNDER_REVIEW,
                {"cloud_credits_included": True, "booth_space_sqft": 100},
            ),
            (
                "demo-sponsorship-002",
                "demo-opp-event-003",
                "demo-user-student-007",
                "demo-partner-devtools-002",
                "Title Track Sponsorship for Robotics Grand Prix 2026",
                SupportType.IN_KIND,
                "Arena perimeter banners, product demonstration session, custom track challenge obstacle award.",
                "200+ hardware engineering students and robotics clubs",
                "USD",
                1800.00,
                now + timedelta(days=20),
                "aditya.nair.demo@apextech.edu",
                SponsorshipStatus.ACCEPTED,
                {"hardware_starter_kits_count": 30, "arena_branding_sqft": 80},
            ),
            (
                "demo-sponsorship-003",
                "demo-opp-competition-006",
                "demo-user-student-012",
                "demo-partner-ventures-003",
                "Seed Prize Pool for Campus Startup Pitch Fest 2026",
                SupportType.FINANCIAL,
                "Evaluation jury chair seat, direct pipeline to incubator batch, student team seed capital award.",
                "40+ student startup teams and university angel investors",
                "USD",
                3000.00,
                now + timedelta(days=28),
                "neha.verma.demo@apextech.edu",
                SponsorshipStatus.SUBMITTED,
                {"first_look_equity_rights": False, "grant_format": "Non-dilutive seed award"},
            ),
        ]

        for sid, opp_id, uid, pid, obj, stype, benefits, aud, cur, amt, dline, email, stat, terms in sponsorships_data:
            existing_spons = db.scalar(select(SponsorshipRequest).where(SponsorshipRequest.id == sid))
            if not existing_spons:
                db.add(
                    SponsorshipRequest(
                        id=sid,
                        institution_id=DEMO_INSTITUTION_ID,
                        opportunity_id=opp_id,
                        organizer_user_id=uid,
                        partner_organization_id=pid,
                        objective=obj,
                        support_type=stype,
                        proposed_benefits=benefits,
                        intended_audience=aud,
                        budget_currency=cur,
                        budget_amount=amt,
                        deadline=dline,
                        contact_email=email,
                        status=stat,
                        commercial_terms=terms,
                    )
                )
        db.flush()

        # Promotion Campaigns
        campaigns_data = [
            (
                DEMO_CAMPAIGN_ID,
                DEMO_OPP_1_ID,
                DEMO_USER_ID,
                CampaignType.FEATURED_SPOTLIGHT,
                "standard_cross_college",
                150.00,
                "USD",
                [],
                CampaignStatus.ACTIVE,
                now - timedelta(days=2),
                now + timedelta(days=14),
                True,
                "Approved cross-college spotlight for Apex Innovators flagship collegiate hackathon.",
            ),
            (
                "demo-campaign-002",
                "demo-opp-workshop-005",
                "demo-user-student-005",
                CampaignType.CAMPUS_BULLETIN,
                "featured_regional_placement",
                75.00,
                "USD",
                [],
                CampaignStatus.ACTIVE,
                now - timedelta(days=1),
                now + timedelta(days=10),
                True,
                "Approved featured placement for Deep Learning & Generative Models Workshop.",
            ),
        ]

        for cid, opp_id, uid, ctype, ppack, pamt, pcur, targets, cstat, sdate, edate, is_paid, rnotes in campaigns_data:
            existing_camp = db.scalar(select(PromotionCampaign).where(PromotionCampaign.id == cid))
            if not existing_camp:
                db.add(
                    PromotionCampaign(
                        id=cid,
                        source_institution_id=DEMO_INSTITUTION_ID,
                        opportunity_id=opp_id,
                        creator_user_id=uid,
                        campaign_type=ctype,
                        pricing_package=ppack,
                        price_amount=pamt,
                        currency=pcur,
                        target_institution_ids=targets,
                        status=cstat,
                        start_date=sdate,
                        end_date=edate,
                        is_paid_placement=is_paid,
                        review_notes=rnotes,
                    )
                )
        db.flush()

        # =====================================================================
        # 14. ALUMNI DIRECTORY IMPORT AUDIT RECORD
        # =====================================================================
        import_job = db.scalar(select(AlumniImportJob).where(AlumniImportJob.id == "demo-alumni-job-001"))
        if not import_job:
            db.add(
                AlumniImportJob(
                    id="demo-alumni-job-001",
                    institution_id=DEMO_INSTITUTION_ID,
                    uploader_user_id=DEMO_USER_ID,
                    filename="apex_alumni_directory_2020_2024.csv",
                    status=ImportJobStatus.COMMITTED,
                    total_rows=52,
                    accepted_rows=50,
                    skipped_rows=2,
                    rejected_rows=0,
                    validation_errors=[],
                )
            )

        db.commit()
        return {
            "status": "success",
            "message": "Enriched, interconnected demonstration college community seeded successfully.",
            "demo_institution_id": DEMO_INSTITUTION_ID,
            "demo_user_email": (settings.demo_user_email or "demo@eventsignal.local").strip().lower(),
            "community_stats": {
                "users": len(users_specs),
                "units": len(units_data),
                "positions": len(positions_data),
                "opportunities": len(opportunities_data),
                "help_offers": len(help_offers_data),
                "student_needs": len(needs_specs),
                "handovers": len(handovers_data),
                "event_memories": len(memories_data),
                "tasks": len(tasks_data),
                "partners": len(partners_data),
                "sponsorships": len(sponsorships_data),
                "campaigns": len(campaigns_data),
            },
        }

    @staticmethod
    def reset_demo_environment(db: Session, settings: Settings) -> dict[str, Any]:
        """Safely delete all isolated demo data without touching production records."""
        inst = db.scalar(select(Institution).where(Institution.id == DEMO_INSTITUTION_ID))
        if inst:
            # Delete dependent entities where cascade is not automatic or needs clean removal
            db.execute(delete(OpportunityAssessment).where(OpportunityAssessment.opportunity_id.in_(ALL_DEMO_OPPORTUNITY_IDS)))
            db.execute(delete(FieldEvidence).where(FieldEvidence.opportunity_id.in_(ALL_DEMO_OPPORTUNITY_IDS)))
            db.execute(delete(SourceReference).where(SourceReference.opportunity_id.in_(ALL_DEMO_OPPORTUNITY_IDS)))
            db.execute(delete(Opportunity).where(Opportunity.id.in_(ALL_DEMO_OPPORTUNITY_IDS)))
            db.execute(delete(PromotionCampaign).where(PromotionCampaign.source_institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(SponsorshipRequest).where(SponsorshipRequest.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(PartnerOrganization).where(PartnerOrganization.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(AlumniImportJob).where(AlumniImportJob.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(FollowUpTask).where(FollowUpTask.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(EventMemory).where(EventMemory.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(LegacyHandover).where(LegacyHandover.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(HelperMatch).where(HelperMatch.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(StudentNeed).where(StudentNeed.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(HelpOffer).where(HelpOffer.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(StudentProfile).where(StudentProfile.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(AlumniProfile).where(AlumniProfile.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(CampusRoleAssignment).where(CampusRoleAssignment.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(CampusPositionDefinition).where(CampusPositionDefinition.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(OrganizationalUnit).where(OrganizationalUnit.institution_id == DEMO_INSTITUTION_ID))
            db.execute(delete(InstitutionMembership).where(InstitutionMembership.institution_id == DEMO_INSTITUTION_ID))
            db.delete(inst)

        # Remove demo accounts (strictly verifying is_demo marker to prevent touching real users)
        # Note: We preserve the primary presenter DEMO_USER_ID account so the presenter's active session
        # token remains valid to re-seed or perform demo admin operations. All memberships and
        # institution-scoped assets for the presenter were cleanly deleted above.
        for uid in ALL_DEMO_USER_IDS:
            if uid == DEMO_USER_ID:
                continue
            u = db.scalar(select(User).where(User.id == uid))
            if u:
                if u.extra_data and u.extra_data.get("is_demo") is True:
                    db.delete(u)
                else:
                    logger.warning(
                        "Skipping deletion of user ID '%s' (%s) during demo reset: missing is_demo marker.",
                        uid,
                        u.email,
                    )

        db.commit()
        return {
            "status": "success",
            "message": "Demonstration environment reset cleanly. Production records unaffected.",
        }
