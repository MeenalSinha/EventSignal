import type { UserProfile } from "../types/auth";

interface WelcomePanelProps {
  currentUser: UserProfile | null;
  onSubmitOpportunity: () => void;
  onShareEvent: () => void;
  onAskHelp: () => void;
  onOfferHelp: () => void;
  onCreateHandover: () => void;
}

export function WelcomePanel({
  currentUser,
  onSubmitOpportunity,
  onShareEvent,
  onAskHelp,
  onOfferHelp,
  onCreateHandover,
}: WelcomePanelProps) {
  const parts = currentUser?.user.full_name?.split(" ");
  const firstName = parts && parts.length > 0 && parts[0] ? parts[0].toUpperCase() : null;

  return (
    <section className="relative overflow-hidden rounded-2xl border border-line bg-card p-5 sm:p-6 shadow-xs">
      <div className="relative z-10 max-w-xl">
        {/* Subtitle / User Greeting */}
        <div className="text-[11px] font-bold uppercase tracking-widest text-ink-muted">
          {firstName ? `WELCOME BACK, ${firstName}!` : "WELCOME TO EVENTSIGNAL"}
        </div>

        {/* Primary Heading */}
        <h2 className="mt-1 font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
          Your campus. Your opportunities. Your network.
        </h2>

        {/* Description */}
        <p className="mt-1.5 text-xs sm:text-sm leading-relaxed text-ink-soft">
          Discover opportunities, connect with people who can help, and carry campus knowledge forward.
        </p>

        {/* Quick Action Buttons Row */}
        <div className="mt-4 flex flex-wrap items-center gap-2 pt-1">
          <button
            type="button"
            onClick={onSubmitOpportunity}
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal px-3.5 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-teal-deep focus:outline-hidden"
          >
            <svg className="h-3.5 w-3.5 text-teal-wash" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <span>Submit Opportunity</span>
          </button>

          <button
            type="button"
            onClick={onShareEvent}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-card px-3 py-2 text-xs font-semibold text-ink shadow-2xs transition hover:border-teal hover:bg-page hover:text-teal focus:outline-hidden"
          >
            <svg className="h-3.5 w-3.5 text-ink-soft" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>Share Event</span>
          </button>

          <button
            type="button"
            onClick={onAskHelp}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-card px-3 py-2 text-xs font-semibold text-ink shadow-2xs transition hover:border-teal hover:bg-page hover:text-teal focus:outline-hidden"
          >
            <svg className="h-3.5 w-3.5 text-ink-soft" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span>Ask for Help</span>
          </button>

          <button
            type="button"
            onClick={onOfferHelp}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-card px-3 py-2 text-xs font-semibold text-ink shadow-2xs transition hover:border-teal hover:bg-page hover:text-teal focus:outline-hidden"
          >
            <svg className="h-3.5 w-3.5 text-ink-soft" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Offer Help</span>
          </button>

          <button
            type="button"
            onClick={onCreateHandover}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-card px-3 py-2 text-xs font-semibold text-ink shadow-2xs transition hover:border-teal hover:bg-page hover:text-teal focus:outline-hidden"
          >
            <svg className="h-3.5 w-3.5 text-ink-soft" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Create Handover</span>
          </button>
        </div>
      </div>

      {/* Decorative campus architecture line art illustration in background */}
      <div className="pointer-events-none absolute -bottom-2 -right-4 hidden sm:block opacity-30 lg:opacity-40">
        <svg width="220" height="130" viewBox="0 0 220 130" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M110 20 L110 10 M105 10 L115 10" stroke="#07879A" strokeWidth="2" strokeLinecap="round" />
          <path d="M85 45 C85 28 135 28 135 45 Z" fill="#E7F5F6" stroke="#07879A" strokeWidth="1.5" />
          <rect x="80" y="45" width="60" height="8" rx="1" fill="#DFE6ED" stroke="#07879A" strokeWidth="1.2" />
          <line x1="88" y1="53" x2="88" y2="100" stroke="#07879A" strokeWidth="2.5" />
          <line x1="102" y1="53" x2="102" y2="100" stroke="#07879A" strokeWidth="2.5" />
          <line x1="118" y1="53" x2="118" y2="100" stroke="#07879A" strokeWidth="2.5" />
          <line x1="132" y1="53" x2="132" y2="100" stroke="#07879A" strokeWidth="2.5" />
          <rect x="30" y="65" width="50" height="40" fill="#E7F5F6" stroke="#07879A" strokeWidth="1.5" />
          <rect x="140" y="65" width="50" height="40" fill="#E7F5F6" stroke="#07879A" strokeWidth="1.5" />
          <rect x="42" y="75" width="8" height="12" rx="4" stroke="#07879A" strokeWidth="1.2" />
          <rect x="60" y="75" width="8" height="12" rx="4" stroke="#07879A" strokeWidth="1.2" />
          <rect x="152" y="75" width="8" height="12" rx="4" stroke="#07879A" strokeWidth="1.2" />
          <rect x="170" y="75" width="8" height="12" rx="4" stroke="#07879A" strokeWidth="1.2" />
          <rect x="15" y="105" width="190" height="6" rx="1" fill="#DFE6ED" stroke="#07879A" strokeWidth="1.2" />
          <rect x="5" y="111" width="210" height="8" rx="1" fill="#DFE6ED" stroke="#07879A" strokeWidth="1.2" />
          <circle cx="20" cy="85" r="14" fill="#BCE2E6" fillOpacity="0.5" />
          <circle cx="200" cy="85" r="14" fill="#BCE2E6" fillOpacity="0.5" />
        </svg>
      </div>
    </section>
  );
}
