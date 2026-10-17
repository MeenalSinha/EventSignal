import { useEffect, useState } from "react";
import { AuthModal } from "./components/AuthModal";
import { EventWorkspace } from "./components/EventWorkspace";
import { Header, type AppView } from "./components/Header";
import { HelpOffersPanel } from "./components/HelpOffersPanel";
import { InstitutionWorkspacePanel } from "./components/InstitutionWorkspacePanel";
import { MemberDiscoveryPanel } from "./components/MemberDiscoveryPanel";
import { MyProfileModal } from "./components/MyProfileModal";
import { ServiceStatusPanel } from "./components/ServiceStatusPanel";
import { useRemoteResource } from "./hooks/useRemoteResource";
import { fetchCurrentUser, logoutUser } from "./services/authService";
import { fetchEvents } from "./services/eventsService";
import { fetchHealth } from "./services/healthService";
import type { UserProfile } from "./types/auth";

export default function App() {
  const health = useRemoteResource(fetchHealth);
  const events = useRemoteResource(fetchEvents);

  const [currentView, setCurrentView] = useState<AppView>("opportunities");
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  useEffect(() => {
    fetchCurrentUser()
      .then((profile) => {
        setCurrentUser(profile);
      })
      .catch(() => {
        // Ignore background session restore errors
      });
  }, []);

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header
        health={health.state}
        currentView={currentView}
        onViewChange={setCurrentView}
        currentUser={currentUser}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onOpenProfile={() => setIsProfileModalOpen(true)}
      />

      <main className="mx-auto w-full max-w-5xl flex-1 px-5 py-10 sm:px-8 sm:py-14">
        {currentView === "opportunities" && (
          <>
            <div className="max-w-2xl">
              <h1 className="font-display text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
                Evidence Before You Register.
              </h1>
              <p className="mt-5 text-lg leading-relaxed text-ink-soft">
                Evaluate and compare events using source-linked evidence. EventSignal shows what each claim rests on, so the
                decision stays with you.
              </p>
            </div>

            <div className="mt-12 grid gap-10 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
              <EventWorkspace state={events.state} onRetry={events.reload} />
              <ServiceStatusPanel state={health.state} onRetry={health.reload} />
            </div>
          </>
        )}

        {currentView === "institutions" && (
          <>
            <div className="max-w-2xl mb-8">
              <h1 className="font-display text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
                Institutional Workspaces & Identity
              </h1>
              <p className="mt-4 text-base leading-relaxed text-ink-soft">
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
              <h1 className="font-display text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
                Campus Network & Discovery
              </h1>
              <p className="mt-4 text-base leading-relaxed text-ink-soft">
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
              <h1 className="font-display text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
                Campus Mentorship & Help Offers
              </h1>
              <p className="mt-4 text-base leading-relaxed text-ink-soft">
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
      </main>

      <footer className="border-t border-line bg-paper">
        <p className="mx-auto max-w-5xl px-5 py-5 text-sm text-ink-soft sm:px-8">
          AI extracts. Rules evaluate. Evidence explains. Students decide.
        </p>
      </footer>

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
    </div>
  );
}
