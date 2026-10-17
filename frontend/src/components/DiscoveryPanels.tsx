import { useEffect, useState } from "react";
import type { Opportunity } from "../types/opportunity";
import type { HelpOffer } from "../types/helpOffer";
import type { FollowUpTask } from "../types/phase7";
import type { FeedPromotionItem } from "../types/phase8";
import type { UserProfile } from "../types/auth";
import type { AppView } from "./AppNavbar";
import { fetchHelpOffers } from "../services/helpOfferService";
import { fetchMyFollowUpTasks, completeFollowUpTask } from "../services/legacyService";
import { fetchPromotedFeed } from "../services/phase8Service";

interface DiscoveryPanelsProps {
  currentUser: UserProfile | null;
  opportunities: Opportunity[];
  onViewChange: (view: AppView) => void;
  onSelectOpportunity: (opportunity: Opportunity) => void;
  onRequestHelpConnection: (offer: HelpOffer) => void;
  onOpenAuth: () => void;
}

export function DiscoveryPanels({
  currentUser,
  opportunities,
  onViewChange,
  onSelectOpportunity,
  onRequestHelpConnection,
  onOpenAuth,
}: DiscoveryPanelsProps) {
  const [helpers, setHelpers] = useState<HelpOffer[]>([]);
  const [tasks, setTasks] = useState<FollowUpTask[]>([]);
  const [promotions, setPromotions] = useState<FeedPromotionItem[]>([]);
  const [loadedHelpers, setLoadedHelpers] = useState(false);
  const [loadedTasks, setLoadedTasks] = useState(false);

  const primaryInstitutionId = currentUser?.memberships?.[0]?.institution_id;
  const isLoadingHelpers = Boolean(primaryInstitutionId) && !loadedHelpers;
  const isLoadingTasks = Boolean(primaryInstitutionId && currentUser) && !loadedTasks;

  // Filter real campus events from stored opportunities
  const upcomingEvents = opportunities
    .filter((op: Opportunity) => {
      const type = (op.opportunity_type || "").toLowerCase();
      return type.includes("event") || type.includes("campus") || type.includes("hackathon") || type.includes("workshop");
    })
    .slice(0, 3);

  // Load real active help offers for the institution
  useEffect(() => {
    if (!primaryInstitutionId) {
      return;
    }
    let cancelled = false;
    fetchHelpOffers(primaryInstitutionId, { limit: 3 })
      .then((res) => {
        if (!cancelled) {
          setHelpers(res.items || []);
          setLoadedHelpers(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setHelpers([]);
          setLoadedHelpers(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [primaryInstitutionId]);

  // Load real tasks for current user
  useEffect(() => {
    if (!primaryInstitutionId || !currentUser) {
      return;
    }
    let cancelled = false;
    fetchMyFollowUpTasks(primaryInstitutionId, { is_completed: false })
      .then((res) => {
        if (!cancelled) {
          setTasks(res.items || []);
          setLoadedTasks(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setTasks([]);
          setLoadedTasks(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [primaryInstitutionId, currentUser]);

  // Load real promoted campaigns
  useEffect(() => {
    if (!primaryInstitutionId) return;
    fetchPromotedFeed(primaryInstitutionId)
      .then((items) => {
        setPromotions(items || []);
      })
      .catch(() => {
        setPromotions([]);
      });
  }, [primaryInstitutionId]);

  const handleCompleteTask = async (taskId: string) => {
    if (!primaryInstitutionId) return;
    try {
      await completeFollowUpTask(primaryInstitutionId, taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
    } catch {
      // non-blocking
    }
  };

  return (
    <aside className="w-full flex-col gap-3.5 lg:w-72 xl:w-80 shrink-0 flex" aria-label="Campus Discovery">
      {/* 1. Upcoming Campus Events Card */}
      <div className="rounded-xl border border-line bg-card p-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-line">
          <div className="flex items-center gap-1.5 text-xs font-bold text-ink">
            <svg className="h-4 w-4 text-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>Upcoming Campus Events</span>
          </div>
          <button
            type="button"
            onClick={() => onViewChange("opportunities")}
            className="text-[11px] font-semibold text-teal hover:underline"
          >
            View all
          </button>
        </div>

        <div className="mt-3 flex flex-col divide-y divide-line">
          {upcomingEvents.length > 0 ? (
            upcomingEvents.map((evt: Opportunity) => {
              const displayDate = evt.start_date
                ? new Date(evt.start_date).toLocaleDateString(undefined, {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })
                : "Upcoming";

              return (
                <div
                  key={evt.id}
                  onClick={() => onSelectOpportunity(evt)}
                  className="group flex items-start gap-3 py-2.5 cursor-pointer first:pt-0 last:pb-0"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-teal-wash text-teal font-bold text-xs">
                    {(evt.title || evt.event_name || "E").charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h4 className="text-xs font-bold text-ink group-hover:text-teal transition line-clamp-1">
                      {evt.title || evt.event_name || "Campus Event"}
                    </h4>
                    <p className="mt-0.5 text-[11px] text-ink-soft truncate">
                      {evt.organizer || "Host Institution"} · {displayDate}
                    </p>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="py-4 text-center">
              <p className="text-xs text-ink-soft">No campus events scheduled.</p>
              <button
                onClick={() => onViewChange("opportunities")}
                className="mt-1 text-[11px] font-semibold text-teal hover:underline"
              >
                Ingest or browse all
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 2. People Who Offer Help Card */}
      <div className="rounded-xl border border-line bg-card p-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-line">
          <div className="flex items-center gap-1.5 text-xs font-bold text-ink">
            <svg className="h-4 w-4 text-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <span>People Who Offer Help</span>
          </div>
          <button
            type="button"
            onClick={() => onViewChange("offers")}
            className="text-[11px] font-semibold text-teal hover:underline"
          >
            View all
          </button>
        </div>

        <div className="mt-3 flex flex-col divide-y divide-line">
          {isLoadingHelpers ? (
            <div className="py-4 text-center text-xs text-ink-soft">Loading available helpers...</div>
          ) : helpers.length > 0 ? (
            helpers.map((offer: HelpOffer) => {
              const name = offer.creator_name || "Community Mentor";
              const helperInitials = name
                .split(" ")
                .map((n: string) => n[0])
                .slice(0, 2)
                .join("")
                .toUpperCase();

              return (
                <div key={offer.id} className="flex items-start justify-between gap-2.5 py-2.5 first:pt-0 last:pb-0">
                  <div className="flex items-start gap-2.5 min-w-0">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-wash text-xs font-bold text-teal">
                      {helperInitials}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h4 className="text-xs font-bold text-ink truncate">{name}</h4>
                      <p className="text-[10px] text-ink-soft truncate">{offer.creator_role || offer.category}</p>
                      {offer.topics && offer.topics.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {offer.topics.slice(0, 2).map((t: string, i: number) => (
                            <span key={i} className="rounded-full bg-page px-1.5 py-0.5 text-[9px] font-medium text-ink-soft">
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      if (!currentUser) {
                        onOpenAuth();
                      } else {
                        onRequestHelpConnection(offer);
                      }
                    }}
                    className="shrink-0 rounded-lg border border-teal bg-card px-2.5 py-1 text-[11px] font-semibold text-teal transition hover:bg-teal hover:text-white"
                  >
                    Connect
                  </button>
                </div>
              );
            })
          ) : (
            <div className="py-4 text-center">
              <p className="text-xs text-ink-soft">No active help offers in this college workspace yet.</p>
              <button
                onClick={() => onViewChange("offers")}
                className="mt-1 text-[11px] font-semibold text-teal hover:underline"
              >
                Offer help or create one
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 3. Sponsored Opportunities Card */}
      <div className="rounded-xl border border-line bg-card p-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-line">
          <div className="flex items-center gap-1.5 text-xs font-bold text-ink">
            <svg className="h-4 w-4 text-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
            </svg>
            <span>Sponsored Opportunities</span>
          </div>
          <button
            type="button"
            onClick={() => onViewChange("partnerships")}
            className="text-[11px] font-semibold text-teal hover:underline"
          >
            View all
          </button>
        </div>

        <div className="mt-3 flex flex-col divide-y divide-line">
          {promotions.length > 0 ? (
            promotions.slice(0, 2).map((item: FeedPromotionItem) => (
              <div key={item.campaign_id} className="flex items-start gap-3 py-2.5 first:pt-0 last:pb-0">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-50 text-amber-700 font-bold text-xs border border-amber-200">
                  <svg className="h-4 w-4 fill-amber-500 text-amber-600" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <h4 className="text-xs font-bold text-ink truncate">{item.opportunity_title}</h4>
                    <span className="rounded-full bg-amber-100 px-1.5 py-0.2 text-[9px] font-semibold text-amber-800">
                      Sponsored
                    </span>
                  </div>
                  <p className="text-[10px] text-ink-soft truncate">{item.source_institution_name || "Brand Partner"}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="py-3 text-center">
              <p className="text-xs text-ink-soft">Verified campus partnerships & sponsorship prospectuses.</p>
              <button
                onClick={() => onViewChange("partnerships")}
                className="mt-1 text-[11px] font-semibold text-teal hover:underline"
              >
                Browse verified partners
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 4. Your Legacy & Tasks Card */}
      <div className="rounded-xl border border-line bg-card p-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-line">
          <div className="flex items-center gap-1.5 text-xs font-bold text-ink">
            <svg className="h-4 w-4 text-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            <span>Your Legacy & Tasks</span>
          </div>
          <button
            type="button"
            onClick={() => onViewChange("legacy")}
            className="text-[11px] font-semibold text-teal hover:underline"
          >
            View all
          </button>
        </div>

        <div className="mt-3 flex flex-col divide-y divide-line">
          {isLoadingTasks ? (
            <div className="py-4 text-center text-xs text-ink-soft">Loading tasks...</div>
          ) : tasks.length > 0 ? (
            tasks.slice(0, 3).map((task: FollowUpTask) => {
              const dueStr = task.due_date
                ? new Date(task.due_date).toLocaleDateString(undefined, {
                    day: "numeric",
                    month: "short",
                  })
                : "No due date";

              return (
                <div key={task.id} className="flex items-start justify-between gap-2 py-2.5 first:pt-0 last:pb-0">
                  <div className="flex items-start gap-2 min-w-0">
                    <button
                      type="button"
                      onClick={() => handleCompleteTask(task.id)}
                      title="Mark task completed"
                      className="mt-0.5 h-3.5 w-3.5 rounded-sm border border-line hover:border-teal flex items-center justify-center text-teal"
                    >
                      <svg className="h-2.5 w-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </button>
                    <div className="min-w-0 flex-1">
                      <h4 className="text-xs font-semibold text-ink line-clamp-1">{task.title}</h4>
                      <p className="text-[10px] text-ink-soft">Due {dueStr}</p>
                    </div>
                  </div>

                  <span className="shrink-0 rounded-full bg-amber-50 px-2 py-0.5 text-[9px] font-bold text-amber-700">
                    Task
                  </span>
                </div>
              );
            })
          ) : (
            <div className="py-3 text-center">
              <p className="text-xs text-ink-soft">All legacy and follow-up commitments up to date.</p>
              <button
                onClick={() => onViewChange("legacy")}
                className="mt-1 text-[11px] font-semibold text-teal hover:underline"
              >
                Manage handovers
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
