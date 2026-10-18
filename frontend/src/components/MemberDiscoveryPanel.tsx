import { useCallback, useEffect, useMemo, useState } from "react";
import { discoverMembers } from "../services/profileService";
import type { UserProfile } from "../types/auth";
import type { MemberDiscovery } from "../types/profile";

interface MemberDiscoveryPanelProps {
  currentUser: UserProfile | null;
  onOpenAuth: () => void;
  onSelectMemberForOffers?: (userId: string) => void;
}

export function MemberDiscoveryPanel({
  currentUser,
  onOpenAuth,
  onSelectMemberForOffers,
}: MemberDiscoveryPanelProps) {
  const activeMemberships = useMemo(
    () => currentUser?.memberships.filter((m) => m.status === "active") || [],
    [currentUser]
  );

  const [selectedInstId, setSelectedInstId] = useState<string>("");
  const effectiveInstId = selectedInstId || activeMemberships[0]?.institution_id || "";

  const [roleFilter, setRoleFilter] = useState<string>("");
  const [searchInput, setSearchInput] = useState<string>("");
  const [submittedQuery, setSubmittedQuery] = useState<string>("");
  const [members, setMembers] = useState<MemberDiscovery[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadTrigger, setReloadTrigger] = useState(0);

  const loadMembers = useCallback(() => {
    setLoading(true);
    setError(null);
    setReloadTrigger((n) => n + 1);
  }, []);

  useEffect(() => {
    if (!currentUser || !effectiveInstId) return;
    let isMounted = true;

    discoverMembers(effectiveInstId, roleFilter || undefined, submittedQuery.trim() || undefined)
      .then((data) => {
        if (!isMounted) return;
        setMembers(data);
        setError(null);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (!isMounted) return;
        if (err instanceof Error) setError(err.message);
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [currentUser, effectiveInstId, roleFilter, submittedQuery, reloadTrigger]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSubmittedQuery(searchInput);
  };

  if (!currentUser) {
    return (
      <div className="rounded-2xl border border-line bg-paper p-8 text-center">
        <h3 className="font-display text-lg font-semibold text-ink">Campus Network Discovery</h3>
        <p className="mt-2 text-sm text-ink-soft">
          Sign in and join your college workspace to discover students, alumni mentors, and official campus leaders.
        </p>
        <button
          onClick={onOpenAuth}
          className="mt-4 rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft"
        >
          Sign In to Access Network
        </button>
      </div>
    );
  }

  if (activeMemberships.length === 0) {
    return (
      <div className="rounded-2xl border border-line bg-paper p-8 text-center">
        <h3 className="font-display text-lg font-semibold text-ink">No Active College Memberships</h3>
        <p className="mt-2 text-sm text-ink-soft">
          You are authenticated, but not yet an active member of any college workspace.
        </p>
        <p className="mt-1 text-xs text-ink-soft">
          Visit the College Workspaces tab to onboard or request membership to your campus.
        </p>
      </div>
    );
  }

  const currentInst = activeMemberships.find((m) => m.institution_id === effectiveInstId);

  return (
    <div className="space-y-6">
      {/* Workspace & Search Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-3">
          {activeMemberships.length > 1 ? (
            <select
              value={effectiveInstId}
              onChange={(e) => {
                setLoading(true);
                setSelectedInstId(e.target.value);
              }}
              className="rounded-xl border border-line bg-paper px-3 py-1.5 text-xs font-semibold text-ink"
            >
              {activeMemberships.map((m) => (
                <option key={m.institution_id} value={m.institution_id}>
                  {m.institution_name || m.institution_slug || "College Workspace"}
                </option>
              ))}
            </select>
          ) : (
            <div className="flex items-center gap-1.5 rounded-xl border border-line bg-paper-warm px-3 py-1.5 text-xs font-semibold text-ink">
              <svg className="h-3.5 w-3.5 text-teal shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span>{currentInst?.institution_name || currentInst?.institution_slug || "Campus Network"}</span>
            </div>
          )}

          <div className="flex items-center gap-1 rounded-xl bg-paper-warm p-1 text-xs font-medium">
            <button
              onClick={() => {
                setLoading(true);
                setRoleFilter("");
              }}
              className={`rounded-lg px-2.5 py-1 transition ${
                roleFilter === "" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
              }`}
            >
              All Members
            </button>
            <button
              onClick={() => {
                setLoading(true);
                setRoleFilter("student");
              }}
              className={`rounded-lg px-2.5 py-1 transition ${
                roleFilter === "student" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
              }`}
            >
              Students
            </button>
            <button
              onClick={() => {
                setLoading(true);
                setRoleFilter("alumni");
              }}
              className={`rounded-lg px-2.5 py-1 transition ${
                roleFilter === "alumni" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
              }`}
            >
              Alumni
            </button>
            <button
              onClick={() => {
                setLoading(true);
                setRoleFilter("faculty");
              }}
              className={`rounded-lg px-2.5 py-1 transition ${
                roleFilter === "faculty" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
              }`}
            >
              Faculty
            </button>
          </div>
        </div>

        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by name, skill, topic..."
            className="rounded-xl border border-line bg-paper px-3 py-1.5 text-xs text-ink placeholder:text-ink-soft focus:outline-none focus:ring-1 focus:ring-ink"
          />
          <button
            type="submit"
            className="rounded-xl bg-ink px-3 py-1.5 text-xs font-semibold text-paper hover:bg-ink-soft"
          >
            Search
          </button>
        </form>
      </div>

      {error && (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          <span>Failed to load campus members: {error}</span>
          <button
            type="button"
            onClick={loadMembers}
            className="rounded-lg bg-rose-700 px-2.5 py-1 text-xs font-semibold text-white hover:bg-rose-800 shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center text-sm text-ink-soft">
          Searching college network records...
        </div>
      ) : members.length === 0 ? (
        <div className="rounded-2xl border border-line bg-paper p-10 text-center">
          <h4 className="font-display text-base font-semibold text-ink">No Members Found</h4>
          <p className="mt-1 text-xs text-ink-soft">
            {submittedQuery
              ? `No authorized members in this college workspace matched "${submittedQuery}".`
              : "No members have declared discoverable profiles for this role in this college yet."}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {members.map((member) => {
            const role = member.membership_role || (member as any).role || "member";
            const isAlum = role === "alumni";
            const sp = member.student_profile;
            const ap = member.alumni_profile;
            const positions: string[] = Array.isArray(member.campus_positions)
              ? member.campus_positions
              : Array.isArray((member as any).official_positions)
              ? (member as any).official_positions
              : [];

            return (
              <div
                key={member.user_id}
                className="flex flex-col justify-between rounded-2xl border border-line bg-paper p-5 shadow-sm transition hover:shadow-md"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="font-display font-semibold text-ink">{member.full_name}</h4>
                      <span className="inline-block mt-0.5 rounded-md bg-paper-warm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-ink-soft">
                        {role}
                      </span>
                    </div>

                    {member.active_help_offers_count > 0 && (
                      <span className="rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                        {member.active_help_offers_count} Help {member.active_help_offers_count === 1 ? "Offer" : "Offers"}
                      </span>
                    )}
                  </div>

                  {/* Verified campus leadership appointments */}
                  {positions.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {positions.map((pos, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1 rounded-md bg-blue-50 border border-blue-200 px-2 py-0.5 text-[10px] font-medium text-blue-800"
                        >
                          <svg className="h-3 w-3 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                          </svg>
                          <span>{pos}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Alumni details */}
                  {isAlum && ap && (
                    <div className="mt-3 text-xs text-ink space-y-1.5">
                      {(ap.current_title || ap.current_organization) && (
                        <div className="font-medium">
                          {ap.current_title} {ap.current_organization ? `at ${ap.current_organization}` : ""}
                        </div>
                      )}
                      {ap.professional_domain && (
                        <div className="text-[11px] text-ink-soft">
                          Domain: {ap.professional_domain} {ap.years_of_experience ? `• ${ap.years_of_experience} yrs exp` : ""}
                        </div>
                      )}
                      {ap.mentoring_topics && (
                        <div className="mt-2">
                          <span className="text-[10px] font-semibold text-ink-soft uppercase tracking-wider">
                            Willing to help with:
                          </span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {(Array.isArray(ap.mentoring_topics) ? ap.mentoring_topics : String(ap.mentoring_topics).split(",").map((s) => s.trim()).filter(Boolean)).map((t, i) => (
                              <span key={i} className="rounded bg-paper-warm px-1.5 py-0.5 text-[10px] text-ink">
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {ap.skills && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {(Array.isArray(ap.skills) ? ap.skills : String(ap.skills).split(",").map((s) => s.trim()).filter(Boolean)).map((s, i) => (
                            <span key={i} className="rounded bg-paper-warm/70 px-1.5 py-0.5 text-[10px] text-ink-soft">
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Student details */}
                  {!isAlum && sp && (
                    <div className="mt-3 text-xs text-ink space-y-1.5">
                      {sp.headline && <div className="font-medium text-ink-soft">{sp.headline}</div>}
                      {(sp.degree_level || sp.graduation_year) && (
                        <div className="text-[11px] text-ink-soft">
                          {sp.degree_level} {sp.graduation_year ? `Class of ${sp.graduation_year}` : ""}
                        </div>
                      )}
                      {sp.skills && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {(Array.isArray(sp.skills) ? sp.skills : String(sp.skills).split(",").map((s) => s.trim()).filter(Boolean)).map((s, i) => (
                            <span key={i} className="rounded bg-paper-warm px-1.5 py-0.5 text-[10px] text-ink">
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                      {sp.career_goals && (
                        <div className="mt-1 flex items-center gap-1 text-[11px] text-ink-soft">
                          <svg className="h-3.5 w-3.5 text-ink-soft shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span>Goals: {Array.isArray(sp.career_goals) ? sp.career_goals.join(", ") : String(sp.career_goals)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {!sp && !ap && (
                    <div className="mt-3 text-[11px] italic text-ink-soft">
                      No self-reported public profile attributes declared.
                    </div>
                  )}
                </div>

                {member.active_help_offers_count > 0 && onSelectMemberForOffers && (
                  <div className="mt-4 border-t border-line pt-3">
                    <button
                      onClick={() => onSelectMemberForOffers(member.user_id)}
                      className="w-full rounded-xl bg-paper-warm py-1.5 text-center text-xs font-semibold text-ink hover:bg-paper-warm/80"
                    >
                      View Help Offers ({member.active_help_offers_count})
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
