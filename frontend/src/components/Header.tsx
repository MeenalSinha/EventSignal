import { useState } from "react";
import type { ResourceState } from "../hooks/useRemoteResource";
import type { HealthResponse } from "../types/health";
import type { UserProfile } from "../types/auth";
import { ConnectionStatus, SIGNAL_RULE_STYLES, describeConnection } from "./ConnectionStatus";

export type AppView =
  | "home"
  | "opportunities"
  | "institutions"
  | "network"
  | "offers"
  | "legacy"
  | "partnerships";

interface HeaderProps {
  health: ResourceState<HealthResponse>;
  currentView?: AppView;
  onViewChange?: (view: AppView) => void;
  currentUser?: UserProfile | null;
  onOpenAuth?: () => void;
  onOpenProfile?: () => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
}

export function Header({
  health,
  currentView = "home",
  onViewChange,
  currentUser = null,
  onOpenAuth,
  onOpenProfile,
  searchQuery = "",
  onSearchChange,
}: HeaderProps) {
  const { tone } = describeConnection(health);
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);

  const userInitials = currentUser?.user.full_name
    ? currentUser.user.full_name
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "U";

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
          <div className="relative max-w-xs flex-1 sm:max-w-sm">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <svg className="h-4 w-4 text-ink-soft" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => onSearchChange?.(e.target.value)}
              placeholder="Search opportunities, people, events, colleges..."
              className="h-9 w-full rounded-lg border border-transparent bg-page pl-9 pr-3 text-xs text-ink placeholder:text-ink-soft/70 transition focus:border-line focus:bg-card focus:outline-hidden focus:ring-1 focus:ring-teal"
            />
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
            <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-alert text-[9px] font-bold text-white">
              3
            </span>
          </button>

          {/* User Account / Profile */}
          {currentUser ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setIsAccountMenuOpen(!isAccountMenuOpen)}
                className="flex items-center gap-1.5 rounded-full p-0.5 transition hover:ring-2 hover:ring-teal/20 focus:outline-hidden"
                aria-label="User account menu"
                aria-expanded={isAccountMenuOpen}
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full border border-teal/40 bg-teal-wash text-xs font-bold text-teal">
                  {userInitials}
                </div>
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
