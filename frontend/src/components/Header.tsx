import { useState, useRef, useEffect, useMemo } from "react";
import type { ResourceState } from "../hooks/useRemoteResource";
import type { HealthResponse } from "../types/health";
import type { UserProfile } from "../types/auth";
import type { Opportunity } from "../types/opportunity";
import { ConnectionStatus, SIGNAL_RULE_STYLES, describeConnection } from "./ConnectionStatus";
import { UserAvatar } from "./Avatar";

export type AppView =
  | "home"
  | "opportunities"
  | "institutions"
  | "network"
  | "offers"
  | "legacy"
  | "partnerships";

export interface HeaderProps {
  health: ResourceState<HealthResponse>;
  currentView?: AppView;
  onViewChange?: (view: AppView) => void;
  currentUser?: UserProfile | null;
  onOpenAuth?: () => void;
  onOpenProfile?: () => void;
  onOpenSettings?: () => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  onSearchSubmit?: (query: string) => void;
  opportunities?: Opportunity[];
  onSelectOpportunity?: (op: Opportunity) => void;
  notificationsCount?: number;
}

export function Header({
  health,
  currentView = "home",
  onViewChange,
  currentUser = null,
  onOpenAuth,
  onOpenProfile,
  onOpenSettings,
  searchQuery = "",
  onSearchChange,
  onSearchSubmit,
  opportunities = [],
  onSelectOpportunity,
  notificationsCount,
}: HeaderProps) {
  const { tone } = describeConnection(health);
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Close search popover on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setIsSearchFocused(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const trimmedQuery = searchQuery.trim().toLowerCase();

  const matchingOpportunities = useMemo(() => {
    if (!trimmedQuery) return [];
    return opportunities
      .filter((op) => {
        const title = (op.title || op.event_name || "").toLowerCase();
        const org = (op.organizer || "").toLowerCase();
        const loc = (op.location || "").toLowerCase();
        const skills = (op.skills_required || "").toLowerCase();
        const type = (op.opportunity_type || "").toLowerCase();
        return (
          title.includes(trimmedQuery) ||
          org.includes(trimmedQuery) ||
          loc.includes(trimmedQuery) ||
          skills.includes(trimmedQuery) ||
          type.includes(trimmedQuery)
        );
      })
      .slice(0, 4);
  }, [opportunities, trimmedQuery]);

  const appSections = useMemo(
    () => [
      {
        view: "home" as AppView,
        label: "Home Feed & Campus Events",
        keywords: ["home", "feed", "campus", "event", "all", "updates"],
      },
      {
        view: "opportunities" as AppView,
        label: "Evidence Before You Register",
        keywords: ["evidence", "register", "intake", "verify", "compare", "url"],
      },
      {
        view: "institutions" as AppView,
        label: "Institutional Workspaces & Identity",
        keywords: ["institution", "workspace", "college", "department", "unit", "position", "admin"],
      },
      {
        view: "network" as AppView,
        label: "Campus Network & Discovery",
        keywords: ["network", "people", "student", "alumni", "faculty", "mentor", "discover", "members"],
      },
      {
        view: "offers" as AppView,
        label: "Campus Mentorship & Help Offers",
        keywords: ["help", "offer", "mentor", "guidance", "mock", "review", "portfolio"],
      },
      {
        view: "legacy" as AppView,
        label: "Gap Matching & Legacy Handover",
        keywords: ["legacy", "gap", "need", "handover", "task", "followup", "commitment"],
      },
      {
        view: "partnerships" as AppView,
        label: "Partnerships & Promotion",
        keywords: ["partner", "partnership", "sponsor", "promotion", "pilot", "metrics", "brand"],
      },
    ],
    []
  );

  const matchingSections = useMemo(() => {
    if (!trimmedQuery) return [];
    return appSections
      .filter(
        (sec) =>
          sec.label.toLowerCase().includes(trimmedQuery) ||
          sec.keywords.some((kw) => kw.includes(trimmedQuery))
      )
      .slice(0, 3);
  }, [appSections, trimmedQuery]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearchFocused(false);
    if (onSearchSubmit) {
      onSearchSubmit(searchQuery);
    } else {
      onSearchChange?.(searchQuery);
      onViewChange?.("home");
    }
  };

  const primaryMembership = currentUser?.memberships?.[0];

  const navItems: { view: AppView; label: string; icon: (active: boolean) => React.ReactNode }[] = [
    {
      view: "home",
      label: "Home",
      icon: (active) => (
        <svg
          className={`h-5 w-5 ${active ? "text-teal" : "text-ink-soft"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={active ? 2.2 : 1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
          />
        </svg>
      ),
    },
    {
      view: "opportunities",
      label: "Opportunities",
      icon: (active) => (
        <svg
          className={`h-5 w-5 ${active ? "text-teal" : "text-ink-soft"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={active ? 2.2 : 1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
          />
        </svg>
      ),
    },
    {
      view: "institutions",
      label: "Workspaces",
      icon: (active) => (
        <svg
          className={`h-5 w-5 ${active ? "text-teal" : "text-ink-soft"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={active ? 2.2 : 1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
          />
        </svg>
      ),
    },
    {
      view: "network",
      label: "Network",
      icon: (active) => (
        <svg
          className={`h-5 w-5 ${active ? "text-teal" : "text-ink-soft"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={active ? 2.2 : 1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
      ),
    },
    {
      view: "offers",
      label: "Help Offers",
      icon: (active) => (
        <svg
          className={`h-5 w-5 ${active ? "text-teal" : "text-ink-soft"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={active ? 2.2 : 1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      ),
    },
    {
      view: "legacy",
      label: "Legacy",
      icon: (active) => (
        <svg
          className={`h-5 w-5 ${active ? "text-teal" : "text-ink-soft"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={active ? 2.2 : 1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z"
          />
        </svg>
      ),
    },
    {
      view: "partnerships",
      label: "Partnerships",
      icon: (active) => (
        <svg
          className={`h-5 w-5 ${active ? "text-teal" : "text-ink-soft"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={active ? 2.2 : 1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
          />
        </svg>
      ),
    },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-card shadow-xs">
      {/* Top signal status line */}
      <div aria-hidden="true" className={`h-[3px] w-full transition-colors ${SIGNAL_RULE_STYLES[tone]}`} />

      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6">
        {/* Left: Brand & Search */}
        <div className="flex flex-1 items-center gap-3 sm:gap-4">
          <button
            type="button"
            onClick={() => onViewChange?.("home")}
            className="flex items-center gap-2.5 transition hover:opacity-90 focus:outline-hidden"
            aria-label="EventSignal Home"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink text-teal-wash shadow-xs">
              <svg className="h-5 w-5 text-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.6}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 12h3l3-7 4 14 3-7h5" />
              </svg>
            </div>
            <span className="font-display text-lg font-bold tracking-tight text-ink hidden sm:inline-block">
              EventSignal
            </span>
          </button>

          {/* Search Field */}
          <div ref={searchContainerRef} className="relative max-w-xs flex-1 sm:max-w-sm lg:max-w-md">
            <form onSubmit={handleSearchSubmit} role="search" className="relative flex items-center">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <svg className="h-4 w-4 text-ink-soft" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="search"
                value={searchQuery}
                onFocus={() => setIsSearchFocused(true)}
                onChange={(e) => {
                  onSearchChange?.(e.target.value);
                  setIsSearchFocused(true);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Escape") {
                    setIsSearchFocused(false);
                  }
                }}
                placeholder="Search opportunities, people, events, colleges..."
                aria-label="Search opportunities, people, events, colleges"
                className="h-9 w-full rounded-lg border border-transparent bg-page pl-9 pr-8 text-xs text-ink placeholder:text-ink-soft/70 transition focus:border-line focus:bg-card focus:outline-hidden focus:ring-1 focus:ring-teal"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => {
                    onSearchChange?.("");
                    setIsSearchFocused(false);
                  }}
                  className="absolute right-2 text-ink-soft hover:text-ink p-1 rounded-full hover:bg-page transition"
                  aria-label="Clear search query"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </form>

            {/* Live Instant Search Dropdown Popover */}
            {isSearchFocused && trimmedQuery.length > 0 && (
              <div className="absolute left-0 right-0 top-10 z-50 overflow-hidden rounded-xl border border-line bg-card shadow-xl animate-in fade-in slide-in-from-top-1 duration-150">
                {/* 1. Opportunities & Events Matches */}
                {matchingOpportunities.length > 0 && (
                  <div className="p-2 border-b border-line">
                    <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-ink-soft">
                      Matching Opportunities ({matchingOpportunities.length})
                    </div>
                    <div className="flex flex-col gap-1 mt-0.5">
                      {matchingOpportunities.map((op) => (
                        <button
                          key={op.id}
                          type="button"
                          onClick={() => {
                            setIsSearchFocused(false);
                            if (onSelectOpportunity) {
                              onSelectOpportunity(op);
                            }
                            onViewChange?.("home");
                          }}
                          className="flex items-center justify-between gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs hover:bg-page transition"
                        >
                          <div className="min-w-0 flex-1">
                            <p className="font-semibold text-ink truncate">{op.title || op.event_name || "Opportunity"}</p>
                            <p className="text-[11px] text-ink-soft truncate">{op.organizer || "Campus Partner"}</p>
                          </div>
                          {op.opportunity_type && (
                            <span className="shrink-0 rounded bg-teal-wash px-1.5 py-0.5 text-[10px] font-medium text-teal capitalize">
                              {op.opportunity_type.replace("_", " ")}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* 2. Direct Area / Navigation Matches */}
                {matchingSections.length > 0 && (
                  <div className="p-2 border-b border-line bg-page/40">
                    <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-ink-soft">
                      Jump to Section
                    </div>
                    <div className="flex flex-col gap-1 mt-0.5">
                      {matchingSections.map((sec) => (
                        <button
                          key={sec.view}
                          type="button"
                          onClick={() => {
                            setIsSearchFocused(false);
                            onViewChange?.(sec.view);
                          }}
                          className="flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs hover:bg-card transition w-full"
                        >
                          <svg className="h-3.5 w-3.5 text-teal shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                          <span className="font-medium text-ink">{sec.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3. Empty State or Action to View in Feed */}
                <div className="p-2.5 bg-page text-center">
                  <button
                    type="button"
                    onClick={(e) => handleSearchSubmit(e)}
                    className="w-full rounded-lg bg-teal px-3 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-teal-deep transition flex items-center justify-center gap-1.5"
                  >
                    <span>Search all opportunities for "{searchQuery}"</span>
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Center / Right: Nav Item Links */}
        {onViewChange && (
          <nav className="hidden lg:flex items-center gap-1 xl:gap-2" aria-label="Main navigation">
            {navItems.map((item) => {
              const isActive = currentView === item.view;
              return (
                <button
                  key={item.view}
                  onClick={() => onViewChange(item.view)}
                  className={`relative flex h-14 flex-col items-center justify-center px-2.5 xl:px-3 text-[11px] font-medium transition ${
                    isActive ? "text-teal font-semibold" : "text-ink-soft hover:text-ink"
                  }`}
                >
                  <div className="flex items-center justify-center">{item.icon(isActive)}</div>
                  <span className="mt-0.5 whitespace-nowrap">{item.label}</span>
                  {isActive && (
                    <span className="absolute bottom-0 left-2 right-2 h-[2.5px] rounded-t-full bg-teal" />
                  )}
                </button>
              );
            })}
          </nav>
        )}

        {/* Right Section: Connection Status, Notifications & Profile Avatar */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Subtle Live Connection Status Component */}
          <div className="scale-90 sm:scale-100 origin-right">
            <ConnectionStatus state={health} />
          </div>

          {/* Notifications Bell */}
          <button
            type="button"
            className="relative flex h-8 w-8 items-center justify-center rounded-full text-ink-soft transition hover:bg-page hover:text-ink focus:outline-hidden"
            aria-label="Notifications"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
            {typeof notificationsCount === "number" && notificationsCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-alert text-[9px] font-bold text-white">
                {notificationsCount > 9 ? "9+" : notificationsCount}
              </span>
            )}
          </button>

          {/* User Account / Profile */}
          {currentUser ? (
            <div className="relative flex items-center gap-2">
              {currentUser.is_demo && (
                <span className="inline-flex items-center rounded-md border border-amber-300 bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-900 tracking-wider">
                  DEMO
                </span>
              )}
              <button
                type="button"
                onClick={() => setIsAccountMenuOpen(!isAccountMenuOpen)}
                className="flex items-center gap-1.5 rounded-full p-0.5 transition hover:ring-2 hover:ring-teal/20 focus:outline-hidden"
                aria-label="User account menu"
                aria-expanded={isAccountMenuOpen}
              >
                <UserAvatar
                  name={currentUser?.user.full_name || "User"}
                  role={currentUser?.is_demo ? "demo" : (primaryMembership?.role || "user")}
                  size="sm"
                />
                <svg className="h-3.5 w-3.5 text-ink-soft hidden sm:block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isAccountMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-xl border border-line bg-card py-1.5 shadow-lg z-50">
                  <div className="border-b border-line px-3.5 py-2">
                    <p className="text-xs font-bold text-ink truncate">{currentUser.user.full_name}</p>
                    <p className="text-[11px] text-ink-soft truncate">{currentUser.user.email}</p>
                    {primaryMembership?.institution_name && (
                      <span className="mt-1 inline-block rounded-md bg-teal-wash px-1.5 py-0.5 text-[10px] font-medium text-teal truncate max-w-full">
                        {primaryMembership.institution_name}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => {
                      setIsAccountMenuOpen(false);
                      onOpenProfile?.();
                    }}
                    className="flex w-full items-center gap-2 px-3.5 py-2 text-left text-xs font-medium text-ink hover:bg-page transition"
                  >
                    <svg className="h-4 w-4 text-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5" />
                    </svg>
                    <span>View & Edit Profile</span>
                  </button>
                  <button
                    onClick={() => {
                      setIsAccountMenuOpen(false);
                      onViewChange?.("institutions");
                    }}
                    className="flex w-full items-center gap-2 px-3.5 py-2 text-left text-xs font-medium text-ink hover:bg-page transition"
                  >
                    <svg className="h-4 w-4 text-ink-soft" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
                    </svg>
                    <span>College Workspaces</span>
                  </button>
                  {onOpenSettings && (
                    <button
                      onClick={() => {
                        setIsAccountMenuOpen(false);
                        onOpenSettings();
                      }}
                      className="flex w-full items-center gap-2 px-3.5 py-2 text-left text-xs font-medium text-ink hover:bg-page transition"
                    >
                      <svg className="h-4 w-4 text-ink-soft" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span>Settings & Preferences</span>
                    </button>
                  )}
                  <div className="border-t border-line my-1" />
                  <button
                    onClick={() => {
                      setIsAccountMenuOpen(false);
                      onOpenAuth?.();
                    }}
                    className="flex w-full items-center gap-2 px-3.5 py-2 text-left text-xs font-medium text-alert hover:bg-alert-wash transition"
                  >
                    <svg className="h-4 w-4 text-alert" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span>Sign Out / Switch User</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="inline-flex items-center gap-1.5 rounded-lg bg-teal px-3 py-1.5 text-xs font-semibold text-white shadow-xs transition hover:bg-teal-deep focus:outline-hidden"
            >
              Sign In
            </button>
          )}
        </div>
      </div>

      {/* Mobile Navigation Drawer / Horizontal scroll on small devices */}
      {onViewChange && (
        <div className="flex lg:hidden overflow-x-auto border-t border-line px-3 py-1.5 scrollbar-none gap-1 bg-page">
          {navItems.map((item) => {
            const isActive = currentView === item.view;
            return (
              <button
                key={item.view}
                onClick={() => onViewChange(item.view)}
                className={`flex shrink-0 items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition ${
                  isActive ? "bg-teal text-white font-semibold" : "text-ink-soft hover:bg-card"
                }`}
              >
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
}
