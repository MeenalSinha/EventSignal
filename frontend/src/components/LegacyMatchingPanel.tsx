import { useCallback, useEffect, useMemo, useState } from "react";
import {
  acknowledgeHandover,
  completeFollowUpTask,
  createEventMemory,
  createFollowUpTask,
  createHandover,
  createStudentNeed,
  fetchEventMemories,
  fetchHandovers,
  fetchMatchesForNeed,
  fetchMyFollowUpTasks,
  fetchMyStudentNeeds,
  runMatchingForNeed,
  submitHandover,
  updateMatchStatus,
  updateNeedStatus,
} from "../services/legacyService";
import type { UserProfile } from "../types/auth";
import type {
  EventMemory,
  FollowUpTask,
  HelperMatch,
  LegacyHandover,
  NeedUrgency,
  StudentNeed,
} from "../types/phase7";
import { UserAvatar } from "./Avatar";
import { MediaUploadWidget } from "./MediaUploadWidget";

interface InstitutionOption {
  id: string;
  name: string;
  slug: string;
}

interface LegacyMatchingPanelProps {
  currentUser: UserProfile | null;
  onOpenAuth: () => void;
}

type SubTab = "needs" | "handovers" | "memories" | "tasks";

function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof Error) return err.message;
  return fallback;
}

export function LegacyMatchingPanel({
  currentUser,
  onOpenAuth,
}: LegacyMatchingPanelProps) {
  const institutions: InstitutionOption[] = useMemo(() => {
    return (currentUser?.memberships || []).map((m) => ({
      id: m.institution_id,
      name: m.institution_name || "College Workspace",
      slug: m.institution_slug || m.institution_id.slice(0, 8),
    }));
  }, [currentUser]);

  const [selectedInstId, setSelectedInstId] = useState<string>(
    () => currentUser?.memberships?.[0]?.institution_id || ""
  );
  const effectiveInstId = selectedInstId || institutions[0]?.id || "";
  const [refreshKey, setRefreshKey] = useState(0);
  const refreshData = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);
  const [subTab, setSubTab] = useState<SubTab>("needs");
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Needs & Matches State
  const [needs, setNeeds] = useState<StudentNeed[]>([]);
  const [matchesMap, setMatchesMap] = useState<Record<string, HelperMatch[]>>({});
  const [isCreatingNeed, setIsCreatingNeed] = useState(false);
  const [needTitle, setNeedTitle] = useState("");
  const [needCategory, setNeedCategory] = useState("mock_interview");
  const [needDesc, setNeedDesc] = useState("");
  const [needDeliveryMode, setNeedDeliveryMode] = useState("remote");
  const [needUrgency, setNeedUrgency] = useState<NeedUrgency>("medium");

  // Handovers State
  const [handovers, setHandovers] = useState<LegacyHandover[]>([]);
  const [isCreatingHandover, setIsCreatingHandover] = useState(false);
  const [hoTitle, setHoTitle] = useState("");
  const [hoAccomplishments, setHoAccomplishments] = useState("");
  const [hoOngoingWork, setHoOngoingWork] = useState("");
  const [hoLessonsLearned, setHoLessonsLearned] = useState("");
  const [hoFirstSteps, setHoFirstSteps] = useState("");

  // Memories State
  const [memories, setMemories] = useState<EventMemory[]>([]);
  const [isCreatingMemory, setIsCreatingMemory] = useState(false);
  const [memTitle, setMemTitle] = useState("");
  const [memWhatWorked, setMemWhatWorked] = useState("");
  const [memWhatDidNot, setMemWhatDidNot] = useState("");
  const [memAttendance, setMemAttendance] = useState("");
  const [memOutcome, setMemOutcome] = useState("");
  const [memTags, setMemTags] = useState("");

  // Tasks State
  const [tasks, setTasks] = useState<FollowUpTask[]>([]);
  const [isCreatingTask, setIsCreatingTask] = useState(false);
  const [taskTitle, setTaskTitle] = useState("");
  const [taskDesc, setTaskDesc] = useState("");
  const [taskPriority, setTaskPriority] = useState<"low" | "medium" | "high">("medium");

  useEffect(() => {
    if (!effectiveInstId || !currentUser) return;
    let isMounted = true;

    async function loadData() {
      try {
        if (subTab === "needs") {
          const res = await fetchMyStudentNeeds(effectiveInstId);
          if (!isMounted) return;
          setNeeds(res.items);
          for (const need of res.items) {
            fetchMatchesForNeed(effectiveInstId, need.id)
              .then((matches) => {
                if (isMounted) {
                  setMatchesMap((prev) => ({ ...prev, [need.id]: matches }));
                }
              })
              .catch((err: unknown) => {
                console.error("Failed to fetch matches for need", err);
              });
          }
        } else if (subTab === "handovers") {
          const res = await fetchHandovers(effectiveInstId);
          if (isMounted) setHandovers(res.items);
        } else if (subTab === "memories") {
          const res = await fetchEventMemories(effectiveInstId);
          if (isMounted) setMemories(res.items);
        } else if (subTab === "tasks") {
          const res = await fetchMyFollowUpTasks(effectiveInstId);
          if (isMounted) setTasks(res.items);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setFeedback({ type: "error", message: getErrorMessage(err, "Failed to load tab data") });
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    void loadData();

    return () => {
      isMounted = false;
    };
  }, [effectiveInstId, currentUser, subTab, refreshKey]);

  // Need Handlers
  const handleCreateNeed = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId) return;
    setIsLoading(true);
    try {
      await createStudentNeed(effectiveInstId, {
        title: needTitle,
        category: needCategory,
        description: needDesc || undefined,
        preferred_delivery_mode: needDeliveryMode || undefined,
        urgency: needUrgency,
      });
      setFeedback({ type: "success", message: "Support need declared successfully!" });
      setIsCreatingNeed(false);
      setNeedTitle("");
      setNeedDesc("");
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not declare need.") });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunMatching = async (needId: string) => {
    if (!effectiveInstId) return;
    const targetNeed = needs.find((n) => n.id === needId);
    if (targetNeed && targetNeed.status !== "open") {
      setFeedback({
        type: "success",
        message: `Matches are already evaluated for "${targetNeed.title}". Compatible mentors are listed below.`,
      });
      return;
    }
    setIsLoading(true);
    try {
      const matches = await runMatchingForNeed(effectiveInstId, needId);
      setMatchesMap((prev) => ({ ...prev, [needId]: matches }));
      setFeedback({
        type: "success",
        message: `Matching engine evaluated offers: found ${matches.length} compatible helper(s)!`,
      });
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Matching engine run failed.") });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateMatch = async (matchId: string, needId: string, status: "accepted" | "dismissed") => {
    if (!effectiveInstId) return;
    try {
      await updateMatchStatus(effectiveInstId, matchId, status);
      setFeedback({ type: "success", message: `Match updated to ${status}.` });
      // reload matches for this need
      const updated = await fetchMatchesForNeed(effectiveInstId, needId);
      setMatchesMap((prev) => ({ ...prev, [needId]: updated }));
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not update match.") });
    }
  };

  const handleResolveNeed = async (needId: string) => {
    if (!effectiveInstId) return;
    try {
      await updateNeedStatus(effectiveInstId, needId, "resolved");
      setFeedback({ type: "success", message: "Need marked as resolved!" });
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not resolve need.") });
    }
  };

  // Handover Handlers
  const handleCreateHandover = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId) return;
    setIsLoading(true);
    try {
      await createHandover(effectiveInstId, {
        title: hoTitle,
        accomplishments_summary: hoAccomplishments || undefined,
        ongoing_work: hoOngoingWork || undefined,
        lessons_learned: hoLessonsLearned || undefined,
        recommended_first_steps: hoFirstSteps || undefined,
      });
      setFeedback({ type: "success", message: "Draft legacy handover created!" });
      setIsCreatingHandover(false);
      setHoTitle("");
      setHoAccomplishments("");
      setHoOngoingWork("");
      setHoLessonsLearned("");
      setHoFirstSteps("");
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not create handover.") });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitHandover = async (handoverId: string) => {
    if (!effectiveInstId) return;
    try {
      await submitHandover(effectiveInstId, handoverId);
      setFeedback({ type: "success", message: "Handover submitted for successor review!" });
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not submit handover.") });
    }
  };

  const handleAcknowledgeHandover = async (handoverId: string) => {
    if (!effectiveInstId) return;
    try {
      await acknowledgeHandover(effectiveInstId, handoverId);
      setFeedback({ type: "success", message: "Handover acknowledged! Knowledge transfer complete." });
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not acknowledge handover.") });
    }
  };

  // Memory Handlers
  const handleCreateMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId) return;
    setIsLoading(true);
    try {
      const parsedTags = memTags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      await createEventMemory(effectiveInstId, {
        title: memTitle,
        what_worked: memWhatWorked || undefined,
        what_did_not_work: memWhatDidNot || undefined,
        attendance_notes: memAttendance || undefined,
        outcome_summary: memOutcome || undefined,
        tags: parsedTags,
      });
      setFeedback({ type: "success", message: "Institutional event memory documented!" });
      setIsCreatingMemory(false);
      setMemTitle("");
      setMemWhatWorked("");
      setMemWhatDidNot("");
      setMemAttendance("");
      setMemOutcome("");
      setMemTags("");
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not record memory.") });
    } finally {
      setIsLoading(false);
    }
  };

  // Task Handlers
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId || !currentUser) return;
    setIsLoading(true);
    try {
      await createFollowUpTask(effectiveInstId, {
        title: taskTitle,
        description: taskDesc || undefined,
        assignee_user_id: currentUser.user.id,
        priority: taskPriority,
      });
      setFeedback({ type: "success", message: "Follow-up task created!" });
      setIsCreatingTask(false);
      setTaskTitle("");
      setTaskDesc("");
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not create task.") });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompleteTask = async (taskId: string) => {
    if (!effectiveInstId) return;
    try {
      await completeFollowUpTask(effectiveInstId, taskId);
      setFeedback({ type: "success", message: "Task marked completed!" });
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not complete task.") });
    }
  };

  if (!currentUser) {
    return (
      <div className="rounded-2xl border border-line bg-paper-warm p-8 text-center sm:p-12">
        <h3 className="font-display text-2xl font-semibold">Sign in to Access Campus Matching & Legacy</h3>
        <p className="mx-auto mt-2 max-w-md text-sm text-ink-soft">
          EventSignal Gap-to-Helper Matching and Institutional Memory are college-scoped. Sign in to declare support
          needs, view matches, and browse tenure handovers.
        </p>
        <button
          onClick={onOpenAuth}
          className="mt-6 rounded-xl bg-ink px-6 py-2.5 text-sm font-semibold text-paper hover:bg-ink-soft transition"
        >
          Sign In / Register
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Institution Picker */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-line bg-paper p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <label htmlFor="inst-select" className="text-xs font-semibold uppercase tracking-wider text-ink-soft">
            College Workspace:
          </label>
          <select
            id="inst-select"
            value={effectiveInstId}
            onChange={(e) => setSelectedInstId(e.target.value)}
            className="rounded-lg border border-line bg-paper-warm px-3 py-1.5 text-sm font-medium text-ink focus:border-ink focus:outline-none"
          >
            {institutions.map((inst) => (
              <option key={inst.id} value={inst.id}>
                {inst.name} ({inst.slug})
              </option>
            ))}
          </select>
        </div>

        {/* Sub-tab Navigation */}
        <div className="flex flex-wrap gap-1 rounded-xl bg-paper-warm p-1 text-xs font-semibold">
          <button
            onClick={() => setSubTab("needs")}
            className={`rounded-lg px-3 py-1.5 transition ${
              subTab === "needs" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
            }`}
          >
            Support Needs & Matching
          </button>
          <button
            onClick={() => setSubTab("handovers")}
            className={`rounded-lg px-3 py-1.5 transition ${
              subTab === "handovers" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
            }`}
          >
            Legacy Handovers
          </button>
          <button
            onClick={() => setSubTab("memories")}
            className={`rounded-lg px-3 py-1.5 transition ${
              subTab === "memories" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
            }`}
          >
            Event Memories
          </button>
          <button
            onClick={() => setSubTab("tasks")}
            className={`rounded-lg px-3 py-1.5 transition ${
              subTab === "tasks" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
            }`}
          >
            Follow-Up Tasks
          </button>
        </div>
      </div>

      {feedback && (
        <div
          className={`flex items-center justify-between gap-3 rounded-xl p-4 text-sm font-medium ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
              : "bg-rose-50 text-rose-800 border border-rose-200"
          }`}
        >
          <span>{feedback.message}</span>
          {feedback.type === "error" && (
            <button
              type="button"
              onClick={refreshData}
              className="rounded-lg bg-rose-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-800 shrink-0"
            >
              Retry
            </button>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* SUB-TAB 1: NEEDS & MATCHING */}
      {/* ------------------------------------------------------------------ */}
      {subTab === "needs" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-xl font-semibold">My Academic & Career Needs</h2>
              <p className="text-xs text-ink-soft">
                Declare your specific challenge. The matching engine evaluates verified help offers transparently.
              </p>
            </div>
            <button
              onClick={() => setIsCreatingNeed(!isCreatingNeed)}
              className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition"
            >
              {isCreatingNeed ? "Cancel" : "+ Declare Support Need"}
            </button>
          </div>

          {isCreatingNeed && (
            <form onSubmit={handleCreateNeed} className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
              <h3 className="font-semibold text-sm">Declare a Specific Support Need</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Title *</label>
                  <input
                    type="text"
                    required
                    value={needTitle}
                    onChange={(e) => setNeedTitle(e.target.value)}
                    placeholder="e.g. Need mock interview practice for SWE placements"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Category *</label>
                  <select
                    value={needCategory}
                    onChange={(e) => setNeedCategory(e.target.value)}
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  >
                    <option value="mock_interview">Mock Interview</option>
                    <option value="resume_review">Resume Review</option>
                    <option value="research_guidance">Research Guidance</option>
                    <option value="higher_studies">Higher Studies Advice</option>
                    <option value="project_feedback">Project Feedback</option>
                    <option value="industry_transition">Industry Transition</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Preferred Delivery Mode</label>
                  <select
                    value={needDeliveryMode}
                    onChange={(e) => setNeedDeliveryMode(e.target.value)}
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  >
                    <option value="remote">Remote (Video / Chat)</option>
                    <option value="in_person">In-Person (On Campus)</option>
                    <option value="hybrid">Hybrid</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Urgency</label>
                  <select
                    value={needUrgency}
                    onChange={(e) => setNeedUrgency(e.target.value as NeedUrgency)}
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  >
                    <option value="low">Low (General guidance)</option>
                    <option value="medium">Medium (Upcoming deadline)</option>
                    <option value="high">High (Immediate upcoming interview)</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-soft mb-1">Description & Topic Details</label>
                <textarea
                  rows={3}
                  value={needDesc}
                  onChange={(e) => setNeedDesc(e.target.value)}
                  placeholder="Detail your target role, technologies, algorithms, or questions..."
                  className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="rounded-lg bg-ink px-5 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition disabled:opacity-50"
              >
                {isLoading ? "Saving..." : "Submit Support Need"}
              </button>
            </form>
          )}

          {needs.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line p-8 text-center text-sm text-ink-soft">
              No declared needs in this institution yet. Declare one above to find matching alumni and senior mentors.
            </div>
          ) : (
            <div className="space-y-4">
              {needs.map((need) => {
                const rawMatches = matchesMap[need.id];
                const matches: HelperMatch[] = Array.isArray(rawMatches)
                  ? rawMatches
                  : (rawMatches as any)?.items || [];
                return (
                  <div key={need.id} className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                              need.status === "matched"
                                ? "bg-emerald-100 text-emerald-800"
                                : need.status === "resolved"
                                ? "bg-blue-100 text-blue-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {need.status}
                          </span>
                          <span className="rounded-full bg-paper-warm px-2 py-0.5 text-[10px] font-medium text-ink-soft uppercase">
                            Urgency: {need.urgency}
                          </span>
                          <span className="text-xs text-ink-soft">Category: {need.category}</span>
                        </div>
                        <h3 className="mt-1 font-semibold text-base">{need.title}</h3>
                      </div>
                      <div className="flex items-center gap-2">
                        {need.status !== "resolved" && (
                          <button
                            onClick={() => handleResolveNeed(need.id)}
                            className="rounded-lg border border-line px-3 py-1.5 text-xs font-medium text-ink-soft hover:text-ink hover:bg-paper-warm transition"
                          >
                            Mark Resolved
                          </button>
                        )}
                        {need.status === "open" ? (
                          <button
                            onClick={() => handleRunMatching(need.id)}
                            disabled={isLoading}
                            className="rounded-lg bg-ink px-3 py-1.5 text-xs font-semibold text-paper hover:bg-ink-soft transition disabled:opacity-50"
                          >
                            Find Helper Matches
                          </button>
                        ) : need.status === "matched" ? (
                          <span className="rounded-lg border border-line bg-paper-warm px-2.5 py-1 text-[11px] font-medium text-ink-soft">
                            Matches Evaluated
                          </span>
                        ) : null}
                      </div>
                    </div>

                    {need.description && <p className="text-sm text-ink-soft">{need.description}</p>}

                    {/* Matched Helpers Section */}
                    <div className="mt-4 rounded-xl bg-paper-warm p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">
                          Helper Matches ({matches.length})
                        </span>
                        <span className="text-[11px] text-ink-soft">Deterministic Rule Scorer v1.0</span>
                      </div>

                      {matches.length === 0 ? (
                        <p className="text-xs italic text-ink-soft">
                          No matches computed yet. Click "Find Helper Matches" to query active help offers.
                        </p>
                      ) : (
                        <div className="space-y-3">
                          {matches.map((m) => (
                            <div key={m.id} className="rounded-lg border border-line bg-paper p-4 space-y-3">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-sm">{m.offer_title || "Help Offer"}</span>
                                    <span
                                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                                        m.status === "accepted"
                                          ? "bg-emerald-100 text-emerald-800"
                                          : m.status === "dismissed"
                                          ? "bg-zinc-100 text-zinc-600"
                                          : "bg-blue-100 text-blue-800"
                                      }`}
                                    >
                                      {m.status}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-2 mt-1">
                                    <UserAvatar name={m.offer_owner_name || "Campus Helper"} size="xs" />
                                    <p className="text-xs text-ink-soft">
                                      Offered by: <span className="font-medium text-ink">{m.offer_owner_name || "Campus Helper"}</span> • Mode:{" "}
                                      {m.offer_delivery_mode || "Remote"}
                                    </p>
                                  </div>
                                </div>
                                <div className="text-right">
                                  <span className="text-xs font-semibold text-ink-soft uppercase tracking-wider">
                                    Match Fit
                                  </span>
                                  <div className="font-display text-lg font-bold text-ink">
                                    {Math.round(m.score * 100)}%
                                  </div>
                                </div>
                              </div>

                              {/* Rule Breakdown Drawer */}
                              <div className="border-t border-line pt-2 text-xs space-y-1.5">
                                <span className="font-semibold text-[11px] uppercase tracking-wider text-ink-soft">
                                  Scoring Evidence:
                                </span>
                                {(Array.isArray(m.rule_results) ? m.rule_results : []).map((r, i) => (
                                  <div key={i} className="flex items-start justify-between gap-4 text-[11px]">
                                    <div className="flex items-center gap-1.5">
                                      <span
                                        className={`inline-block h-2 w-2 rounded-full ${
                                          r.matched === true
                                            ? "bg-emerald-500"
                                            : r.matched === false
                                            ? "bg-rose-400"
                                            : "bg-zinc-300"
                                        }`}
                                      />
                                      <span className="font-medium text-ink">
                                        {r.rule.replace(/_/g, " ")}:
                                      </span>
                                      <span className="text-ink-soft">{r.evidence}</span>
                                    </div>
                                    <span className="font-mono text-ink-soft shrink-0">
                                      +{(r.contribution * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                ))}
                                {m.uncertainty_notes && (
                                  <p className="mt-1 text-[11px] text-amber-700 bg-amber-50 p-1.5 rounded">
                                    Note: {m.uncertainty_notes}
                                  </p>
                                )}
                              </div>

                              {/* Action Buttons */}
                              <div className="flex justify-end gap-2 pt-1 border-t border-line">
                                {m.status !== "accepted" && (
                                  <button
                                    onClick={() => handleUpdateMatch(m.id, need.id, "accepted")}
                                    className="rounded-lg bg-ink px-3 py-1 text-xs font-semibold text-paper hover:bg-ink-soft transition"
                                  >
                                    Accept Match
                                  </button>
                                )}
                                {m.status !== "dismissed" && (
                                  <button
                                    onClick={() => handleUpdateMatch(m.id, need.id, "dismissed")}
                                    className="rounded-lg border border-line px-3 py-1 text-xs font-medium text-ink-soft hover:bg-paper-warm transition"
                                  >
                                    Dismiss
                                  </button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* SUB-TAB 2: HANDOVERS */}
      {/* ------------------------------------------------------------------ */}
      {subTab === "handovers" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-xl font-semibold">Campus Leadership Handovers</h2>
              <p className="text-xs text-ink-soft">
                Institutional memory preserved across club leads, chapter heads, and student coordinators.
              </p>
            </div>
            <button
              onClick={() => setIsCreatingHandover(!isCreatingHandover)}
              className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition"
            >
              {isCreatingHandover ? "Cancel" : "+ Draft Handover"}
            </button>
          </div>

          {isCreatingHandover && (
            <form onSubmit={handleCreateHandover} className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
              <h3 className="font-semibold text-sm">Create Tenure Handover Document</h3>
              <div>
                <label className="block text-xs font-medium text-ink-soft mb-1">Handover Title *</label>
                <input
                  type="text"
                  required
                  value={hoTitle}
                  onChange={(e) => setHoTitle(e.target.value)}
                  placeholder="e.g. 2025 GDSC Lead Handover to 2026 Core Team"
                  className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Accomplishments Summary</label>
                  <textarea
                    rows={3}
                    value={hoAccomplishments}
                    onChange={(e) => setHoAccomplishments(e.target.value)}
                    placeholder="Key milestones reached, sponsorships closed, hackathons hosted..."
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Ongoing Work in Progress</label>
                  <textarea
                    rows={3}
                    value={hoOngoingWork}
                    onChange={(e) => setHoOngoingWork(e.target.value)}
                    placeholder="Unfinished projects, pending approvals, vendor contacts..."
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Lessons Learned & Pitfalls</label>
                  <textarea
                    rows={3}
                    value={hoLessonsLearned}
                    onChange={(e) => setHoLessonsLearned(e.target.value)}
                    placeholder="Budget delays, room booking timeline rules, dean sign-offs..."
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Recommended First Steps</label>
                  <textarea
                    rows={3}
                    value={hoFirstSteps}
                    onChange={(e) => setHoFirstSteps(e.target.value)}
                    placeholder="Schedule faculty meeting within week 1, update GitHub access..."
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="rounded-lg bg-ink px-5 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition disabled:opacity-50"
              >
                {isLoading ? "Saving..." : "Save Draft Handover"}
              </button>
            </form>
          )}

          {handovers.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line p-8 text-center text-sm text-ink-soft">
              No handovers logged for this institution yet. Outgoing leaders can document their tenure above.
            </div>
          ) : (
            <div className="space-y-4">
              {handovers.map((h) => (
                <div key={h.id} className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                            h.status === "acknowledged"
                              ? "bg-emerald-100 text-emerald-800"
                              : h.status === "submitted"
                              ? "bg-blue-100 text-blue-800"
                              : h.status === "superseded"
                              ? "bg-zinc-100 text-zinc-500 line-through"
                              : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {h.status}
                        </span>
                        <span className="text-xs text-ink-soft font-mono">v{h.version}</span>
                        {h.position_title && (
                          <span className="rounded-full bg-paper-warm px-2 py-0.5 text-[10px] font-medium text-ink">
                            {h.position_title}
                          </span>
                        )}
                      </div>
                      <h3 className="mt-1 font-semibold text-base">{h.title}</h3>
                      <p className="text-xs text-ink-soft">
                        Outgoing Lead: {h.outgoing_user_name || "Author"} • Successor:{" "}
                        {h.incoming_user_name || "Unassigned"}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {h.status === "draft" && (
                        <button
                          onClick={() => handleSubmitHandover(h.id)}
                          className="rounded-lg bg-ink px-3 py-1.5 text-xs font-semibold text-paper hover:bg-ink-soft transition"
                        >
                          Submit Handover
                        </button>
                      )}
                      {h.status === "submitted" && (
                        <button
                          onClick={() => handleAcknowledgeHandover(h.id)}
                          className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 transition"
                        >
                          Acknowledge Handover
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2 text-xs">
                    {h.accomplishments_summary && (
                      <div className="rounded-lg bg-paper-warm p-3">
                        <span className="font-semibold text-ink block mb-1">Accomplishments</span>
                        <p className="text-ink-soft">{h.accomplishments_summary}</p>
                      </div>
                    )}
                    {h.ongoing_work && (
                      <div className="rounded-lg bg-paper-warm p-3">
                        <span className="font-semibold text-ink block mb-1">Ongoing Work</span>
                        <p className="text-ink-soft">{h.ongoing_work}</p>
                      </div>
                    )}
                    {h.lessons_learned && (
                      <div className="rounded-lg bg-paper-warm p-3">
                        <span className="font-semibold text-ink block mb-1">Lessons Learned</span>
                        <p className="text-ink-soft">{h.lessons_learned}</p>
                      </div>
                    )}
                    {h.recommended_first_steps && (
                      <div className="rounded-lg bg-paper-warm p-3">
                        <span className="font-semibold text-ink block mb-1">Recommended First Steps</span>
                        <p className="text-ink-soft">{h.recommended_first_steps}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* SUB-TAB 3: EVENT MEMORIES */}
      {/* ------------------------------------------------------------------ */}
      {subTab === "memories" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-xl font-semibold">Campus Event Retrospectives & Memories</h2>
              <p className="text-xs text-ink-soft">
                Institutional post-mortems so future organizers learn from past successes and missteps.
              </p>
            </div>
            <button
              onClick={() => setIsCreatingMemory(!isCreatingMemory)}
              className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition"
            >
              {isCreatingMemory ? "Cancel" : "+ Record Memory"}
            </button>
          </div>

          {isCreatingMemory && (
            <form onSubmit={handleCreateMemory} className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
              <h3 className="font-semibold text-sm">Document Event Retrospective</h3>
              <div>
                <label className="block text-xs font-medium text-ink-soft mb-1">Event / Milestone Title *</label>
                <input
                  type="text"
                  required
                  value={memTitle}
                  onChange={(e) => setMemTitle(e.target.value)}
                  placeholder="e.g. Annual Campus Hackathon 2025 Retrospective"
                  className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">What Worked Well</label>
                  <textarea
                    rows={3}
                    value={memWhatWorked}
                    onChange={(e) => setMemWhatWorked(e.target.value)}
                    placeholder="Discord server engagement, lightning talks, food delivery..."
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">What Did NOT Work</label>
                  <textarea
                    rows={3}
                    value={memWhatDidNot}
                    onChange={(e) => setMemWhatDidNot(e.target.value)}
                    placeholder="Wi-Fi bandwidth collapsed during demo, projector adaptor missing..."
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Attendance & Participation Notes</label>
                  <textarea
                    rows={2}
                    value={memAttendance}
                    onChange={(e) => setMemAttendance(e.target.value)}
                    placeholder="250 registered, 180 checked in. Heavy turnout from 2nd year CSE..."
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Outcome & Next Steps</label>
                  <textarea
                    rows={2}
                    value={memOutcome}
                    onChange={(e) => setMemOutcome(e.target.value)}
                    placeholder="Top 3 teams received placement fast-tracks from sponsor..."
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-soft mb-1">Tags (comma-separated)</label>
                <input
                  type="text"
                  value={memTags}
                  onChange={(e) => setMemTags(e.target.value)}
                  placeholder="hackathon, tech, placement, logistics"
                  className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="rounded-lg bg-ink px-5 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition disabled:opacity-50"
              >
                {isLoading ? "Saving..." : "Save Retrospective"}
              </button>
            </form>
          )}

          {memories.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line p-8 text-center text-sm text-ink-soft">
              No event memories logged yet. Record lessons from your latest workshop or hackathon above.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {memories.map((m) => (
                <div key={m.id} className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-base">{m.title}</h3>
                    {m.is_current && (
                      <span className="rounded-full bg-emerald-100 text-emerald-800 px-2 py-0.5 text-[10px] font-semibold uppercase">
                        Current
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-ink-soft">Documented by: {m.author_name || "Campus Organizer"}</p>

                  {m.what_worked && (
                    <div className="rounded-lg bg-emerald-50/50 border border-emerald-100 p-2.5 text-xs">
                      <span className="font-semibold text-emerald-900 block mb-0.5">What Worked:</span>
                      <p className="text-emerald-800">{m.what_worked}</p>
                    </div>
                  )}

                  {m.what_did_not_work && (
                    <div className="rounded-lg bg-rose-50/50 border border-rose-100 p-2.5 text-xs">
                      <span className="font-semibold text-rose-900 block mb-0.5">What Didn't Work:</span>
                      <p className="text-rose-800">{m.what_did_not_work}</p>
                    </div>
                  )}

                  {m.tags && m.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {m.tags.map((t, idx) => (
                        <span key={idx} className="rounded bg-paper-warm px-2 py-0.5 text-[10px] text-ink-soft">
                          #{t}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Attached Cloudinary Media Gallery */}
                  {m.media_assets && m.media_assets.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <span className="text-[11px] font-semibold text-ink-soft">Event Media & Artifacts:</span>
                      <div className="flex flex-wrap gap-2">
                        {m.media_assets.map((asset) => (
                          <a
                            key={asset.id}
                            href={asset.delivery_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="group/img relative block overflow-hidden rounded-xl border border-line bg-paper-warm hover:border-teal transition shadow-2xs"
                            title={asset.alt_text || "Event photo"}
                          >
                            <img
                              src={asset.thumbnail_url || asset.optimized_url || asset.delivery_url}
                              alt={asset.alt_text || "Event photo"}
                              className="h-16 w-24 object-cover group-hover/img:scale-105 transition duration-200"
                            />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Upload photo widget for this memory */}
                  <div className="pt-2 border-t border-line/60">
                    <MediaUploadWidget
                      purpose="event_memory"
                      institutionId={effectiveInstId}
                      eventMemoryId={m.id}
                      label="Attach Photo"
                      helperText="Attach event photo or retrospective evidence"
                      compact
                      canDelete={false}
                      onUploadSuccess={() => refreshData()}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* SUB-TAB 4: TASKS */}
      {/* ------------------------------------------------------------------ */}
      {subTab === "tasks" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-xl font-semibold">Institutional Follow-Up Tasks</h2>
              <p className="text-xs text-ink-soft">
                Action items created from handover transitions or matched mentorship commitments.
              </p>
            </div>
            <button
              onClick={() => setIsCreatingTask(!isCreatingTask)}
              className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition"
            >
              {isCreatingTask ? "Cancel" : "+ Add Task"}
            </button>
          </div>

          {isCreatingTask && (
            <form onSubmit={handleCreateTask} className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
              <h3 className="font-semibold text-sm">Assign Follow-Up Task</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Task Title *</label>
                  <input
                    type="text"
                    required
                    value={taskTitle}
                    onChange={(e) => setTaskTitle(e.target.value)}
                    placeholder="e.g. Schedule mock interview session with Alice"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Priority</label>
                  <select
                    value={taskPriority}
                    onChange={(e) => setTaskPriority(e.target.value as "low" | "medium" | "high")}
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-soft mb-1">Description</label>
                <textarea
                  rows={2}
                  value={taskDesc}
                  onChange={(e) => setTaskDesc(e.target.value)}
                  placeholder="Task context, instructions, or deliverables..."
                  className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="rounded-lg bg-ink px-5 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition disabled:opacity-50"
              >
                {isLoading ? "Saving..." : "Create Task"}
              </button>
            </form>
          )}

          {tasks.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line p-8 text-center text-sm text-ink-soft">
              No pending tasks assigned to you in this institution.
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((t) => (
                <div
                  key={t.id}
                  className={`rounded-2xl border border-line p-4 shadow-sm flex items-center justify-between gap-4 transition ${
                    t.is_completed ? "bg-paper-warm opacity-60" : "bg-paper"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={t.is_completed}
                      disabled={t.is_completed}
                      onChange={() => handleCompleteTask(t.id)}
                      className="mt-1 h-4 w-4 rounded border-line text-ink focus:ring-ink"
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-semibold ${t.is_completed ? "line-through text-ink-soft" : ""}`}>
                          {t.title}
                        </span>
                        <span
                          className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                            t.priority === "high"
                              ? "bg-rose-100 text-rose-800"
                              : t.priority === "medium"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-zinc-100 text-zinc-600"
                          }`}
                        >
                          {t.priority}
                        </span>
                        <span className="rounded bg-paper-warm px-1.5 py-0.5 text-[9px] font-medium text-ink-soft uppercase">
                          Source: {t.source}
                        </span>
                      </div>
                      {t.description && <p className="text-xs text-ink-soft mt-1">{t.description}</p>}
                    </div>
                  </div>

                  {!t.is_completed && (
                    <button
                      onClick={() => handleCompleteTask(t.id)}
                      className="rounded-lg border border-line px-3 py-1.5 text-xs font-medium text-ink hover:bg-paper-warm transition shrink-0"
                    >
                      Mark Done
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
