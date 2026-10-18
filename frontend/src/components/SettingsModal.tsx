import { useState, useEffect } from "react";
import type { UserProfile } from "../types/auth";
import { UserAvatar } from "./Avatar";
import { fetchDemoStatus, resetDemoEnvironment, seedDemoEnvironment } from "../services/authService";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserProfile | null;
  onOpenProfile: () => void;
  onLogout: () => void;
  onOpenAuth: () => void;
  onRefreshData?: () => void;
}

type SettingsTab = "account" | "display" | "privacy" | "demo";

export interface UserPreferences {
  defaultFeedCategory: string;
  cardDensity: "comfortable" | "compact";
  showConfidenceBadges: boolean;
  allowDiscovery: boolean;
  notifyReminders: boolean;
}

const PREFERENCES_KEY = "eventsignal_user_preferences";

export function loadUserPreferences(): UserPreferences {
  try {
    const raw = localStorage.getItem(PREFERENCES_KEY);
    if (raw) {
      return {
        defaultFeedCategory: "all",
        cardDensity: "comfortable",
        showConfidenceBadges: true,
        allowDiscovery: true,
        notifyReminders: true,
        ...JSON.parse(raw),
      };
    }
  } catch {
    // fallback
  }
  return {
    defaultFeedCategory: "all",
    cardDensity: "comfortable",
    showConfidenceBadges: true,
    allowDiscovery: true,
    notifyReminders: true,
  };
}

export function saveUserPreferences(prefs: UserPreferences): void {
  try {
    localStorage.setItem(PREFERENCES_KEY, JSON.stringify(prefs));
  } catch {
    // ignore
  }
}

export function SettingsModal({
  isOpen,
  onClose,
  currentUser,
  onOpenProfile,
  onLogout,
  onOpenAuth,
  onRefreshData,
}: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>("account");
  const [preferences, setPreferences] = useState<UserPreferences>(loadUserPreferences);
  const [saveFeedback, setSaveFeedback] = useState<string | null>(null);

  // Demo status and operations
  const [isDemoActive, setIsDemoActive] = useState<boolean>(false);
  const [isResettingDemo, setIsResettingDemo] = useState(false);
  const [demoFeedback, setDemoFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    if (isOpen) {
      setPreferences(loadUserPreferences());
      setSaveFeedback(null);
      setDemoFeedback(null);
      fetchDemoStatus().then((status) => {
        setIsDemoActive(Boolean(status?.demo_mode_enabled || currentUser?.is_demo));
      }).catch(() => {
        setIsDemoActive(Boolean(currentUser?.is_demo));
      });
    }
  }, [isOpen, currentUser]);

  if (!isOpen) return null;

  const handlePreferenceChange = <K extends keyof UserPreferences>(key: K, value: UserPreferences[K]) => {
    const updated = { ...preferences, [key]: value };
    setPreferences(updated);
    saveUserPreferences(updated);
    setSaveFeedback("Preference updated successfully.");
    setTimeout(() => setSaveFeedback(null), 2500);
  };

  const handleResetDemo = async () => {
    if (!window.confirm("Are you sure you want to reset demo data? All temporary demo mutations will be restored to the synthetic baseline.")) {
      return;
    }
    setIsResettingDemo(true);
    setDemoFeedback(null);
    try {
      const res = await resetDemoEnvironment();
      setDemoFeedback({
        type: "success",
        message: res.message || "Demo workspace successfully reset to synthetic baseline.",
      });
      onRefreshData?.();
    } catch (err) {
      setDemoFeedback({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to reset demo workspace.",
      });
    } finally {
      setIsResettingDemo(false);
    }
  };

  const handleSeedDemo = async () => {
    setIsResettingDemo(true);
    setDemoFeedback(null);
    try {
      const res = await seedDemoEnvironment();
      setDemoFeedback({
        type: "success",
        message: res.message || "Synthetic demo dataset verified and ready.",
      });
      onRefreshData?.();
    } catch (err) {
      setDemoFeedback({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to seed demo dataset.",
      });
    } finally {
      setIsResettingDemo(false);
    }
  };

  const primaryMembership = currentUser?.memberships?.[0];
  const institutionName = primaryMembership?.institution_name || "Campus Community";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-dialog-title"
    >
      <div
        className="w-full max-w-2xl overflow-hidden rounded-2xl border border-line bg-card shadow-xl transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-wash text-teal">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h2 id="settings-dialog-title" className="text-lg font-bold text-ink">
                Settings & Preferences
              </h2>
              <p className="text-xs text-ink-soft">
                Manage your account, workspace identity, view preferences, and privacy controls.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-ink-soft hover:bg-page hover:text-ink transition"
            aria-label="Close Settings Dialog"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-line bg-page px-6 gap-2 text-xs font-medium">
          <button
            onClick={() => setActiveTab("account")}
            className={`border-b-2 px-3 py-2.5 transition ${
              activeTab === "account"
                ? "border-teal text-teal font-semibold"
                : "border-transparent text-ink-soft hover:text-ink"
            }`}
          >
            Account & Identity
          </button>
          <button
            onClick={() => setActiveTab("display")}
            className={`border-b-2 px-3 py-2.5 transition ${
              activeTab === "display"
                ? "border-teal text-teal font-semibold"
                : "border-transparent text-ink-soft hover:text-ink"
            }`}
          >
            Display & Feed
          </button>
          <button
            onClick={() => setActiveTab("privacy")}
            className={`border-b-2 px-3 py-2.5 transition ${
              activeTab === "privacy"
                ? "border-teal text-teal font-semibold"
                : "border-transparent text-ink-soft hover:text-ink"
            }`}
          >
            Privacy & Alerts
          </button>
          <button
            onClick={() => setActiveTab("demo")}
            className={`border-b-2 px-3 py-2.5 transition ${
              activeTab === "demo"
                ? "border-teal text-teal font-semibold"
                : "border-transparent text-ink-soft hover:text-ink"
            }`}
          >
            Demo & Environment
          </button>
        </div>

        {/* Feedback Alert */}
        {saveFeedback && (
          <div className="bg-teal-wash px-6 py-2 text-xs font-medium text-teal border-b border-teal/20 flex items-center gap-2">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{saveFeedback}</span>
          </div>
        )}

        {/* Tab Content Body */}
        <div className="max-h-[60vh] overflow-y-auto p-6 space-y-6">
          {/* TAB 1: ACCOUNT & IDENTITY */}
          {activeTab === "account" && (
            <div className="space-y-6">
              {currentUser ? (
                <>
                  <div className="flex items-center gap-4 rounded-xl border border-line bg-page p-4">
                    <UserAvatar
                      name={currentUser.user.full_name}
                      role={currentUser.is_demo ? "Presenter" : (primaryMembership?.role || "Member")}
                      size="lg"
                      showBadge={true}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-ink truncate">{currentUser.user.full_name}</h3>
                        {currentUser.is_demo && (
                          <span className="rounded bg-teal-wash px-2 py-0.5 text-[10px] font-semibold text-teal border border-teal/20">
                            Demo Mode
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-ink-soft truncate">{currentUser.user.email}</p>
                      <p className="mt-1 text-xs font-medium text-teal truncate">
                        {institutionName} · <span className="capitalize">{primaryMembership?.role || "Member"}</span>
                      </p>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-line p-4">
                      <h4 className="text-xs font-semibold text-ink">Campus Profile</h4>
                      <p className="mt-1 text-xs text-ink-soft">
                        Update your academic headline, bio, skills, domains, and career interests.
                      </p>
                      <button
                        onClick={() => {
                          onClose();
                          onOpenProfile();
                        }}
                        className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-teal px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-deep transition shadow-xs"
                      >
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        Edit Full Profile
                      </button>
                    </div>

                    <div className="rounded-xl border border-line p-4">
                      <h4 className="text-xs font-semibold text-ink">Session Management</h4>
                      <p className="mt-1 text-xs text-ink-soft">
                        End your authenticated session or switch to another campus profile.
                      </p>
                      <button
                        onClick={() => {
                          onLogout();
                          onClose();
                        }}
                        className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-alert/30 bg-alert/5 px-3 py-1.5 text-xs font-semibold text-alert hover:bg-alert/10 transition"
                      >
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        Sign Out
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="rounded-xl border border-line bg-page p-6 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-teal-wash text-teal mb-3">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <h3 className="text-sm font-bold text-ink">Guest Visitor</h3>
                  <p className="mt-1 text-xs text-ink-soft max-w-sm mx-auto">
                    You are currently using EventSignal in unauthenticated guest mode. Sign in to access your campus profile, manage institutional workspaces, or request mentorship.
                  </p>
                  <button
                    onClick={() => {
                      onClose();
                      onOpenAuth();
                    }}
                    className="mt-4 rounded-lg bg-teal px-4 py-2 text-xs font-semibold text-white hover:bg-teal-deep transition shadow-xs"
                  >
                    Sign In or Register
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: DISPLAY & FEED */}
          {activeTab === "display" && (
            <div className="space-y-5">
              <div className="rounded-xl border border-line p-4 space-y-4">
                <div>
                  <label htmlFor="settings-default-feed-select" className="block text-xs font-bold text-ink">
                    Default Feed Category
                  </label>
                  <p className="text-[11px] text-ink-soft">
                    Choose which category of opportunities to focus on upon landing on the home feed.
                  </p>
                  <select
                    id="settings-default-feed-select"
                    value={preferences.defaultFeedCategory}
                    onChange={(e) => handlePreferenceChange("defaultFeedCategory", e.target.value)}
                    className="mt-2 w-full rounded-lg border border-line bg-card px-3 py-2 text-xs text-ink focus:border-teal focus:outline-hidden"
                  >
                    <option value="all">For You (All Items)</option>
                    <option value="campus_event">Campus Events</option>
                    <option value="hackathon">Hackathons</option>
                    <option value="internship">Internships</option>
                    <option value="research">Research</option>
                    <option value="workshop">Workshops</option>
                    <option value="opportunity">Other Opportunities</option>
                  </select>
                </div>

                <div className="border-t border-line pt-4">
                  <label className="block text-xs font-bold text-ink">Feed Card Density</label>
                  <p className="text-[11px] text-ink-soft">
                    Adjust the spacing and depth of opportunity cards in your feed.
                  </p>
                  <div className="mt-2 flex gap-3">
                    <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
                      <input
                        type="radio"
                        name="cardDensity"
                        value="comfortable"
                        checked={preferences.cardDensity === "comfortable"}
                        onChange={() => handlePreferenceChange("cardDensity", "comfortable")}
                        className="text-teal focus:ring-teal"
                      />
                      <span>Comfortable (Standard spacing with full evidence preview)</span>
                    </label>
                    <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
                      <input
                        type="radio"
                        name="cardDensity"
                        value="compact"
                        checked={preferences.cardDensity === "compact"}
                        onChange={() => handlePreferenceChange("cardDensity", "compact")}
                        className="text-teal focus:ring-teal"
                      />
                      <span>Compact (Denser view for quick scanning)</span>
                    </label>
                  </div>
                </div>

                <div className="border-t border-line pt-4 flex items-center justify-between">
                  <div>
                    <span className="block text-xs font-bold text-ink">Evidence Confidence Badges</span>
                    <span className="text-[11px] text-ink-soft">
                      Highlight High/Medium confidence signals on evidence claims.
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.showConfidenceBadges}
                    onChange={(e) => handlePreferenceChange("showConfidenceBadges", e.target.checked)}
                    className="h-4 w-4 rounded border-line text-teal focus:ring-teal"
                    aria-label="Toggle evidence confidence badges"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: PRIVACY & ALERTS */}
          {activeTab === "privacy" && (
            <div className="space-y-5">
              <div className="rounded-xl border border-line p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="block text-xs font-bold text-ink">Campus Member Discovery</span>
                    <span className="text-[11px] text-ink-soft">
                      Allow peers, alumni, and verified faculty in your college workspace to discover your profile.
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.allowDiscovery}
                    onChange={(e) => handlePreferenceChange("allowDiscovery", e.target.checked)}
                    className="h-4 w-4 rounded border-line text-teal focus:ring-teal"
                    aria-label="Toggle campus member discovery"
                  />
                </div>

                <div className="border-t border-line pt-4 flex items-center justify-between">
                  <div>
                    <span className="block text-xs font-bold text-ink">Event & Task Reminders</span>
                    <span className="text-[11px] text-ink-soft">
                      Receive notifications for registered events and pending legacy handover commitments.
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.notifyReminders}
                    onChange={(e) => handlePreferenceChange("notifyReminders", e.target.checked)}
                    className="h-4 w-4 rounded border-line text-teal focus:ring-teal"
                    aria-label="Toggle event and task reminders"
                  />
                </div>

                <div className="border-t border-line pt-4 text-[11px] text-ink-soft bg-page p-3 rounded-lg">
                  <div className="flex items-start gap-2">
                    <svg className="h-4 w-4 text-teal shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    <div>
                      <strong className="text-ink">Zero Surveillance Guarantee:</strong> EventSignal never sells or shares student data, private resumes, or unverified contact info with commercial advertisers.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: DEMO & SYSTEM ENVIRONMENT */}
          {activeTab === "demo" && (
            <div className="space-y-5">
              {demoFeedback && (
                <div
                  className={`rounded-lg p-3 text-xs font-medium ${
                    demoFeedback.type === "success"
                      ? "bg-teal-wash text-teal border border-teal/20"
                      : "bg-alert/10 text-alert border border-alert/20"
                  }`}
                >
                  {demoFeedback.message}
                </div>
              )}

              <div className="rounded-xl border border-line p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-ink">Demo Mode Status</h4>
                    <p className="text-[11px] text-ink-soft">
                      Isolated evaluation environment with synthetic college community dataset.
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                      isDemoActive
                        ? "bg-teal-wash text-teal border border-teal/20"
                        : "bg-page text-ink-soft border border-line"
                    }`}
                  >
                    {isDemoActive ? "Active" : "Standard Mode"}
                  </span>
                </div>

                <div className="rounded-lg bg-page p-3 text-[11px] text-ink-soft space-y-1">
                  <div><strong>College:</strong> Apex Institute of Technology (Demo Workspace)</div>
                  <div><strong>Synthetic Community:</strong> 30 Students, 12 Mentors, 10 Leadership Positions</div>
                  <div><strong>Isolation:</strong> In-memory / isolated dataset, non-destructive demo testing</div>
                </div>

                <div className="border-t border-line pt-4 flex flex-wrap gap-2.5">
                  <button
                    onClick={handleResetDemo}
                    disabled={isResettingDemo}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-teal bg-teal/5 px-3 py-1.5 text-xs font-semibold text-teal hover:bg-teal/15 transition disabled:opacity-50"
                  >
                    {isResettingDemo ? "Resetting..." : "Reset Demo Environment"}
                  </button>
                  <button
                    onClick={handleSeedDemo}
                    disabled={isResettingDemo}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-card px-3 py-1.5 text-xs font-medium text-ink hover:bg-page transition disabled:opacity-50"
                  >
                    Re-verify Demo Data
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end border-t border-line bg-page px-6 py-3.5">
          <button
            onClick={onClose}
            className="rounded-lg bg-teal px-4 py-1.5 text-xs font-semibold text-white hover:bg-teal-deep transition shadow-xs"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
