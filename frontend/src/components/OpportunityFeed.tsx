import { useMemo, useState } from "react";
import type { Opportunity } from "../types/opportunity";
import type { ResourceState } from "../hooks/useRemoteResource";
import type { OpportunityList } from "../services/eventsService";

const EMPTY_OPPORTUNITIES: Opportunity[] = [];

interface OpportunityFeedProps {
  eventsState: ResourceState<OpportunityList>;
  onRetry: () => void;
  onSelectOpportunity: (opportunity: Opportunity) => void;
  onSubmitOpportunity: () => void;
  activeCategory: string;
  onCategoryChange: (category: string) => void;
  searchQuery: string;
  savedOpportunityIds: Set<string>;
  onToggleSave: (id: string) => void;
}

export function OpportunityFeed({
  eventsState,
  onRetry,
  onSelectOpportunity,
  onSubmitOpportunity,
  activeCategory,
  onCategoryChange,
  searchQuery,
  savedOpportunityIds,
  onToggleSave,
}: OpportunityFeedProps) {
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);
  const [filterMode, setFilterMode] = useState<string>("all");
  const [filterEvidence, setFilterEvidence] = useState<string>("all");

  const categories = [
    { id: "all", label: "For You" },
    { id: "opportunity", label: "Opportunities" },
    { id: "campus_event", label: "Campus Events" },
    { id: "hackathon", label: "Hackathons" },
    { id: "internship", label: "Internships" },
    { id: "research", label: "Research" },
    { id: "workshop", label: "Workshops" },
  ];

  // Raw opportunities from the API
  const allOpportunities = eventsState.status === "success" ? eventsState.data.items : EMPTY_OPPORTUNITIES;

  // Filter opportunities based on active category, search query, mode, and evidence
  const filteredOpportunities = useMemo(() => {
    return allOpportunities.filter((op: Opportunity) => {
      // 1. Category filter
      if (activeCategory !== "all") {
        const type = (op.opportunity_type || "").toLowerCase();
        if (activeCategory === "campus_event" && !type.includes("event") && !type.includes("campus")) {
          return false;
        }
        if (activeCategory === "hackathon" && !type.includes("hackathon")) {
          return false;
        }
        if (activeCategory === "internship" && !type.includes("internship") && !type.includes("job")) {
          return false;
        }
        if (activeCategory === "research" && !type.includes("research")) {
          return false;
        }
        if (activeCategory === "workshop" && !type.includes("workshop")) {
          return false;
        }
      }

      // 2. Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const title = (op.title || op.event_name || "").toLowerCase();
        const org = (op.organizer || "").toLowerCase();
        const loc = (op.location || "").toLowerCase();
        const skills = (op.skills_required || "").toLowerCase();
        if (!title.includes(q) && !org.includes(q) && !loc.includes(q) && !skills.includes(q)) {
          return false;
        }
      }

      // 3. Mode filter
      if (filterMode !== "all") {
        const mode = (op.mode || "").toLowerCase();
        if (filterMode === "remote" && !mode.includes("remote") && !mode.includes("virtual")) {
          return false;
        }
        if (filterMode === "in_person" && !mode.includes("person") && !mode.includes("offline")) {
          return false;
        }
        if (filterMode === "hybrid" && !mode.includes("hybrid")) {
          return false;
        }
      }

      // 4. Evidence filter
      if (filterEvidence !== "all") {
        const evidenceCount = op.evidence?.length ?? 0;
        if (filterEvidence === "strong" && evidenceCount < 2) return false;
        if (filterEvidence === "assessed" && evidenceCount === 0) return false;
        if (filterEvidence === "unassessed" && evidenceCount > 0) return false;
      }

      return true;
    });
  }, [allOpportunities, activeCategory, searchQuery, filterMode, filterEvidence]);

  // Format relative time helper
  const getRelativeTime = (isoString?: string): string => {
    if (!isoString) return "Recently";
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
      if (diffDays <= 0) return "Today";
      if (diffDays === 1) return "1 day ago";
      if (diffDays < 30) return `${diffDays} days ago`;
      return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch {
      return "Recently";
    }
  };

  // Format deadline helper
  const formatDeadline = (isoString?: string | null): string | null => {
    if (!isoString) return null;
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
    } catch {
      return null;
    }
  };

  return (
    <section
      role="region"
      aria-label="Event workspace"
      className="flex flex-col gap-3.5"
    >
      {/* 1. Category Filter Tabs & Filter Drawer Toggle */}
      <div className="flex items-center justify-between border-b border-line pb-0 px-1">
        <div className="flex overflow-x-auto scrollbar-none gap-4 sm:gap-6">
          {categories.map((cat) => {
            const isActive = activeCategory === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => onCategoryChange(cat.id)}
                className={`relative pb-2.5 text-xs sm:text-sm font-semibold transition whitespace-nowrap ${
                  isActive ? "text-teal" : "text-ink-soft hover:text-ink"
                }`}
              >
                <span>{cat.label}</span>
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2.5px] rounded-full bg-teal" />
                )}
              </button>
            );
          })}
        </div>

        <button
          type="button"
          onClick={() => setIsFilterDrawerOpen(!isFilterDrawerOpen)}
          className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-semibold transition mb-1.5 shrink-0 ${
            isFilterDrawerOpen
              ? "border-teal bg-teal-wash text-teal"
              : "border-line bg-card text-ink-soft hover:border-ink-soft hover:text-ink"
          }`}
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          <span>Filters</span>
        </button>
      </div>

      {/* Filter Options Bar (collapsible) */}
      {isFilterDrawerOpen && (
        <div className="rounded-xl border border-line bg-card p-3 shadow-xs flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-ink-soft">Mode:</span>
            <select
              value={filterMode}
              onChange={(e) => setFilterMode(e.target.value)}
              className="rounded-md border border-line bg-page px-2 py-1 text-xs text-ink focus:outline-hidden focus:border-teal"
            >
              <option value="all">All Modes</option>
              <option value="remote">Remote / Virtual</option>
              <option value="in_person">In-Person</option>
              <option value="hybrid">Hybrid</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-semibold text-ink-soft">Evidence:</span>
            <select
              value={filterEvidence}
              onChange={(e) => setFilterEvidence(e.target.value)}
              className="rounded-md border border-line bg-page px-2 py-1 text-xs text-ink focus:outline-hidden focus:border-teal"
            >
              <option value="all">All Evidence Levels</option>
              <option value="strong">Strong (2+ Sources)</option>
              <option value="assessed">Assessed Only</option>
              <option value="unassessed">Pending Assessment</option>
            </select>
          </div>

          {(filterMode !== "all" || filterEvidence !== "all") && (
            <button
              onClick={() => {
                setFilterMode("all");
                setFilterEvidence("all");
              }}
              className="text-teal hover:underline text-xs font-medium ml-auto"
            >
              Reset filters
            </button>
          )}
        </div>
      )}

      {/* 2. Loading State */}
      {eventsState.status === "loading" && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-line bg-card py-16 px-4 text-center shadow-xs">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-teal mb-3" />
          <h3 className="text-sm font-semibold text-ink">Loading your events</h3>
          <p className="mt-1 text-xs text-ink-soft">Connecting to institutional servers...</p>
        </div>
      )}

      {/* 3. Error State */}
      {eventsState.status === "error" && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-alert/30 bg-alert-wash/30 py-12 px-6 text-center shadow-xs">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-alert-wash text-alert mb-2">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-sm font-bold text-ink">Feed Network Offline</p>
          <h3 className="text-xs font-semibold text-ink-soft mt-0.5">Your events could not be loaded</h3>
          <p className="mt-1 max-w-sm text-xs text-ink-soft">
            {eventsState.error?.message || "A network or server error occurred while retrieving opportunities."}
          </p>
          <div className="mt-4 flex gap-2">
            <button
              type="button"
              onClick={onRetry}
              className="rounded-lg bg-teal px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-teal-deep transition"
            >
              Try again
            </button>
            <button
              type="button"
              onClick={onRetry}
              className="rounded-lg border border-line bg-card px-3 py-1.5 text-xs font-semibold text-ink shadow-xs hover:bg-page transition"
            >
              Retry connection
            </button>
          </div>
        </div>
      )}

      {/* 4. Empty State (When zero opportunities stored) */}
      {eventsState.status === "success" && allOpportunities.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-line bg-card py-16 px-6 text-center shadow-xs">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-teal-wash text-teal mb-3">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-ink">The workspace is ready, with no events yet</h3>
          <p className="mt-1.5 max-w-md text-xs text-ink-soft leading-relaxed">
            Ingest and verify real opportunities from hackathons, internships, campus workshops, and open-source programs.
          </p>
          <button
            type="button"
            onClick={onSubmitOpportunity}
            className="mt-5 inline-flex items-center gap-1.5 rounded-lg bg-teal px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-teal-deep transition"
          >
            <span>+ Submit Opportunity</span>
          </button>
        </div>
      )}

      {/* 5. Filter Result Empty State (When opportunities exist in DB, but filter yields 0) */}
      {eventsState.status === "success" &&
        allOpportunities.length > 0 &&
        filteredOpportunities.length === 0 && (
          <div className="rounded-2xl border border-line bg-card p-8 text-center shadow-xs">
            <p className="text-sm font-semibold text-ink">No opportunities match your filter criteria.</p>
            <p className="mt-1 text-xs text-ink-soft">Try switching tabs or resetting your active search keywords.</p>
            <button
              onClick={() => {
                onCategoryChange("all");
                setFilterMode("all");
                setFilterEvidence("all");
              }}
              className="mt-3 text-xs font-semibold text-teal hover:underline"
            >
              Show all opportunities
            </button>
          </div>
        )}

      {/* 6. Success List — Clean LinkedIn-style Opportunity Cards */}
      {eventsState.status === "success" && filteredOpportunities.length > 0 && (
        <div className="flex flex-col gap-3">
          {/* Subtle item count badge required by test suites */}
          <div className="text-[11px] font-semibold text-ink-soft px-1">
            {allOpportunities.length} {allOpportunities.length === 1 ? "event stored" : "events stored"}
          </div>

          {filteredOpportunities.map((op: Opportunity) => {
            const isSaved = savedOpportunityIds.has(op.id);
            const sourceCount = op.sources?.length ?? 1;
            const evidenceCount = op.evidence?.length ?? 0;
            const deadlineFormatted =
              formatDeadline(op.registration_deadline) ||
              formatDeadline(op.submission_deadline) ||
              formatDeadline(op.end_date);

            const displayTitle = op.title || op.event_name || "Untitled event";
            const displayOrganizer = op.organizer || "Organizer not stated";

            // Derive badge styling
            const isVerified = evidenceCount >= 2;
            const isCampusEvent =
              op.opportunity_type?.includes("event") || op.opportunity_type?.includes("campus");

            // Extract tags
            const tags: string[] = [];
            if (op.opportunity_type) tags.push(op.opportunity_type.replace("_", " "));
            if (op.mode) tags.push(op.mode.replace("_", " "));
            if (op.skills_required) {
              const skillList = op.skills_required.split(",").map((s: string) => s.trim());
              tags.push(...skillList.slice(0, 2));
            }
            if (tags.length === 0) tags.push("Opportunity");

            return (
              <article
                key={op.id}
                className="group relative rounded-2xl border border-line bg-card p-4 sm:p-5 shadow-xs transition hover:border-teal/50 hover:shadow-sm"
              >
                {/* Top Row: Verification Badge, Relative Time & Three-dots */}
                <div className="flex items-center justify-between gap-2 pb-3">
                  <div className="flex items-center gap-2">
                    {isVerified ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-success-wash px-2.5 py-0.5 text-[11px] font-semibold text-success">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Verified Source</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-teal-wash px-2.5 py-0.5 text-[11px] font-semibold text-teal">
                        <span className="h-1.5 w-1.5 rounded-full bg-teal" /> Source-backed
                      </span>
                    )}

                    {isCampusEvent && (
                      <span className="inline-flex items-center rounded-full bg-purple-50 px-2.5 py-0.5 text-[11px] font-semibold text-purple-700">
                        Campus Event
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-ink-muted">
                    <span>{getRelativeTime(op.created_at)}</span>
                    <button
                      type="button"
                      className="rounded-full p-1 text-ink-muted hover:bg-page hover:text-ink transition"
                      aria-label="Options"
                    >
                      ···
                    </button>
                  </div>
                </div>

                {/* Main Content Layout: Left Thumbnail + Right Information */}
                <div className="flex flex-col sm:flex-row gap-4 items-start">
                  {/* Left Thumbnail Illustration / Badge */}
                  <div className="flex h-24 w-24 sm:h-28 sm:w-28 shrink-0 items-center justify-center rounded-xl border border-line bg-page overflow-hidden">
                    <div className="flex flex-col items-center justify-center p-2 text-center">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-wash text-teal font-bold text-base mb-1">
                        {displayTitle.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-[10px] font-bold text-ink-soft uppercase tracking-wider line-clamp-1">
                        {op.opportunity_type || "Event"}
                      </span>
                    </div>
                  </div>

                  {/* Right Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-display text-base sm:text-lg font-bold text-ink group-hover:text-teal transition leading-snug">
                      {displayTitle}
                    </h3>
                    <p className="mt-0.5 text-xs font-semibold text-ink-soft">{displayOrganizer}</p>

                    {/* Category Tags */}
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="rounded-full bg-[#F0F2FE] px-2.5 py-0.5 text-[10px] font-semibold text-[#4834D4] capitalize"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>

                    {/* Meta info row */}
                    <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-ink-soft">
                      {deadlineFormatted && (
                        <div className="flex items-center gap-1 font-medium text-ink">
                          <svg className="h-3.5 w-3.5 text-teal shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span>Applications close {deadlineFormatted}</span>
                        </div>
                      )}
                      {op.location && (
                        <div className="flex items-center gap-1">
                          <svg className="h-3.5 w-3.5 text-ink-soft shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <span>{op.location}</span>
                        </div>
                      )}
                      {op.mode && (
                        <div className="flex items-center gap-1 capitalize">
                          <svg className="h-3.5 w-3.5 text-ink-soft shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                          </svg>
                          <span>{op.mode.replace("_", " ")}</span>
                        </div>
                      )}
                    </div>

                    {/* Eligibility or description excerpt */}
                    {(op.eligibility || op.skills_required) && (
                      <p className="mt-2 text-xs text-ink-soft/90 line-clamp-2 leading-relaxed">
                        {op.eligibility || `Skills: ${op.skills_required}`}
                      </p>
                    )}
                  </div>
                </div>

                {/* Footer Row: Evidence Breakdown on Left & Actions on Right */}
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                        evidenceCount >= 3
                          ? "bg-success-wash text-success"
                          : evidenceCount >= 1
                          ? "bg-teal-wash text-teal"
                          : "bg-page text-ink-soft"
                      }`}
                    >
                      <svg className="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Evidence: {evidenceCount >= 3 ? "Strong" : evidenceCount >= 1 ? "Good" : "Not Yet Assessed"}</span>
                      <svg className="h-3 w-3 opacity-75 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </span>

                    <span className="text-[11px] text-ink-muted">
                      {sourceCount} {sourceCount === 1 ? "source" : "sources"}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => onToggleSave(op.id)}
                      className={`inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${
                        isSaved
                          ? "border-teal bg-teal-wash text-teal"
                          : "border-line bg-card text-ink hover:bg-page"
                      }`}
                    >
                      <svg className={`h-3.5 w-3.5 ${isSaved ? "fill-teal text-teal" : "text-ink-soft"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                      </svg>
                      <span>{isSaved ? "Saved" : "Save"}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => onSelectOpportunity(op)}
                      className="inline-flex items-center gap-1 rounded-lg bg-ink px-3.5 py-1.5 text-xs font-semibold text-white shadow-xs transition hover:bg-teal focus:outline-hidden"
                    >
                      <span>View Details</span>
                      <span>→</span>
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
