import { useEffect, useMemo, useState } from "react";
import {
  createHelpOffer,
  fetchHelpOffers,
  fetchMyHelpOffers,
  requestHelpOffer,
  updateHelpOfferStatus,
} from "../services/helpOfferService";
import type { UserProfile } from "../types/auth";
import type {
  HelpOffer,
  HelpOfferAudience,
  HelpOfferDeliveryMode,
  HelpOfferStatus,
} from "../types/helpOffer";

interface HelpOffersPanelProps {
  currentUser: UserProfile | null;
  onOpenAuth: () => void;
}

export function HelpOffersPanel({
  currentUser,
  onOpenAuth,
}: HelpOffersPanelProps) {
  const activeMemberships = useMemo(
    () => currentUser?.memberships.filter((m) => m.status === "active") || [],
    [currentUser]
  );

  const [selectedInstId, setSelectedInstId] = useState<string>("");
  const effectiveInstId = selectedInstId || activeMemberships[0]?.institution_id || "";

  const [activeTab, setActiveTab] = useState<"browse" | "manage">("browse");

  // Browse state
  const [browseCategory, setBrowseCategory] = useState<string>("");
  const [searchInput, setSearchInput] = useState<string>("");
  const [submittedQuery, setSubmittedQuery] = useState<string>("");
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [offers, setOffers] = useState<HelpOffer[]>([]);
  const [browseLoading, setBrowseLoading] = useState(false);
  const [browseError, setBrowseError] = useState<string | null>(null);

  // Manage state
  const [myOffers, setMyOffers] = useState<HelpOffer[]>([]);
  const [manageLoading, setManageLoading] = useState(false);
  const [manageError, setManageError] = useState<string | null>(null);
  const [refreshCount, setRefreshCount] = useState(0);

  // New offer form
  const [newTitle, setNewTitle] = useState("");
  const [newCategory, setNewCategory] = useState("Portfolio Reviews");
  const [newDescription, setNewDescription] = useState("");
  const [newTopics, setNewTopics] = useState("");
  const [newAudience, setNewAudience] = useState<HelpOfferAudience>("all_students");
  const [newDelivery, setNewDelivery] = useState<HelpOfferDeliveryMode>("virtual");
  const [newCapacity, setNewCapacity] = useState(5);
  const [creating, setCreating] = useState(false);
  const [createSuccess, setCreateSuccess] = useState<string | null>(null);

  // Request help modal state
  const [requestingOffer, setRequestingOffer] = useState<HelpOffer | null>(null);
  const [requestMessage, setRequestMessage] = useState("");
  const [submittingRequest, setSubmittingRequest] = useState(false);
  const [requestSuccess, setRequestSuccess] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);

  useEffect(() => {
    if (!currentUser || !effectiveInstId) return;
    let isMounted = true;

    if (activeTab === "browse") {
      fetchHelpOffers(effectiveInstId, {
        category: browseCategory || undefined,
        query: submittedQuery.trim() || undefined,
      })
        .then((res) => {
          if (!isMounted) return;
          setOffers(res.items);
          setAvailableCategories(res.categories);
          setBrowseError(null);
          setBrowseLoading(false);
        })
        .catch((err: unknown) => {
          if (!isMounted) return;
          if (err instanceof Error) setBrowseError(err.message);
          setBrowseLoading(false);
        });
    } else {
      fetchMyHelpOffers(effectiveInstId)
        .then((data) => {
          if (!isMounted) return;
          setMyOffers(data);
          setManageError(null);
          setManageLoading(false);
        })
        .catch((err: unknown) => {
          if (!isMounted) return;
          if (err instanceof Error) setManageError(err.message);
          setManageLoading(false);
        });
    }

    return () => {
      isMounted = false;
    };
  }, [currentUser, effectiveInstId, activeTab, browseCategory, submittedQuery, refreshCount]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setBrowseLoading(true);
    setSubmittedQuery(searchInput);
  };

  const handleCreateOffer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId) return;
    setCreating(true);
    setCreateSuccess(null);
    setManageError(null);

    try {
      await createHelpOffer(effectiveInstId, {
        title: newTitle.trim(),
        category: newCategory.trim(),
        description: newDescription.trim(),
        topics: newTopics.split(",").map((t) => t.trim()).filter(Boolean),
        target_audience: newAudience,
        delivery_mode: newDelivery,
        capacity_per_month: Number(newCapacity) || 5,
        status: "active",
      });

      setCreateSuccess("Help offer published successfully to your college community!");
      setNewTitle("");
      setNewDescription("");
      setNewTopics("");
      setRefreshCount((c) => c + 1);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to publish offer.";
      setManageError(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleStatusChange = async (offerId: string, status: HelpOfferStatus) => {
    if (!effectiveInstId) return;
    try {
      await updateHelpOfferStatus(effectiveInstId, offerId, status);
      setRefreshCount((c) => c + 1);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update offer status.";
      setManageError(msg);
    }
  };

  const handleSendRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId || !requestingOffer) return;
    setSubmittingRequest(true);
    setRequestError(null);
    setRequestSuccess(null);

    try {
      await requestHelpOffer(effectiveInstId, requestingOffer.id, requestMessage.trim());
      setRequestSuccess("Your guidance request has been sent to the mentor!");
      setRequestMessage("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to send request.";
      setRequestError(msg);
    } finally {
      setSubmittingRequest(false);
    }
  };

  if (!currentUser) {
    return (
      <div className="rounded-2xl border border-line bg-paper p-8 text-center">
        <h3 className="font-display text-lg font-semibold text-ink">Campus Help & Mentorship</h3>
        <p className="mt-2 text-sm text-ink-soft">
          Sign in and join your college workspace to browse available help offers from alumni and senior peers.
        </p>
        <button
          onClick={onOpenAuth}
          className="mt-4 rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft"
        >
          Sign In to Access Help Offers
        </button>
      </div>
    );
  }

  if (activeMemberships.length === 0) {
    return (
      <div className="rounded-2xl border border-line bg-paper p-8 text-center">
        <h3 className="font-display text-lg font-semibold text-ink">No Active College Memberships</h3>
        <p className="mt-2 text-sm text-ink-soft">
          You are authenticated, but not yet an active member of any college workspace.
        </p>
        <p className="mt-1 text-xs text-ink-soft">
          Join your campus workspace to explore or publish college help offers.
        </p>
      </div>
    );
  }

  const currentInst = activeMemberships.find((m) => m.institution_id === effectiveInstId);

  return (
    <div className="space-y-6">
      {/* Top Header & Workspace / Tab switcher */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-line pb-4">
        <div className="flex flex-wrap items-center gap-3">
          {activeMemberships.length > 1 ? (
            <select
              value={effectiveInstId}
              onChange={(e) => {
                setBrowseLoading(true);
                setManageLoading(true);
                setSelectedInstId(e.target.value);
              }}
              className="rounded-xl border border-line bg-paper px-3 py-1.5 text-xs font-semibold text-ink"
            >
              {activeMemberships.map((m) => (
                <option key={m.institution_id} value={m.institution_id}>
                  {m.institution_name || m.institution_slug || "College Workspace"}
                </option>
              ))}
            </select>
          ) : (
            <div className="flex items-center gap-1.5 rounded-xl border border-line bg-paper-warm px-3 py-1.5 text-xs font-semibold text-ink">
              <svg className="h-3.5 w-3.5 text-teal shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span>{currentInst?.institution_name || currentInst?.institution_slug || "College Workspace"}</span>
            </div>
          )}

          <div className="flex items-center gap-1 rounded-xl bg-paper-warm p-1 text-xs font-semibold">
            <button
              onClick={() => {
                setBrowseLoading(true);
                setActiveTab("browse");
              }}
              className={`rounded-lg px-3 py-1.5 transition ${
                activeTab === "browse" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
              }`}
            >
              Browse Active Offers
            </button>
            <button
              onClick={() => {
                setManageLoading(true);
                setActiveTab("manage");
              }}
              className={`rounded-lg px-3 py-1.5 transition ${
                activeTab === "manage" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
              }`}
            >
              My Published Offers ({myOffers.length})
            </button>
          </div>
        </div>
      </div>

      {activeTab === "browse" ? (
        <div className="space-y-6">
          {/* Search and Dynamic Category Filter */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <form onSubmit={handleSearchSubmit} className="flex flex-1 max-w-md gap-2">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search offers by title, skill, or keyword..."
                className="w-full rounded-xl border border-line bg-paper px-3 py-1.5 text-xs text-ink placeholder:text-ink-soft focus:outline-none focus:ring-1 focus:ring-ink"
              />
              <button
                type="submit"
                className="rounded-xl bg-ink px-3 py-1.5 text-xs font-semibold text-paper hover:bg-ink-soft"
              >
                Search
              </button>
            </form>

            {availableCategories.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5">
                <button
                  onClick={() => {
                    setBrowseLoading(true);
                    setBrowseCategory("");
                  }}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium transition ${
                    browseCategory === ""
                      ? "bg-ink text-paper"
                      : "bg-paper-warm text-ink-soft hover:text-ink"
                  }`}
                >
                  All Categories
                </button>
                {availableCategories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => {
                      setBrowseLoading(true);
                      setBrowseCategory(cat);
                    }}
                    className={`rounded-lg px-2.5 py-1 text-xs font-medium transition ${
                      browseCategory === cat
                        ? "bg-ink text-paper"
                        : "bg-paper-warm text-ink-soft hover:text-ink"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            )}
          </div>

          {browseError && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
              Failed to load help offers: {browseError}
            </div>
          )}

          {browseLoading ? (
            <div className="py-16 text-center text-sm text-ink-soft">
              Searching active campus help offers...
            </div>
          ) : offers.length === 0 ? (
            <div className="rounded-2xl border border-line bg-paper p-10 text-center">
              <h4 className="font-display text-base font-semibold text-ink">No Active Offers Found</h4>
              <p className="mt-1 text-xs text-ink-soft">
                {submittedQuery || browseCategory
                  ? "No active help offers matched your search criteria."
                  : "No active help offers published in this college workspace yet. Be the first to share your expertise!"}
              </p>
              <button
                onClick={() => {
                  setManageLoading(true);
                  setActiveTab("manage");
                }}
                className="mt-4 rounded-xl border border-line px-3 py-1.5 text-xs font-semibold text-ink hover:bg-paper-warm"
              >
                + Publish a Help Offer
              </button>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {offers.map((offer) => {
                const isOwnOffer = offer.user_id === currentUser.user.id;

                return (
                  <div
                    key={offer.id}
                    className="flex flex-col justify-between rounded-2xl border border-line bg-paper p-5 shadow-sm transition hover:shadow-md"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <span className="rounded-md bg-paper-warm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-ink-soft">
                          {offer.category}
                        </span>
                        <span className="rounded-md bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[10px] font-medium text-emerald-800">
                          {offer.delivery_mode.replace("_", " ")}
                        </span>
                      </div>

                      <h4 className="mt-2 font-display text-base font-semibold text-ink leading-snug">
                        {offer.title}
                      </h4>

                      <div className="mt-1 text-xs text-ink-soft">
                        Offered by <span className="font-medium text-ink">{offer.creator_name || "Community Member"}</span>
                        {offer.creator_role && ` (${offer.creator_role})`}
                      </div>

                      <p className="mt-3 text-xs text-ink leading-relaxed line-clamp-3">
                        {offer.description}
                      </p>

                      {offer.topics && offer.topics.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1">
                          {offer.topics.map((t, idx) => (
                            <span
                              key={idx}
                              className="rounded bg-paper-warm px-1.5 py-0.5 text-[10px] text-ink-soft"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="mt-3 text-[11px] text-ink-soft flex items-center justify-between border-t border-line/60 pt-2">
                        <span>Audience: {offer.target_audience.replace("_", " ")}</span>
                        <span>Capacity: ~{offer.capacity_per_month}/mo</span>
                      </div>
                    </div>

                    <div className="mt-4 border-t border-line pt-3">
                      {isOwnOffer ? (
                        <div className="text-center text-xs italic text-ink-soft">
                          (Your own published offer)
                        </div>
                      ) : (
                        <button
                          onClick={() => {
                            setRequestingOffer(offer);
                            setRequestSuccess(null);
                            setRequestError(null);
                          }}
                          className="w-full rounded-xl bg-ink py-2 text-center text-xs font-semibold text-paper hover:bg-ink-soft transition"
                        >
                          Request Help
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        /* Manage My Offers */
        <div className="space-y-8">
          {/* Create New Offer Form */}
          <div className="rounded-2xl border border-line bg-paper p-6 shadow-sm">
            <h3 className="font-display text-lg font-semibold text-ink">Publish a Help Offer</h3>
            <p className="mt-1 text-xs text-ink-soft">
              Declare specific assistance you are willing to provide to fellow members in this college workspace.
            </p>

            {createSuccess && (
              <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700">
                {createSuccess}
              </div>
            )}

            {manageError && (
              <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                {manageError}
              </div>
            )}

            <form onSubmit={handleCreateOffer} className="mt-4 space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Offer Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. Portfolio Reviews for ML Projects"
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Assistance Category *
                  </label>
                  <input
                    type="text"
                    required
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    placeholder="e.g. Portfolio Reviews, Mock Interviews, Resume Feedback"
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                  <div className="mt-1 flex flex-wrap gap-1 text-[10px] text-ink-soft">
                    <span>Quick:</span>
                    {["Portfolio Reviews", "Mock Interviews", "Resume Feedback", "Career Guidance", "Technical Mentoring"].map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => setNewCategory(q)}
                        className="underline hover:text-ink"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink-soft mb-1">
                  Description *
                </label>
                <textarea
                  required
                  rows={3}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Explain what kind of guidance you will provide, what students should prepare, and format..."
                  className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                />
              </div>

              <div className="grid sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Relevant Skills / Topics (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={newTopics}
                    onChange={(e) => setNewTopics(e.target.value)}
                    placeholder="PyTorch, System Design, Hackathons"
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Target Audience
                  </label>
                  <select
                    value={newAudience}
                    onChange={(e) => setNewAudience(e.target.value as HelpOfferAudience)}
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  >
                    <option value="all_students">All Students</option>
                    <option value="undergrads">Undergraduates</option>
                    <option value="seniors">Seniors / Final Year</option>
                    <option value="alumni_peers">Alumni Peers</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Delivery Mode
                  </label>
                  <select
                    value={newDelivery}
                    onChange={(e) => setNewDelivery(e.target.value as HelpOfferDeliveryMode)}
                    className="w-full rounded-xl border border-line px-3 py-2 text-sm"
                  >
                    <option value="virtual">Virtual (Video / Call)</option>
                    <option value="in_person">In Person (On Campus)</option>
                    <option value="async">Asynchronous (Written)</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-line pt-4">
                <div className="flex items-center gap-2">
                  <label className="text-xs font-semibold text-ink-soft">Monthly Capacity Limit:</label>
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={newCapacity}
                    onChange={(e) => setNewCapacity(Number(e.target.value))}
                    className="w-20 rounded-xl border border-line px-2 py-1 text-sm text-center"
                  />
                </div>
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft disabled:opacity-50"
                >
                  {creating ? "Publishing..." : "Publish Help Offer"}
                </button>
              </div>
            </form>
          </div>

          {/* List of User's Offers */}
          <div>
            <h3 className="font-display text-base font-semibold text-ink mb-3">
              Your Published Offers in this College
            </h3>

            {manageLoading ? (
              <div className="py-8 text-center text-sm text-ink-soft">Loading your offers...</div>
            ) : myOffers.length === 0 ? (
              <div className="rounded-2xl border border-line bg-paper p-8 text-center text-xs text-ink-soft">
                You haven&apos;t created any help offers in this college workspace yet.
              </div>
            ) : (
              <div className="space-y-3">
                {myOffers.map((offer) => {
                  const statusColors: Record<HelpOfferStatus, string> = {
                    active: "bg-emerald-50 text-emerald-700 border-emerald-200",
                    paused: "bg-amber-50 text-amber-700 border-amber-200",
                    draft: "bg-paper-warm text-ink-soft border-line",
                    archived: "bg-rose-50 text-rose-700 border-rose-200",
                  };

                  return (
                    <div
                      key={offer.id}
                      className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-xl border border-line bg-paper p-4"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-sm text-ink">{offer.title}</h4>
                          <span
                            className={`rounded border px-2 py-0.5 text-[10px] font-semibold uppercase ${
                              statusColors[offer.status]
                            }`}
                          >
                            {offer.status}
                          </span>
                          <span className="text-xs text-ink-soft">• {offer.category}</span>
                        </div>
                        <p className="mt-1 text-xs text-ink-soft line-clamp-1">{offer.description}</p>
                      </div>

                      <div className="flex items-center gap-2">
                        {offer.status === "active" ? (
                          <button
                            onClick={() => handleStatusChange(offer.id, "paused")}
                            className="rounded-lg border border-line bg-paper px-3 py-1 text-xs font-medium text-ink hover:bg-paper-warm"
                          >
                            Pause Offer
                          </button>
                        ) : offer.status === "paused" ? (
                          <button
                            onClick={() => handleStatusChange(offer.id, "active")}
                            className="rounded-lg bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700"
                          >
                            Resume Active
                          </button>
                        ) : null}

                        {offer.status !== "archived" && (
                          <button
                            onClick={() => handleStatusChange(offer.id, "archived")}
                            className="rounded-lg border border-rose-200 px-3 py-1 text-xs font-medium text-rose-700 hover:bg-rose-50"
                          >
                            Archive
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Purpose-specific Help Request Modal */}
      {requestingOffer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
          <div className="relative w-full max-w-lg rounded-2xl bg-paper p-6 shadow-xl border border-line">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h3 className="font-display text-base font-semibold text-ink">
                  Request Help: {requestingOffer.title}
                </h3>
                <p className="text-xs text-ink-soft">
                  Mentor: {requestingOffer.creator_name || "Community Member"}
                </p>
              </div>
              <button
                onClick={() => setRequestingOffer(null)}
                aria-label="Close"
                className="rounded-lg p-1.5 text-ink-soft hover:bg-paper-warm hover:text-ink"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {requestSuccess ? (
              <div className="mt-4 space-y-4">
                <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-medium text-emerald-800">
                  <svg className="h-4 w-4 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{requestSuccess}</span>
                </div>
                <div className="text-right">
                  <button
                    onClick={() => setRequestingOffer(null)}
                    className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSendRequest} className="mt-4 space-y-4">
                {requestError && (
                  <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                    {requestError}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-ink mb-1">
                    Introductory Purpose Message *
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={requestMessage}
                    onChange={(e) => setRequestMessage(e.target.value)}
                    placeholder="Introduce yourself, explain what specific guidance or review you need, and any relevant links..."
                    className="w-full rounded-xl border border-line px-3 py-2 text-xs"
                  />
                  <div className="mt-1 text-[11px] text-ink-soft">
                    Tip: Be concrete about your goal (e.g. &apos;I am submitting my machine learning project to HackShift and would appreciate feedback on system architecture&apos;).
                  </div>
                </div>

                <div className="flex justify-end gap-2 border-t border-line pt-3">
                  <button
                    type="button"
                    onClick={() => setRequestingOffer(null)}
                    className="rounded-xl border border-line px-3 py-1.5 text-xs font-semibold text-ink hover:bg-paper-warm"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingRequest || requestMessage.trim().length < 5}
                    className="rounded-xl bg-ink px-4 py-1.5 text-xs font-semibold text-paper hover:bg-ink-soft disabled:opacity-50"
                  >
                    {submittingRequest ? "Sending Request..." : "Send Request"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
