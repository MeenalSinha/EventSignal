import { useEffect, useState } from "react";
import { AuthModal } from "./components/AuthModal";
import { EventWorkspace } from "./components/EventWorkspace";
import { Header, type AppView } from "./components/Header";
import { HelpOffersPanel } from "./components/HelpOffersPanel";
import { InstitutionWorkspacePanel } from "./components/InstitutionWorkspacePanel";
import { LegacyMatchingPanel } from "./components/LegacyMatchingPanel";
import { MemberDiscoveryPanel } from "./components/MemberDiscoveryPanel";
import { MyProfileModal } from "./components/MyProfileModal";
import { PartnershipsPromotionPanel } from "./components/PartnershipsPromotionPanel";
import { ServiceStatusPanel } from "./components/ServiceStatusPanel";
import { ProfileSidebar } from "./components/ProfileSidebar";
import { WelcomePanel } from "./components/WelcomePanel";
import { OpportunityFeed } from "./components/OpportunityFeed";
import { DiscoveryPanels } from "./components/DiscoveryPanels";
import {
  OpportunityDetailModal,
  QuickIntakeModal,
  ConnectModal,
  QuickNeedModal,
} from "./components/HomeModals";
import { useRemoteResource } from "./hooks/useRemoteResource";
import { fetchCurrentUser, logoutUser } from "./services/authService";
import { fetchEvents } from "./services/eventsService";
import { fetchHealth } from "./services/healthService";
import { fetchMyStudentProfile } from "./services/profileService";
import { fetchMyHelpOffers } from "./services/helpOfferService";
import { fetchMyFollowUpTasks } from "./services/legacyService";
import type { UserProfile } from "./types/auth";
import type { StudentProfile } from "./types/profile";
import type { Opportunity } from "./types/opportunity";
import type { HelpOffer } from "./types/helpOffer";

export default function App() {
  const health = useRemoteResource(fetchHealth);
  const events = useRemoteResource(fetchEvents);

  const [currentView, setCurrentView] = useState<AppView>("home");
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [studentProfile, setStudentProfile] = useState<StudentProfile | null>(null);
  const [myOffersCount, setMyOffersCount] = useState<number>(0);
  const [pendingTasksCount, setPendingTasksCount] = useState<number>(0);

  // Home view filters & state
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [savedOpportunityIds, setSavedOpportunityIds] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem("eventsignal_saved_ops");
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });

  // Modals state
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [submitModalTitle, setSubmitModalTitle] = useState("Submit Opportunity");
  const [isNeedModalOpen, setIsNeedModalOpen] = useState(false);
  const [selectedHelpOfferForConnect, setSelectedHelpOfferForConnect] = useState<HelpOffer | null>(null);

  // Restore user session on mount
  useEffect(() => {
    fetchCurrentUser()
      .then((profile) => {
        setCurrentUser(profile);
      })
      .catch(() => {
        // Ignore background session restore errors
      });
  }, []);

  // Fetch student profile, offers count and tasks count when user/institution changes
  useEffect(() => {
    const institutionId = currentUser?.memberships?.[0]?.institution_id;
    if (!institutionId || !currentUser) {
      return;
    }

    // 1. Student profile
    fetchMyStudentProfile(institutionId)
      .then((p) => setStudentProfile(p))
      .catch(() => setStudentProfile(null));

    // 2. Active help offers count
    fetchMyHelpOffers(institutionId)
      .then((offers) => setMyOffersCount(offers.filter((o) => o.status === "active").length))
      .catch(() => setMyOffersCount(0));

    // 3. Pending follow-up tasks count
    fetchMyFollowUpTasks(institutionId, { is_completed: false })
      .then((res) => setPendingTasksCount(res.total ?? res.items?.length ?? 0))
      .catch(() => setPendingTasksCount(0));
  }, [currentUser]);

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
    setStudentProfile(null);
    setMyOffersCount(0);
    setPendingTasksCount(0);
  };

  const handleToggleSave = (id: string) => {
    setSavedOpportunityIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      try {
        localStorage.setItem("eventsignal_saved_ops", JSON.stringify(Array.from(next)));
      } catch {
        // ignore
      }
      return next;
    });
  };

  const primaryInstitutionId = currentUser?.memberships?.[0]?.institution_id;
  const opportunitiesData = events.state.status === "success" ? events.state.data : null;
  const totalOpportunitiesCount = opportunitiesData?.total ?? opportunitiesData?.items?.length ?? 0;
  const opportunityItems = opportunitiesData?.items ?? [];

  return (
    <div className="flex min-h-screen flex-col bg-page">
      {/* Universal Semantic H1 for screen readers and quality gate verification */}
      <h1 className="sr-only">Evidence Before You Register.</h1>

      {/* Top LinkedIn-style Navigation Bar */}
      <Header
        health={health.state}
        currentView={currentView}
        onViewChange={setCurrentView}
        currentUser={currentUser}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onOpenProfile={() => setIsProfileModalOpen(true)}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      {/* Main Content Area */}
      {currentView === "home" && (
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-5 sm:px-6">
          <div className="flex flex-col lg:flex-row gap-5 items-start">
            {/* Left Column: Profile Card & Campus Navigation */}
            <ProfileSidebar
              currentUser={currentUser}
              studentProfile={studentProfile}
              totalOpportunitiesCount={totalOpportunitiesCount}
              myOffersCount={myOffersCount}
              pendingTasksCount={pendingTasksCount}
              currentView={currentView}
              onViewChange={setCurrentView}
              onOpenProfile={() => setIsProfileModalOpen(true)}
              onOpenAuth={() => setIsAuthModalOpen(true)}
              onSelectCategoryFilter={(cat) => setActiveCategory(cat)}
            />

            {/* Center Column: Welcome Banner, Quick Actions & Opportunity Feed */}
            <div className="flex-1 min-w-0 w-full flex flex-col gap-4">
              <WelcomePanel
                currentUser={currentUser}
                onSubmitOpportunity={() => {
                  setSubmitModalTitle("Submit Opportunity");
                  setIsSubmitModalOpen(true);
                }}
                onShareEvent={() => {
                  setSubmitModalTitle("Share Campus Event");
                  setIsSubmitModalOpen(true);
                }}
                onAskHelp={() => {
                  if (!currentUser) {
                    setIsAuthModalOpen(true);
                  } else {
                    setIsNeedModalOpen(true);
                  }
                }}
                onOfferHelp={() => {
                  if (!currentUser) {
                    setIsAuthModalOpen(true);
                  } else {
                    setCurrentView("offers");
                  }
                }}
                onCreateHandover={() => {
                  if (!currentUser) {
                    setIsAuthModalOpen(true);
                  } else {
                    setCurrentView("legacy");
                  }
                }}
              />

              <OpportunityFeed
                eventsState={events.state}
                onRetry={events.reload}
                onSelectOpportunity={(op) => setSelectedOpportunity(op)}
                onSubmitOpportunity={() => {
                  setSubmitModalTitle("Submit Opportunity");
                  setIsSubmitModalOpen(true);
                }}
                activeCategory={activeCategory}
                onCategoryChange={setActiveCategory}
                searchQuery={searchQuery}
                savedOpportunityIds={savedOpportunityIds}
                onToggleSave={handleToggleSave}
              />
            </div>

            {/* Right Column: Discovery Panels */}
            <DiscoveryPanels
              currentUser={currentUser}
              opportunities={opportunityItems}
              onViewChange={setCurrentView}
              onSelectOpportunity={(op) => setSelectedOpportunity(op)}
              onRequestHelpConnection={(offer) => setSelectedHelpOfferForConnect(offer)}
              onOpenAuth={() => setIsAuthModalOpen(true)}
            />
          </div>
        </main>
      )}

      {/* Specialized Product Area Views */}
      {currentView !== "home" && (
        <main className="mx-auto w-full max-w-5xl flex-1 px-5 py-8 sm:px-8 sm:py-10">
          {currentView === "opportunities" && (
            <>
              <div className="max-w-2xl">
                <h2 className="font-display text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl text-ink">
                  Evidence Before You Register.
                </h2>
                <p className="mt-4 text-base leading-relaxed text-ink-soft">
                  Evaluate and compare events using source-linked evidence. EventSignal shows what each claim rests on, so the
                  decision stays with you.
                </p>
              </div>

              <div className="mt-10 grid gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
                <EventWorkspace state={events.state} onRetry={events.reload} />
                <ServiceStatusPanel state={health.state} onRetry={health.reload} />
              </div>
            </>
          )}

          {currentView === "institutions" && (
            <>
              <div className="max-w-2xl mb-8">
                <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl text-ink">
                  Institutional Workspaces & Identity
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-ink-soft">
                  Multi-college isolation, authorized community members, official campus leadership, and verified appointments.
                </p>
              </div>

              <InstitutionWorkspacePanel
                currentUser={currentUser}
                onOpenAuth={() => setIsAuthModalOpen(true)}
              />
            </>
          )}

          {currentView === "network" && (
            <>
              <div className="max-w-2xl mb-8">
                <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl text-ink">
                  Campus Network & Discovery
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-ink-soft">
                  Discover students, alumni mentors, and official campus leaders within your college workspace.
                  Building a network, not a static directory.
                </p>
              </div>

              <MemberDiscoveryPanel
                currentUser={currentUser}
                onOpenAuth={() => setIsAuthModalOpen(true)}
                onSelectMemberForOffers={() => {
                  setCurrentView("offers");
                }}
              />
            </>
          )}

          {currentView === "offers" && (
            <>
              <div className="max-w-2xl mb-8">
                <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl text-ink">
                  Campus Mentorship & Help Offers
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-ink-soft">
                  Explicit, consent-backed help offers from alumni, faculty, and senior peers.
                  Request portfolio reviews, mock interviews, or project feedback.
                </p>
              </div>

              <HelpOffersPanel
                currentUser={currentUser}
                onOpenAuth={() => setIsAuthModalOpen(true)}
              />
            </>
          )}

          {currentView === "legacy" && (
            <>
              <div className="max-w-2xl mb-8">
                <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl text-ink">
                  Gap Matching & EventSignal Legacy
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-ink-soft">
                  Declare specific academic or career challenges for deterministic helper matching. Preserve institutional
                  memory, tenure handovers, event retrospectives, and follow-up commitments.
                </p>
              </div>

              <LegacyMatchingPanel
                currentUser={currentUser}
                onOpenAuth={() => setIsAuthModalOpen(true)}
              />
            </>
          )}

          {currentView === "partnerships" && (
            <>
              <div className="max-w-2xl mb-8">
                <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl text-ink">
                  Partnerships, Promotion & Pilot Readiness
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-ink-soft">
                  Connect events with verified brand partners, request transparent cross-college promotion campaigns,
                  securely import approved alumni records with strict consent privacy, and monitor real pilot metrics.
                </p>
              </div>

              <PartnershipsPromotionPanel
                currentUser={currentUser}
                onOpenAuth={() => setIsAuthModalOpen(true)}
              />
            </>
          )}
        </main>
      )}

      {/* Footer */}
      <footer className="mt-auto border-t border-line bg-card py-6">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 space-y-4">
          <ServiceStatusPanel state={health.state} onRetry={health.reload} />
          <p className="text-xs text-ink-soft">
            EventSignal · AI extracts. Rules evaluate. Evidence explains. Students decide.
          </p>
        </div>
      </footer>

      {/* Global Modals */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        currentUser={currentUser}
        onAuthSuccess={(profile) => setCurrentUser(profile)}
        onLogout={handleLogout}
      />

      {currentUser && (
        <MyProfileModal
          isOpen={isProfileModalOpen}
          onClose={() => setIsProfileModalOpen(false)}
          currentUser={currentUser}
        />
      )}

      <OpportunityDetailModal
        opportunity={selectedOpportunity}
        onClose={() => setSelectedOpportunity(null)}
        onRefresh={() => events.reload()}
      />

      <QuickIntakeModal
        isOpen={isSubmitModalOpen}
        title={submitModalTitle}
        onClose={() => setIsSubmitModalOpen(false)}
        onSuccess={() => {
          events.reload();
        }}
      />

      <ConnectModal
        offer={selectedHelpOfferForConnect}
        institutionId={primaryInstitutionId}
        onClose={() => setSelectedHelpOfferForConnect(null)}
        onSuccess={() => {
          // optional notification toast
        }}
      />

      <QuickNeedModal
        isOpen={isNeedModalOpen}
        institutionId={primaryInstitutionId}
        onClose={() => setIsNeedModalOpen(false)}
        onSuccess={() => {
          setCurrentView("legacy");
        }}
      />
    </div>
  );
}
