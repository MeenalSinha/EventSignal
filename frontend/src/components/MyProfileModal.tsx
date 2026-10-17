import { useEffect, useState } from "react";
import { fetchMyAlumniProfile, fetchMyStudentProfile, saveMyAlumniProfile, saveMyStudentProfile } from "../services/profileService";
import type { UserProfile } from "../types/auth";
import type { AlumniProfile, AlumniVisibility, StudentProfile, StudentVisibility } from "../types/profile";

interface MyProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserProfile;
}

export function MyProfileModal({ isOpen, onClose, currentUser }: MyProfileModalProps) {
  const activeMemberships = currentUser.memberships.filter((m) => m.status === "active");
  const [selectedInstId, setSelectedInstId] = useState<string>(
    activeMemberships[0]?.institution_id ?? ""
  );

  const currentMembership = activeMemberships.find((m) => m.institution_id === selectedInstId);
  const isAlumni = currentMembership?.role === "alumni";

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Student profile state
  const [studentHeadline, setStudentHeadline] = useState("");
  const [studentBio, setStudentBio] = useState("");
  const [studentDegree, setStudentDegree] = useState("");
  const [studentGradYear, setStudentGradYear] = useState<number | "">("");
  const [studentSkills, setStudentSkills] = useState("");
  const [studentInterests, setStudentInterests] = useState("");
  const [studentGoals, setStudentGoals] = useState("");
  const [studentVisibility, setStudentVisibility] = useState<StudentVisibility>("institution_only");

  // Alumni profile state
  const [alumniTitle, setAlumniTitle] = useState("");
  const [alumniOrg, setAlumniOrg] = useState("");
  const [alumniDomain, setAlumniDomain] = useState("");
  const [alumniIndustry, setAlumniIndustry] = useState("");
  const [alumniExpYears, setAlumniExpYears] = useState<number | "">("");
  const [alumniSkills, setAlumniSkills] = useState("");
  const [alumniTopics, setAlumniTopics] = useState("");
  const [alumniBio, setAlumniBio] = useState("");
  const [willingToHelp, setWillingToHelp] = useState(true);
  const [monthlyLimit, setMonthlyLimit] = useState(5);
  const [alumniVisibility, setAlumniVisibility] = useState<AlumniVisibility>("students_only");

  useEffect(() => {
    if (!isOpen || !selectedInstId) return;
    let isMounted = true;

    const toListString = (val: string[] | string | null | undefined): string => {
      if (!val) return "";
      if (Array.isArray(val)) return val.join(", ");
      return String(val);
    };

    if (isAlumni) {
      fetchMyAlumniProfile(selectedInstId)
        .then((p: AlumniProfile | null) => {
          if (!isMounted) return;
          if (p) {
            setAlumniTitle(p.current_title || (p as any).extra_data?.current_title || p.professional_domain || "");
            setAlumniOrg(p.current_organization || (p as any).extra_data?.current_organization || "");
            setAlumniDomain(p.professional_domain || "");
            setAlumniIndustry(p.industry || "");
            setAlumniExpYears(p.years_of_experience ?? (p as any).years_experience ?? "");
            setAlumniSkills(toListString(p.skills));
            setAlumniTopics(toListString(p.mentoring_topics ?? (p as any).mentoring_interests));
            setAlumniBio(p.bio || (p as any).extra_data?.bio || "");
            setWillingToHelp(p.willing_to_help ?? (p as any).willing_to_connect ?? true);
            setMonthlyLimit(p.monthly_request_limit ?? (p as any).monthly_connection_limit ?? 5);
            setAlumniVisibility(p.visibility);
          } else {
            setAlumniTitle("");
            setAlumniOrg("");
            setAlumniDomain("");
            setAlumniIndustry("");
            setAlumniExpYears("");
            setAlumniSkills("");
            setAlumniTopics("");
            setAlumniBio("");
            setWillingToHelp(true);
            setMonthlyLimit(5);
            setAlumniVisibility("students_only");
          }
          setLoading(false);
        })
        .catch((err: unknown) => {
          if (!isMounted) return;
          if (err instanceof Error) setError(err.message);
          setLoading(false);
        });
    } else {
      fetchMyStudentProfile(selectedInstId)
        .then((p: StudentProfile | null) => {
          if (!isMounted) return;
          if (p) {
            setStudentHeadline(p.headline || (p as any).extra_data?.headline || (p as any).display_name || "");
            setStudentBio(p.bio || (p as any).extra_data?.bio || "");
            setStudentDegree(p.degree_level || (p as any).extra_data?.degree_level || "");
            setStudentGradYear(p.graduation_year ?? (p as any).extra_data?.graduation_year ?? "");
            setStudentSkills(toListString(p.skills));
            setStudentInterests(toListString(p.interests));
            setStudentGoals(toListString(p.career_goals));
            setStudentVisibility(p.visibility);
          } else {
            setStudentHeadline("");
            setStudentBio("");
            setStudentDegree("");
            setStudentGradYear("");
            setStudentSkills("");
            setStudentInterests("");
            setStudentGoals("");
            setStudentVisibility("institution_only");
          }
          setLoading(false);
        })
        .catch((err: unknown) => {
          if (!isMounted) return;
          if (err instanceof Error) setError(err.message);
          setLoading(false);
        });
    }

    return () => {
      isMounted = false;
    };
  }, [isOpen, selectedInstId, isAlumni]);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);

    try {
      if (isAlumni) {
        await saveMyAlumniProfile(selectedInstId, {
          current_title: alumniTitle.trim() || null,
          current_organization: alumniOrg.trim() || null,
          professional_domain: alumniDomain.trim() || null,
          industry: alumniIndustry.trim() || null,
          years_of_experience: alumniExpYears === "" ? null : Number(alumniExpYears),
          skills: alumniSkills.split(",").map((s) => s.trim()).filter(Boolean),
          mentoring_topics: alumniTopics.split(",").map((s) => s.trim()).filter(Boolean),
          bio: alumniBio.trim() || null,
          willing_to_help: willingToHelp,
          monthly_request_limit: Number(monthlyLimit) || 5,
          visibility: alumniVisibility,
        });
        setSuccess("Alumni profile successfully updated.");
      } else {
        await saveMyStudentProfile(selectedInstId, {
          headline: studentHeadline.trim() || null,
          bio: studentBio.trim() || null,
          degree_level: studentDegree.trim() || null,
          graduation_year: studentGradYear === "" ? null : Number(studentGradYear),
          skills: studentSkills.split(",").map((s) => s.trim()).filter(Boolean),
          interests: studentInterests.split(",").map((s) => s.trim()).filter(Boolean),
          career_goals: studentGoals.split(",").map((s) => s.trim()).filter(Boolean),
          visibility: studentVisibility,
        });
        setSuccess("Student profile successfully updated.");
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save profile.";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl bg-paper p-6 shadow-xl border border-line">
        <div className="flex items-center justify-between border-b border-line pb-4">
          <div>
            <h2 className="font-display text-xl font-semibold">
              {isAlumni ? "Alumni Professional Profile" : "Student Member Profile"}
            </h2>
            <p className="text-xs text-ink-soft">
              Campus-scoped identity for {currentMembership?.institution_name || "your college workspace"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-ink-soft hover:bg-paper-warm hover:text-ink"
            aria-label="Close"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {activeMemberships.length > 1 && (
          <div className="mt-4">
            <label className="block text-xs font-semibold text-ink-soft mb-1">
              Select College Workspace
            </label>
            <select
              value={selectedInstId}
              onChange={(e) => {
                setLoading(true);
                setSelectedInstId(e.target.value);
              }}
              className="w-full rounded-xl border border-line bg-paper px-3 py-2 text-sm"
            >
              {activeMemberships.map((m) => (
                <option key={m.institution_id} value={m.institution_id}>
                  {m.institution_name || m.institution_slug || m.institution_id} ({m.role})
                </option>
              ))}
            </select>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            {error}
          </div>
        )}

        {success && (
          <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700">
            {success}
          </div>
        )}

        <div className="mt-3 flex items-start gap-2 rounded-xl bg-amber-50 border border-amber-200/60 p-2.5 text-[11px] text-amber-800">
          <svg className="h-4 w-4 text-amber-700 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <strong>Declaration Policy:</strong> Profile skills, career interests, and experience are self-reported and not officially verified by institutional administration.
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-ink-soft">Loading profile...</div>
        ) : (
          <form onSubmit={handleSave} className="mt-4 space-y-4">
            {isAlumni ? (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-ink-soft mb-1">Current Job Title</label>
                    <input
                      type="text"
                      value={alumniTitle}
                      onChange={(e) => setAlumniTitle(e.target.value)}
                      placeholder="e.g. Senior Software Engineer"
                      className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-ink-soft mb-1">Company / Organization</label>
                    <input
                      type="text"
                      value={alumniOrg}
                      onChange={(e) => setAlumniOrg(e.target.value)}
                      placeholder="e.g. Stripe, MIT Lab"
                      className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-ink-soft mb-1">Professional Domain</label>
                    <input
                      type="text"
                      value={alumniDomain}
                      onChange={(e) => setAlumniDomain(e.target.value)}
                      placeholder="e.g. Cloud Infrastructure, BioTech"
                      className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-ink-soft mb-1">Years of Experience</label>
                    <input
                      type="number"
                      min={0}
                      max={70}
                      value={alumniExpYears}
                      onChange={(e) => setAlumniExpYears(e.target.value === "" ? "" : Number(e.target.value))}
                      placeholder="e.g. 5"
                      className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Skills (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={alumniSkills}
                    onChange={(e) => setAlumniSkills(e.target.value)}
                    placeholder="Python, Distributed Systems, System Design"
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Mentoring & Guidance Topics (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={alumniTopics}
                    onChange={(e) => setAlumniTopics(e.target.value)}
                    placeholder="Portfolio Reviews, Mock Interviews, Grad School"
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">Professional Bio</label>
                  <textarea
                    rows={2}
                    value={alumniBio}
                    onChange={(e) => setAlumniBio(e.target.value)}
                    placeholder="Brief background and areas where you can help students..."
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>

                <div className="flex items-center justify-between rounded-xl border border-line p-3">
                  <div>
                    <div className="text-xs font-semibold text-ink">Willing to Receive Help Requests</div>
                    <div className="text-[11px] text-ink-soft">
                      When turned off, students cannot submit connection or guidance requests to you.
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={willingToHelp}
                    onChange={(e) => setWillingToHelp(e.target.checked)}
                    className="h-4 w-4 rounded accent-ink"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-ink-soft mb-1">Monthly Request Limit</label>
                    <input
                      type="number"
                      min={1}
                      max={50}
                      value={monthlyLimit}
                      onChange={(e) => setMonthlyLimit(Number(e.target.value))}
                      className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-ink-soft mb-1">Profile Visibility</label>
                    <select
                      value={alumniVisibility}
                      onChange={(e) => setAlumniVisibility(e.target.value as AlumniVisibility)}
                      className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                    >
                      <option value="students_only">College Students & Faculty Only</option>
                      <option value="alumni_only">Alumni Peers Only</option>
                      <option value="public">Entire College Community</option>
                      <option value="private">Private (Only You)</option>
                    </select>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">Headline</label>
                  <input
                    type="text"
                    value={studentHeadline}
                    onChange={(e) => setStudentHeadline(e.target.value)}
                    placeholder="e.g. Sophomore Computer Science student interested in AI safety"
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-ink-soft mb-1">Degree Level</label>
                    <input
                      type="text"
                      value={studentDegree}
                      onChange={(e) => setStudentDegree(e.target.value)}
                      placeholder="e.g. B.Tech, B.S., M.S."
                      className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-ink-soft mb-1">Graduation Year</label>
                    <input
                      type="number"
                      min={2000}
                      max={2035}
                      value={studentGradYear}
                      onChange={(e) => setStudentGradYear(e.target.value === "" ? "" : Number(e.target.value))}
                      placeholder="e.g. 2027"
                      className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Declared Skills (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={studentSkills}
                    onChange={(e) => setStudentSkills(e.target.value)}
                    placeholder="Python, React, Machine Learning, UI Design"
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Areas of Interest (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={studentInterests}
                    onChange={(e) => setStudentInterests(e.target.value)}
                    placeholder="Open Source, Hackathons, Research, Product Management"
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Career Goals (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={studentGoals}
                    onChange={(e) => setStudentGoals(e.target.value)}
                    placeholder="Summer Internship, Research Assistantship, Startup"
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">Bio / Statement</label>
                  <textarea
                    rows={2}
                    value={studentBio}
                    onChange={(e) => setStudentBio(e.target.value)}
                    placeholder="Brief summary of what you are working on or seeking help with..."
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">Profile Visibility</label>
                  <select
                    value={studentVisibility}
                    onChange={(e) => setStudentVisibility(e.target.value as StudentVisibility)}
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  >
                    <option value="institution_only">College Community (Students, Alumni, Faculty)</option>
                    <option value="public">Authenticated Platform Members</option>
                    <option value="private">Private (Only You)</option>
                  </select>
                </div>
              </>
            )}

            <div className="flex justify-end gap-2 border-t border-line pt-4">
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-line px-4 py-2 text-xs font-semibold text-ink hover:bg-paper-warm"
              >
                Close
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper transition hover:bg-ink-soft disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Profile"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
