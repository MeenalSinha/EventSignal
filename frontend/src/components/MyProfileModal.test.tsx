import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { jsonResponse, stubFetch } from "../test/helpers";
import type { UserProfile } from "../types/auth";
import type { AlumniProfile, StudentProfile } from "../types/profile";
import { MyProfileModal } from "./MyProfileModal";

const testStudentUser: UserProfile = {
  user: {
    id: "usr-student-1",
    email: "student@campus.edu",
    full_name: "Alice Student",
    is_active: true,
    is_superuser: false,
    created_at: "2026-01-01T00:00:00Z",
  },
  memberships: [
    {
      id: "mem-1",
      institution_id: "inst-1",
      institution_name: "Tech Institute",
      institution_slug: "tech-inst",
      role: "student",
      status: "active",
      joined_at: "2026-01-01T00:00:00Z",
    },
  ],
};

const testAlumniUser: UserProfile = {
  user: {
    id: "usr-alumni-1",
    email: "alumni@campus.edu",
    full_name: "Bob Alumnus",
    is_active: true,
    is_superuser: false,
    created_at: "2026-01-01T00:00:00Z",
  },
  memberships: [
    {
      id: "mem-2",
      institution_id: "inst-1",
      institution_name: "Tech Institute",
      institution_slug: "tech-inst",
      role: "alumni",
      status: "active",
      joined_at: "2026-01-01T00:00:00Z",
    },
  ],
};

const mockStudentProfile: StudentProfile = {
  id: "sp-1",
  user_id: "usr-student-1",
  institution_id: "inst-1",
  membership_id: "mem-1",
  headline: "Junior studying Systems",
  bio: "Passionate about databases.",
  degree_level: "B.S. CS",
  graduation_year: 2027,
  skills: ["Python", "PostgreSQL"],
  interests: ["Distributed Systems"],
  career_goals: ["Backend Engineer"],
  portfolio_url: null,
  github_url: null,
  linkedin_url: null,
  preferred_opportunity_types: ["Internship"],
  location_preference: "Remote",
  visibility: "institution_only",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockAlumniProfile: AlumniProfile = {
  id: "ap-1",
  user_id: "usr-alumni-1",
  institution_id: "inst-1",
  membership_id: "mem-2",
  current_title: "Staff Engineer",
  current_organization: "Acme Corp",
  professional_domain: "Cloud Infrastructure",
  industry: "Technology",
  years_of_experience: 7,
  skills: ["Kubernetes", "Go"],
  mentoring_topics: ["System Design", "Mock Interviews"],
  bio: "Happy to help students prepare for technical interviews.",
  linkedin_url: null,
  website_url: null,
  willing_to_help: true,
  preferred_contact_method: "virtual",
  monthly_request_limit: 4,
  active_requests_this_month: 0,
  visibility: "students_only",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("MyProfileModal", () => {
  it("renders student profile and allows saving updates", async () => {
    stubFetch({
      "/api/v1/profiles/student/me": () => jsonResponse(mockStudentProfile),
      "/api/v1/profiles/student": () => {
        return jsonResponse({
          ...mockStudentProfile,
          headline: "Updated Headline",
        });
      },
    });

    const onClose = vi.fn();
    render(<MyProfileModal isOpen={true} onClose={onClose} currentUser={testStudentUser} />);

    expect(screen.getByText("Student Member Profile")).toBeInTheDocument();
    expect(await screen.findByDisplayValue("Junior studying Systems")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Python, PostgreSQL")).toBeInTheDocument();

    const saveButton = screen.getByRole("button", { name: "Save Profile" });
    await userEvent.click(saveButton);

    expect(await screen.findByText("Student profile successfully updated.")).toBeInTheDocument();
  });

  it("renders alumni profile and allows toggling willing to help", async () => {
    stubFetch({
      "/api/v1/profiles/alumni/me": () => jsonResponse(mockAlumniProfile),
      "/api/v1/profiles/alumni": () => jsonResponse(mockAlumniProfile),
    });

    const onClose = vi.fn();
    render(<MyProfileModal isOpen={true} onClose={onClose} currentUser={testAlumniUser} />);

    expect(screen.getByText("Alumni Professional Profile")).toBeInTheDocument();
    expect(await screen.findByDisplayValue("Staff Engineer")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Willing to Receive Help Requests")).toBeInTheDocument();

    const saveButton = screen.getByRole("button", { name: "Save Profile" });
    await userEvent.click(saveButton);

    expect(await screen.findByText("Alumni profile successfully updated.")).toBeInTheDocument();
  });
});
