import type { UserProfile } from "../types/auth";
import type { StudentProfile } from "../types/profile";
import type { AppView } from "./AppNavbar";
import { UserAvatar } from "./Avatar";

interface ProfileSidebarProps {
  currentUser: UserProfile | null;
  studentProfile: StudentProfile | null;
  totalOpportunitiesCount: number;
  myOffersCount: number;
  pendingTasksCount: number;
  currentView: AppView;
  onViewChange: (view: AppView) => void;
  onOpenProfile: () => void;
  onOpenAuth: () => void;
  onOpenSettings?: () => void;
  onSelectCategoryFilter?: (category: string) => void;
  connectionsCount?: number;
}

export function ProfileSidebar({
  currentUser,
  studentProfile,
  totalOpportunitiesCount,
  myOffersCount,
  pendingTasksCount,
  connectionsCount,
  currentView,
  onViewChange,
  onOpenProfile,
  onOpenAuth,
  onOpenSettings,
  onSelectCategoryFilter,
}: ProfileSidebarProps) {
  // Calculate completion percentage from real profile data
  const calculateProfileCompletion = (): number => {
    if (!currentUser) return 0;
    if (!studentProfile) return 30; // base for authenticated user with verified account
    let score = 30;
    if (studentProfile.headline) score += 15;
    if (studentProfile.degree_level) score += 15;
    if (studentProfile.bio) score += 10;
    if (studentProfile.skills && studentProfile.skills.length > 0) score += 10;
    if (studentProfile.interests && studentProfile.interests.length > 0) score += 10;
    if (studentProfile.linkedin_url || studentProfile.github_url || studentProfile.portfolio_url) score += 10;
    return Math.min(100, score);
  };

  const completionPct = calculateProfileCompletion();
  const primaryMembership = currentUser?.memberships?.[0];
  const institutionName = primaryMembership?.institution_name || "Campus Workspace";


  // Degree or Headline
  const roleHeadline =
    studentProfile?.headline ||
    (studentProfile?.degree_level
      ? `${studentProfile.degree_level} ${
          studentProfile.graduation_year ? `(Class of ${studentProfile.graduation_year})` : ""
        }`
      : primaryMembership?.role
      ? `${primaryMembership.role.replace("_", " ")}`
      : "Community Member");

  return (
    <aside className="w-full flex-col gap-3 lg:w-60 xl:w-64 shrink-0 flex" aria-label="Campus Sidebar">
      {/* 1. Profile Summary Card */}
      <div className="overflow-hidden rounded-xl border border-line bg-card shadow-xs">
        {/* Campus Cover Banner */}
        <div className="relative h-20 w-full bg-gradient-to-r from-teal-deep via-teal to-[#1B4B66]">
          {/* Subtle stylized campus architecture pattern overlay */}
          <svg className="absolute inset-0 h-full w-full opacity-15" viewBox="0 0 400 120" preserveAspectRatio="none" fill="currentColor">
            <path d="M0,120 L40,80 L80,120 L120,60 L160,120 L200,70 L240,120 L280,50 L320,120 L360,75 L400,120 Z" />
            <rect x="180" y="30" width="40" height="90" rx="4" />
            <circle cx="200" cy="20" r="12" />
          </svg>
        </div>

        {/* Profile Details Container */}
        <div className="relative px-3.5 pb-4 pt-0">
          {/* Overlapping Avatar */}
          <div className="-mt-9 mb-2 flex items-center justify-between">
            <UserAvatar
              name={currentUser?.user.full_name || "Guest"}
              role={currentUser?.is_demo ? "Presenter" : (primaryMembership?.role || "Member")}
              size="xl"
              showBadge={true}
              className="border-card shadow-xs"
            />
            {currentUser && (
              <button
                type="button"
                onClick={onOpenProfile}
                title="Edit Profile"
                className="rounded-full p-1 text-ink-soft hover:bg-page hover:text-teal transition"
                aria-label="Edit Profile"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
            )}
          </div>

          {currentUser ? (
            <>
              {/* Name & Title */}
              <div className="flex items-center gap-1.5">
                <h2 className="text-sm font-bold text-ink truncate leading-tight">
                  {currentUser.user.full_name}
                </h2>
                <button
                  type="button"
                  onClick={onOpenProfile}
                  className="text-ink-soft hover:text-teal transition text-xs p-0.5"
                  aria-label="Quick edit"
                >
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
              </div>
              <p className="mt-0.5 text-[11px] text-ink-soft line-clamp-1">{roleHeadline}</p>
              <p className="text-[11px] font-medium text-teal truncate mt-0.5">{institutionName}</p>

              {/* Profile Completion Bar */}
              <div className="mt-3">
                <div className="flex items-center justify-between text-[10px] text-ink-soft font-medium">
                  <span>Profile {completionPct}% complete</span>
                </div>
                <div className="mt-1 h-1.5 w-full rounded-full bg-page overflow-hidden">
                  <div
                    className="h-full rounded-full bg-teal transition-all duration-500"
                    style={{ width: `${completionPct}%` }}
                  />
                </div>
              </div>

              {/* 3-Column Stats Row */}
              <div className="mt-3.5 grid grid-cols-3 divide-x divide-line border-t border-line pt-2.5 text-center">
                <div className="px-1">
                  <div className="text-xs font-bold text-ink">
                    {connectionsCount ?? (currentUser.is_demo ? 12 : 0)}
                  </div>
                  <div className="text-[9px] text-ink-soft">Connections</div>
                </div>
                <div className="px-1">
                  <div className="text-xs font-bold text-teal">{myOffersCount}</div>
                  <div className="text-[9px] text-ink-soft">Help Offers</div>
                </div>
                <div className="px-1">
                  <div className="text-xs font-bold text-ink">{totalOpportunitiesCount}</div>
                  <div className="text-[9px] text-ink-soft">Opportunities</div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-left pt-1">
              <h2 className="text-sm font-bold text-ink">Guest Visitor</h2>
              <p className="mt-1 text-xs text-ink-soft leading-relaxed">
                Connect with verified college mentors and source-backed opportunities.
              </p>
              <button
                onClick={onOpenAuth}
                className="mt-3 w-full rounded-lg bg-teal py-1.5 text-xs font-semibold text-white transition hover:bg-teal-deep shadow-xs"
              >
                Sign In to College
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 2. Main Campus Navigation List */}
      <div className="rounded-xl border border-line bg-card p-2 shadow-xs">
        <nav className="flex flex-col gap-0.5 text-xs font-medium" aria-label="Sidebar Navigation">
          <button
            onClick={() => onViewChange("home")}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-left transition ${
              currentView === "home"
                ? "bg-teal-wash text-teal font-semibold border-l-3 border-teal"
                : "text-ink-soft hover:bg-page hover:text-ink"
            }`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            <span>Home</span>
          </button>

          <button
            onClick={currentUser ? onOpenProfile : onOpenAuth}
            className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-left text-ink-soft hover:bg-page hover:text-ink transition"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span>My Profile</span>
          </button>

          <button
            onClick={() => onViewChange("opportunities")}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-left transition ${
              currentView === "opportunities"
                ? "bg-teal-wash text-teal font-semibold border-l-3 border-teal"
                : "text-ink-soft hover:bg-page hover:text-ink"
            }`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span>My Opportunities</span>
          </button>

          <button
            onClick={() => onViewChange("offers")}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-left transition ${
              currentView === "offers"
                ? "bg-teal-wash text-teal font-semibold border-l-3 border-teal"
                : "text-ink-soft hover:bg-page hover:text-ink"
            }`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>My Help Offers</span>
          </button>

          <button
            onClick={() => onViewChange("network")}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-left transition ${
              currentView === "network"
                ? "bg-teal-wash text-teal font-semibold border-l-3 border-teal"
                : "text-ink-soft hover:bg-page hover:text-ink"
            }`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <span>My Connections</span>
          </button>

          <button
            onClick={() => onViewChange("institutions")}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-left transition ${
              currentView === "institutions"
                ? "bg-teal-wash text-teal font-semibold border-l-3 border-teal"
                : "text-ink-soft hover:bg-page hover:text-ink"
            }`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span>My Workspaces</span>
          </button>

          <button
            onClick={() => onViewChange("legacy")}
            className={`flex items-center justify-between rounded-lg px-3 py-2 text-left transition ${
              currentView === "legacy"
                ? "bg-teal-wash text-teal font-semibold border-l-3 border-teal"
                : "text-ink-soft hover:bg-page hover:text-ink"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <span>My Legacy Tasks</span>
            </div>
            {pendingTasksCount > 0 && (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-alert text-[9px] font-bold text-white">
                {pendingTasksCount}
              </span>
            )}
          </button>

          <button
            onClick={() => onViewChange("partnerships")}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-left transition ${
              currentView === "partnerships"
                ? "bg-teal-wash text-teal font-semibold border-l-3 border-teal"
                : "text-ink-soft hover:bg-page hover:text-ink"
            }`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <span>Partnerships & Pilots</span>
          </button>
        </nav>

        {/* 3. My Institution Section */}
        <div className="mt-3 border-t border-line pt-2.5">
          <div className="px-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-ink-muted">
            My Institution
          </div>
          <div className="flex items-center gap-2 px-3 py-1 text-xs font-semibold text-ink truncate">
            <svg className="h-4 w-4 text-teal shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
            </svg>
            <span className="truncate">{institutionName}</span>
          </div>

          <div className="mt-1 flex flex-col gap-0.5 text-[11px] text-ink-soft">
            <button
              onClick={() => {
                onSelectCategoryFilter?.("campus_event");
                onViewChange("home");
              }}
              className="flex items-center gap-2 rounded-md px-3 py-1 text-left hover:bg-page hover:text-teal transition"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>Campus Events</span>
            </button>
            <button
              onClick={() => onViewChange("institutions")}
              className="flex items-center gap-2 rounded-md px-3 py-1 text-left hover:bg-page hover:text-teal transition"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
              </svg>
              <span>Announcements</span>
            </button>
            <button
              onClick={() => onViewChange("institutions")}
              className="flex items-center gap-2 rounded-md px-3 py-1 text-left hover:bg-page hover:text-teal transition"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
              <span>Official Positions</span>
            </button>
            <button
              onClick={() => onViewChange("legacy")}
              className="flex items-center gap-2 rounded-md px-3 py-1 text-left hover:bg-page hover:text-teal transition"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Handover Records</span>
            </button>
          </div>
        </div>

        {/* 4. Other Section */}
        <div className="mt-3 border-t border-line pt-2">
          <div className="px-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-ink-muted">
            Other
          </div>
          <div className="flex flex-col gap-0.5 text-[11px] text-ink-soft">
            <button
              onClick={onOpenSettings}
              className="flex items-center gap-2 rounded-md px-3 py-1 text-left hover:bg-page hover:text-ink transition"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Settings</span>
            </button>
            <button
              onClick={onOpenAuth}
              className="flex items-center gap-2 rounded-md px-3 py-1 text-left text-ink-soft hover:bg-page hover:text-alert transition"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span>{currentUser ? "Sign Out" : "Sign In"}</span>
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
