import { useCallback, useEffect, useMemo, useState } from "react";
import {
  commitAlumniImport,
  createCampaign,
  createPartner,
  createSponsorship,
  fetchAlumniImportJobs,
  fetchCampaigns,
  fetchPartners,
  fetchPilotMetrics,
  fetchPricingPackages,
  fetchPromotedFeed,
  fetchSponsorships,
  previewAlumniImport,
  reviewCampaign,
  updateSponsorshipStatus,
} from "../services/phase8Service";
import type { UserProfile } from "../types/auth";
import type {
  AlumniImportJob,
  AlumniImportPreviewResponse,
  FeedPromotionItem,
  PartnerOrganization,
  PilotMetrics,
  PricingPackage,
  PromotionCampaign,
  SponsorshipRequest,
  SponsorshipStatus,
  SupportType,
} from "../types/phase8";

interface InstitutionOption {
  id: string;
  name: string;
  slug: string;
}

interface PartnershipsPromotionPanelProps {
  currentUser: UserProfile | null;
  onOpenAuth: () => void;
}

type SubTab = "sponsorships" | "campaigns" | "import" | "metrics";

function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof Error) return err.message;
  return fallback;
}

export function PartnershipsPromotionPanel({
  currentUser,
  onOpenAuth,
}: PartnershipsPromotionPanelProps) {
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

  const [subTab, setSubTab] = useState<SubTab>("sponsorships");
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(
    null
  );
  const [refreshKey, setRefreshKey] = useState(0);
  const refreshData = useCallback(() => setRefreshKey((k) => k + 1), []);

  // Sponsorship State
  const [sponsorships, setSponsorships] = useState<SponsorshipRequest[]>([]);
  const [partners, setPartners] = useState<PartnerOrganization[]>([]);
  const [isCreatingSponsorship, setIsCreatingSponsorship] = useState(false);
  const [isCreatingPartner, setIsCreatingPartner] = useState(false);
  const [sponObjective, setSponObjective] = useState("");
  const [sponBenefits, setSponBenefits] = useState("");
  const [sponSupportType, setSponSupportType] = useState<SupportType>("financial");
  const [sponAudience, setSponAudience] = useState("");
  const [sponBudget, setSponBudget] = useState<string>("");
  const [sponCurrency, setSponCurrency] = useState("USD");
  const [sponEmail, setSponEmail] = useState("");
  const [sponPartnerId, setSponPartnerId] = useState("");

  // Partner Form State
  const [partnerName, setPartnerName] = useState("");
  const [partnerIndustry, setPartnerIndustry] = useState("");
  const [partnerContact, setPartnerContact] = useState("");
  const [partnerEmail, setPartnerEmail] = useState("");
  const [partnerWebsite, setPartnerWebsite] = useState("");

  // Campaigns State
  const [pricingPackages, setPricingPackages] = useState<PricingPackage[]>([]);
  const [campaigns, setCampaigns] = useState<PromotionCampaign[]>([]);
  const [promotedFeed, setPromotedFeed] = useState<FeedPromotionItem[]>([]);
  const [isCreatingCampaign, setIsCreatingCampaign] = useState(false);
  const [campOppId, setCampOppId] = useState("");
  const [campTargetInsts, setCampTargetInsts] = useState("");
  const [campPackage, setCampPackage] = useState("standard_cross_college");
  const [campDays, setCampDays] = useState(7);

  // Import State
  const [csvText, setCsvText] = useState("");
  const [csvFilename, setCsvFilename] = useState("alumni_directory.csv");
  const [importPreview, setImportPreview] = useState<AlumniImportPreviewResponse | null>(null);
  const [importJobs, setImportJobs] = useState<AlumniImportJob[]>([]);

  // Pilot Metrics State
  const [metrics, setMetrics] = useState<PilotMetrics | null>(null);

  // Data Loading Effect
  useEffect(() => {
    if (!effectiveInstId || !currentUser) return;
    let isMounted = true;

    async function loadData() {
      try {
        if (subTab === "sponsorships") {
          const [sponList, partnerList] = await Promise.all([
            fetchSponsorships(effectiveInstId),
            fetchPartners(effectiveInstId),
          ]);
          if (!isMounted) return;
          setSponsorships(sponList);
          setPartners(partnerList);
        } else if (subTab === "campaigns") {
          const [pkgs, campList, feed] = await Promise.all([
            fetchPricingPackages(),
            fetchCampaigns(effectiveInstId),
            fetchPromotedFeed(effectiveInstId),
          ]);
          if (!isMounted) return;
          setPricingPackages(pkgs);
          setCampaigns(campList);
          setPromotedFeed(feed);
        } else if (subTab === "import") {
          const jobs = await fetchAlumniImportJobs(effectiveInstId);
          if (isMounted) setImportJobs(jobs);
        } else if (subTab === "metrics") {
          const data = await fetchPilotMetrics(effectiveInstId);
          if (isMounted) setMetrics(data);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setFeedback({
            type: "error",
            message: getErrorMessage(err, "Failed to load partnerships data"),
          });
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

  // Sponsorship Handlers
  const handleCreatePartner = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId) return;
    setIsLoading(true);
    try {
      const payload: Parameters<typeof createPartner>[1] = {
        name: partnerName.trim(),
      };
      if (partnerIndustry.trim()) payload.industry = partnerIndustry.trim();
      if (partnerContact.trim()) payload.contact_name = partnerContact.trim();
      if (partnerEmail.trim()) payload.contact_email = partnerEmail.trim();
      if (partnerWebsite.trim()) payload.website_url = partnerWebsite.trim();

      await createPartner(effectiveInstId, payload);
      setFeedback({ type: "success", message: `Partner organization '${partnerName}' added.` });
      setIsCreatingPartner(false);
      setPartnerName("");
      setPartnerIndustry("");
      setPartnerContact("");
      setPartnerEmail("");
      setPartnerWebsite("");
      refreshData();
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "Could not register partner.") });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateSponsorship = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId) return;
    setIsLoading(true);
    try {
      const payload: Parameters<typeof createSponsorship>[1] = {
        objective: sponObjective.trim(),
        proposed_benefits: sponBenefits.trim(),
        support_type: sponSupportType,
        budget_currency: sponCurrency,
      };
      if (sponAudience.trim()) payload.intended_audience = sponAudience.trim();
      if (sponBudget.trim()) payload.budget_amount = parseFloat(sponBudget);
      if (sponEmail.trim()) payload.contact_email = sponEmail.trim();
      if (sponPartnerId) payload.partner_organization_id = sponPartnerId;

      await createSponsorship(effectiveInstId, payload);
      setFeedback({ type: "success", message: "Sponsorship prospectus created successfully!" });
      setIsCreatingSponsorship(false);
      setSponObjective("");
      setSponBenefits("");
      setSponAudience("");
      setSponBudget("");
      setSponEmail("");
      setSponPartnerId("");
      refreshData();
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message: getErrorMessage(err, "Could not create sponsorship request."),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateSponsorshipStatus = async (
    requestId: string,
    status: SponsorshipStatus,
    note?: string
  ) => {
    if (!effectiveInstId) return;
    try {
      await updateSponsorshipStatus(
        effectiveInstId,
        requestId,
        status,
        note ? { notes: note } : undefined
      );
      setFeedback({ type: "success", message: `Sponsorship transitioned to ${status}.` });
      refreshData();
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message: getErrorMessage(err, "Status transition rejected."),
      });
    }
  };

  // Campaign Handlers
  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId) return;
    setIsLoading(true);
    try {
      const now = new Date();
      const end = new Date(now.getTime() + campDays * 24 * 60 * 60 * 1000);
      const targetIds = campTargetInsts
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      if (targetIds.length === 0) {
        throw new Error("Please specify at least one target institution ID.");
      }

      await createCampaign(effectiveInstId, {
        opportunity_id: campOppId,
        target_institution_ids: targetIds,
        pricing_package: campPackage,
        start_date: now.toISOString(),
        end_date: end.toISOString(),
      });
      setFeedback({
        type: "success",
        message: "Cross-college campaign requested! Pending review.",
      });
      setIsCreatingCampaign(false);
      setCampOppId("");
      setCampTargetInsts("");
      refreshData();
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message: getErrorMessage(err, "Could not create campaign."),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReviewCampaign = async (campaignId: string, action: "approve" | "reject") => {
    if (!effectiveInstId) return;
    try {
      await reviewCampaign(effectiveInstId, campaignId, action);
      setFeedback({ type: "success", message: `Campaign ${action}d.` });
      refreshData();
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message: getErrorMessage(err, "Campaign review action failed."),
      });
    }
  };

  // CSV Import Handlers
  const handlePreviewImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveInstId) return;
    setIsLoading(true);
    try {
      const preview = await previewAlumniImport(effectiveInstId, csvFilename, csvText);
      setImportPreview(preview);
      setFeedback({
        type: "success",
        message: `Validation complete: ${preview.valid_rows} valid rows, ${preview.duplicate_rows} duplicates, ${preview.invalid_rows} invalid.`,
      });
    } catch (err: unknown) {
      setFeedback({ type: "error", message: getErrorMessage(err, "CSV dry-run failed.") });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCommitImport = async () => {
    if (!effectiveInstId) return;
    setIsLoading(true);
    try {
      const job = await commitAlumniImport(effectiveInstId, csvFilename, csvText);
      setFeedback({
        type: "success",
        message: `Import committed! ${job.accepted_rows} alumni records added with private visibility and zero default consent.`,
      });
      setImportPreview(null);
      setCsvText("");
      refreshData();
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message: getErrorMessage(err, "Failed to commit alumni import."),
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!currentUser) {
    return (
      <div className="rounded-2xl border border-line bg-paper-warm p-8 text-center sm:p-12">
        <h3 className="font-display text-2xl font-semibold">Sign in to Access Partnerships & Promotion</h3>
        <p className="mx-auto mt-2 max-w-md text-sm text-ink-soft">
          EventSignal Partnerships, Cross-College Promotion, and Pilot Analytics are institution-scoped.
          Please sign in to manage sponsors and multi-campus campaigns.
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
      {/* College Workspace Selector */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-line bg-paper p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <label htmlFor="p8-inst-select" className="text-xs font-semibold uppercase tracking-wider text-ink-soft">
            College Workspace:
          </label>
          <select
            id="p8-inst-select"
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
            onClick={() => setSubTab("sponsorships")}
            className={`rounded-lg px-3 py-1.5 transition ${
              subTab === "sponsorships" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
            }`}
          >
            Sponsorships ({sponsorships.length})
          </button>
          <button
            onClick={() => setSubTab("campaigns")}
            className={`rounded-lg px-3 py-1.5 transition ${
              subTab === "campaigns" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
            }`}
          >
            Cross-College Promotion ({campaigns.length})
          </button>
          <button
            onClick={() => setSubTab("import")}
            className={`rounded-lg px-3 py-1.5 transition ${
              subTab === "import" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
            }`}
          >
            Alumni CSV Import
          </button>
          <button
            onClick={() => setSubTab("metrics")}
            className={`rounded-lg px-3 py-1.5 transition ${
              subTab === "metrics" ? "bg-paper text-ink shadow-sm" : "text-ink-soft hover:text-ink"
            }`}
          >
            Pilot Analytics
          </button>
        </div>
      </div>

      {/* Global Feedback Alert */}
      {feedback && (
        <div
          className={`flex items-center justify-between rounded-xl p-4 text-sm font-medium ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-900 border border-emerald-200"
              : "bg-rose-50 text-rose-900 border border-rose-200"
          }`}
        >
          <span>{feedback.message}</span>
          <div className="flex items-center gap-2">
            {feedback.type === "error" && (
              <button
                type="button"
                onClick={refreshData}
                className="rounded-lg bg-rose-700 px-2.5 py-1 text-xs font-semibold text-white hover:bg-rose-800"
              >
                Retry
              </button>
            )}
            <button onClick={() => setFeedback(null)} className="ml-2 text-xs font-bold uppercase hover:opacity-75">
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 1: SPONSORSHIPS & PARTNERS */}
      {/* ==================================================================== */}
      {subTab === "sponsorships" && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="font-display text-xl font-bold">Event Sponsorship Facilitation</h2>
              <p className="text-xs text-ink-soft mt-0.5">
                Declare sponsorship needs for campus events and track commercial relationships honestly.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsCreatingPartner(!isCreatingPartner)}
                className="rounded-xl border border-line bg-paper px-4 py-2 text-xs font-semibold text-ink hover:bg-paper-warm transition"
              >
                {isCreatingPartner ? "Close Partner Form" : "+ Add Partner Brand"}
              </button>
              <button
                onClick={() => setIsCreatingSponsorship(!isCreatingSponsorship)}
                className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition"
              >
                {isCreatingSponsorship ? "Close Form" : "+ Create Prospectus"}
              </button>
            </div>
          </div>

          {/* Create Partner Form */}
          {isCreatingPartner && (
            <form onSubmit={handleCreatePartner} className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
              <h3 className="font-semibold text-sm">Register Partner Organization / Brand</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Company / Brand Name *</label>
                  <input
                    type="text"
                    required
                    value={partnerName}
                    onChange={(e) => setPartnerName(e.target.value)}
                    placeholder="e.g. Acme Tech Innovations"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Industry</label>
                  <input
                    type="text"
                    value={partnerIndustry}
                    onChange={(e) => setPartnerIndustry(e.target.value)}
                    placeholder="e.g. Artificial Intelligence, Cloud"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Representative Name</label>
                  <input
                    type="text"
                    value={partnerContact}
                    onChange={(e) => setPartnerContact(e.target.value)}
                    placeholder="e.g. Jane Doe"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Contact Email</label>
                  <input
                    type="email"
                    value={partnerEmail}
                    onChange={(e) => setPartnerEmail(e.target.value)}
                    placeholder="e.g. partner@acme.com"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreatingPartner(false)}
                  className="rounded-lg border border-line px-4 py-2 text-xs font-semibold text-ink-soft hover:bg-paper-warm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="rounded-lg bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft disabled:opacity-50"
                >
                  {isLoading ? "Saving..." : "Save Partner"}
                </button>
              </div>
            </form>
          )}

          {/* Create Sponsorship Form */}
          {isCreatingSponsorship && (
            <form onSubmit={handleCreateSponsorship} className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
              <h3 className="font-semibold text-sm">Create Event Sponsorship Prospectus</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Sponsorship Objective *</label>
                  <input
                    type="text"
                    required
                    value={sponObjective}
                    onChange={(e) => setSponObjective(e.target.value)}
                    placeholder="e.g. Title Track Sponsor for Hackathon"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Support Type</label>
                  <select
                    value={sponSupportType}
                    onChange={(e) => setSponSupportType(e.target.value as SupportType)}
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  >
                    <option value="financial">Financial Contribution</option>
                    <option value="in_kind">In-Kind (Equipment, Software)</option>
                    <option value="mentorship">Industry Mentors</option>
                    <option value="venue">Venue Support</option>
                    <option value="swag">Swag & Prizes</option>
                    <option value="other">Other Support</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Target Partner Organization (Optional)</label>
                  <select
                    value={sponPartnerId}
                    onChange={(e) => setSponPartnerId(e.target.value)}
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  >
                    <option value="">Open Inbound Inquiry (No partner linked yet)</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.verification_status})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-ink-soft mb-1">Requested Budget</label>
                    <input
                      type="number"
                      step="any"
                      value={sponBudget}
                      onChange={(e) => setSponBudget(e.target.value)}
                      placeholder="e.g. 5000"
                      className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                    />
                  </div>
                  <div className="w-24">
                    <label className="block text-xs font-medium text-ink-soft mb-1">Currency</label>
                    <input
                      type="text"
                      maxLength={3}
                      value={sponCurrency}
                      onChange={(e) => setSponCurrency(e.target.value.toUpperCase())}
                      className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                    />
                  </div>
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-ink-soft mb-1">Proposed Sponsor Benefits *</label>
                  <textarea
                    required
                    rows={2}
                    value={sponBenefits}
                    onChange={(e) => setSponBenefits(e.target.value)}
                    placeholder="e.g. Keynote speech slot, company booth, branded lanyard, access to participant opt-in resume book"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Intended Audience Context</label>
                  <input
                    type="text"
                    value={sponAudience}
                    onChange={(e) => setSponAudience(e.target.value)}
                    placeholder="e.g. 300 Computer Science undergraduates"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Inquiry Contact Email</label>
                  <input
                    type="email"
                    value={sponEmail}
                    onChange={(e) => setSponEmail(e.target.value)}
                    placeholder="e.g. sponsorship@college.edu"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreatingSponsorship(false)}
                  className="rounded-lg border border-line px-4 py-2 text-xs font-semibold text-ink-soft hover:bg-paper-warm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="rounded-lg bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft disabled:opacity-50"
                >
                  {isLoading ? "Saving..." : "Create Prospectus"}
                </button>
              </div>
            </form>
          )}

          {/* Sponsorship Prospectuses List */}
          {sponsorships.length === 0 ? (
            <div className="rounded-2xl border border-line bg-paper p-8 text-center text-sm text-ink-soft">
              No sponsorship requests declared yet for this college. Click &quot;+ Create Prospectus&quot; to begin.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {sponsorships.map((req) => (
                <div key={req.id} className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="inline-block rounded-md bg-paper-warm px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-ink-soft">
                        {(req.support_type || "").replace(/_/g, " ")}
                      </span>
                      <h3 className="font-semibold text-base text-ink mt-1">{req.objective}</h3>
                    </div>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${
                        req.status === "accepted"
                          ? "bg-emerald-100 text-emerald-800"
                          : req.status === "submitted"
                          ? "bg-amber-100 text-amber-800"
                          : req.status === "under_review"
                          ? "bg-sky-100 text-sky-800"
                          : req.status === "closed"
                          ? "bg-purple-100 text-purple-800"
                          : "bg-paper-warm text-ink-soft"
                      }`}
                    >
                      {(req.status || "").replace(/_/g, " ")}
                    </span>
                  </div>

                  <p className="text-xs text-ink-soft line-clamp-2">{req.proposed_benefits}</p>

                  <div className="flex items-center justify-between text-xs text-ink-soft border-t border-line pt-2">
                    <span>
                      {req.budget_amount ? `${req.budget_currency} ${req.budget_amount.toLocaleString()}` : "In-Kind / Unspecified"}
                    </span>
                    <span>Audience: {req.intended_audience || "General campus"}</span>
                  </div>

                  {/* Actions based on lifecycle */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    {req.status === "draft" && (
                      <button
                        onClick={() => handleUpdateSponsorshipStatus(req.id, "submitted")}
                        className="rounded-lg bg-ink px-2.5 py-1 text-xs font-semibold text-paper hover:bg-ink-soft"
                      >
                        Submit Inquiry
                      </button>
                    )}
                    {req.status === "submitted" && (
                      <button
                        onClick={() => handleUpdateSponsorshipStatus(req.id, "under_review")}
                        className="rounded-lg bg-sky-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-sky-700"
                      >
                        Start Review
                      </button>
                    )}
                    {req.status === "under_review" && (
                      <>
                        <button
                          onClick={() => handleUpdateSponsorshipStatus(req.id, "accepted", "Terms mutually agreed")}
                          className="rounded-lg bg-emerald-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-emerald-700"
                        >
                          Accept Agreement
                        </button>
                        <button
                          onClick={() => handleUpdateSponsorshipStatus(req.id, "declined")}
                          className="rounded-lg border border-line px-2.5 py-1 text-xs font-semibold text-ink-soft hover:bg-paper-warm"
                        >
                          Decline
                        </button>
                      </>
                    )}
                    {req.status === "accepted" && (
                      <button
                        onClick={() => handleUpdateSponsorshipStatus(req.id, "closed")}
                        className="rounded-lg border border-line px-2.5 py-1 text-xs font-semibold text-ink-soft hover:bg-paper-warm"
                      >
                        Mark Concluded
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 2: CROSS-COLLEGE PROMOTION */}
      {/* ==================================================================== */}
      {subTab === "campaigns" && (
        <div className="space-y-8">
          <div>
            <h2 className="font-display text-xl font-bold">Cross-College Event Promotion</h2>
            <p className="text-xs text-ink-soft mt-0.5">
              Promote your campus opportunities to student feeds at partner institutions with transparent commercial terms and conspicuous disclosure.
            </p>
          </div>

          {/* Pricing Packages Showcase */}
          <div className="grid gap-4 sm:grid-cols-3">
            {pricingPackages.map((pkg) => (
              <div key={pkg.package_id} className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-2">
                <span className="inline-block rounded-md bg-paper-warm px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-ink-soft">
                  {pkg.duration_days} Days Placement
                </span>
                <h3 className="font-semibold text-sm text-ink">{pkg.name}</h3>
                <p className="text-xs text-ink-soft">{pkg.description}</p>
                <div className="text-lg font-bold text-ink pt-1">
                  {pkg.price_amount === 0 ? "Free (Pilot Access)" : `$${pkg.price_amount.toFixed(2)} ${pkg.currency}`}
                </div>
              </div>
            ))}
          </div>

          {/* Request Campaign Action */}
          <div className="flex justify-between items-center">
            <h3 className="font-semibold text-sm">Active & Pending Promotion Campaigns</h3>
            <button
              onClick={() => setIsCreatingCampaign(!isCreatingCampaign)}
              className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition"
            >
              {isCreatingCampaign ? "Close Form" : "+ Request Cross-College Promotion"}
            </button>
          </div>

          {/* Campaign Form */}
          {isCreatingCampaign && (
            <form onSubmit={handleCreateCampaign} className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
              <h3 className="font-semibold text-sm">Create Cross-College Promotion Request</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Opportunity ID to Promote *</label>
                  <input
                    type="text"
                    required
                    value={campOppId}
                    onChange={(e) => setCampOppId(e.target.value)}
                    placeholder="UUID of opportunity"
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Target Institution IDs (Comma separated) *</label>
                  <input
                    type="text"
                    required
                    value={campTargetInsts}
                    onChange={(e) => setCampTargetInsts(e.target.value)}
                    placeholder="e.g. 8a3f..., 9b2c..."
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Pricing Package</label>
                  <select
                    value={campPackage}
                    onChange={(e) => {
                      setCampPackage(e.target.value);
                      const p = pricingPackages.find((pkg) => pkg.package_id === e.target.value);
                      if (p) setCampDays(p.duration_days);
                    }}
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  >
                    {pricingPackages.map((p) => (
                      <option key={p.package_id} value={p.package_id}>
                        {p.name} ({p.price_amount === 0 ? "Free" : `$${p.price_amount}`})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-soft mb-1">Placement Duration (Days)</label>
                  <input
                    type="number"
                    value={campDays}
                    onChange={(e) => setCampDays(parseInt(e.target.value, 10))}
                    className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreatingCampaign(false)}
                  className="rounded-lg border border-line px-4 py-2 text-xs font-semibold text-ink-soft hover:bg-paper-warm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="rounded-lg bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft disabled:opacity-50"
                >
                  {isLoading ? "Submitting..." : "Submit Campaign Request"}
                </button>
              </div>
            </form>
          )}

          {/* Campaigns List */}
          {campaigns.length === 0 ? (
            <div className="rounded-2xl border border-line bg-paper p-8 text-center text-sm text-ink-soft">
              No cross-college campaigns created yet. Click &quot;+ Request Cross-College Promotion&quot; to begin.
            </div>
          ) : (
            <div className="rounded-2xl border border-line bg-paper overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs">
                <thead className="bg-paper-warm border-b border-line text-ink-soft uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="p-3">Campaign Package</th>
                    <th className="p-3">Target Colleges</th>
                    <th className="p-3">Schedule</th>
                    <th className="p-3">Disclosure Label</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {campaigns.map((camp) => (
                    <tr key={camp.id} className="hover:bg-paper-warm/50 transition">
                      <td className="p-3 font-semibold text-ink">{camp.pricing_package.replace(/_/g, " ")}</td>
                      <td className="p-3 text-ink-soft">{camp.target_institution_ids.length} campus(es)</td>
                      <td className="p-3 text-ink-soft">
                        {new Date(camp.start_date).toLocaleDateString()} – {new Date(camp.end_date).toLocaleDateString()}
                      </td>
                      <td className="p-3">
                        <span className="inline-block rounded-md bg-amber-100 text-amber-900 font-bold px-2 py-0.5 text-[10px]">
                          {camp.sponsored_label}
                        </span>
                      </td>
                      <td className="p-3 font-semibold capitalize">{camp.status}</td>
                      <td className="p-3 text-right space-x-1">
                        {camp.status === "draft" && (
                          <button
                            onClick={() => handleReviewCampaign(camp.id, "approve")}
                            className="rounded-md bg-emerald-600 px-2 py-1 text-[11px] font-semibold text-white hover:bg-emerald-700"
                          >
                            Approve
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Live Feed Preview of Sponsored Events */}
          <div className="space-y-4">
            <h3 className="font-semibold text-sm">Sponsored Opportunities Feed on this Campus</h3>
            {promotedFeed.length === 0 ? (
              <div className="rounded-2xl border border-line bg-paper p-6 text-center text-xs text-ink-soft">
                No active cross-college sponsored campaigns are currently targeting this workspace.
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {promotedFeed.map((item) => (
                  <div key={item.campaign_id} className="rounded-2xl border border-amber-200 bg-amber-50/30 p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="rounded-md bg-amber-200/80 px-2 py-0.5 text-[10px] font-bold text-amber-950 uppercase tracking-wider">
                        {item.sponsored_label}
                      </span>
                      <span className="text-[11px] text-ink-soft">From: {item.source_institution_name}</span>
                    </div>
                    <h4 className="font-semibold text-sm text-ink">{item.opportunity_title}</h4>
                    <div className="text-[11px] text-ink-soft">
                      Cross-campus spotlight valid through {new Date(item.end_date).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 3: ALUMNI DIRECTORY CSV IMPORT */}
      {/* ==================================================================== */}
      {subTab === "import" && (
        <div className="space-y-6">
          <div>
            <h2 className="font-display text-xl font-bold">Approved Alumni CSV Directory Import</h2>
            <p className="text-xs text-ink-soft mt-0.5">
              Securely onboard verified institutional alumni with pre-import dry run validation and privacy protection.
            </p>
          </div>

          <div className="rounded-2xl border border-line bg-paper p-6 shadow-sm space-y-4">
            <h3 className="font-semibold text-sm">Upload or Paste CSV Directory Data</h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-ink-soft mb-1">Source Filename *</label>
                <input
                  type="text"
                  required
                  value={csvFilename}
                  onChange={(e) => setCsvFilename(e.target.value)}
                  className="w-full rounded-lg border border-line bg-paper-warm px-3 py-2 text-sm focus:border-ink focus:outline-none"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-ink-soft mb-1">
                CSV Content (Headers: email, full_name, grad_year, degree, current_role, company) *
              </label>
              <textarea
                rows={6}
                value={csvText}
                onChange={(e) => setCsvText(e.target.value)}
                placeholder="email,full_name,grad_year,degree,current_role,company&#10;grace@apex.edu,Grace Hopper,2018,B.S. CS,Systems Engineer,Naval Research"
                className="w-full font-mono text-xs rounded-lg border border-line bg-paper-warm p-3 focus:border-ink focus:outline-none"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={handlePreviewImport}
                disabled={isLoading || !csvText.trim()}
                className="rounded-lg bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft disabled:opacity-50"
              >
                {isLoading ? "Validating..." : "Preview & Dry-Run"}
              </button>
            </div>
          </div>

          {/* Dry Run Preview Modal / Section */}
          {importPreview && (
            <div className="rounded-2xl border border-sky-200 bg-sky-50/40 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm text-sky-950">Dry-Run Validation Results</h3>
                <span className="text-xs text-sky-800 font-medium">Total Rows: {importPreview.total_rows}</span>
              </div>

              {/* Statistics pills */}
              <div className="grid grid-cols-3 gap-3 text-center text-xs">
                <div className="rounded-xl bg-white p-3 border border-sky-100 shadow-sm">
                  <div className="text-lg font-bold text-emerald-600">{importPreview.valid_rows}</div>
                  <div className="text-ink-soft">Valid Rows</div>
                </div>
                <div className="rounded-xl bg-white p-3 border border-sky-100 shadow-sm">
                  <div className="text-lg font-bold text-amber-600">{importPreview.duplicate_rows}</div>
                  <div className="text-ink-soft">Duplicates (Skipped)</div>
                </div>
                <div className="rounded-xl bg-white p-3 border border-sky-100 shadow-sm">
                  <div className="text-lg font-bold text-rose-600">{importPreview.invalid_rows}</div>
                  <div className="text-ink-soft">Invalid Format</div>
                </div>
              </div>

              {/* Legal / Consent Notice */}
              <div className="rounded-xl bg-amber-50 p-4 border border-amber-200 text-xs text-amber-900">
                <strong>Data Protection Guarantee:</strong> {importPreview.consent_notice}
              </div>

              {/* Commit action */}
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setImportPreview(null)}
                  className="rounded-lg border border-line px-4 py-2 text-xs font-semibold text-ink-soft hover:bg-white"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleCommitImport}
                  disabled={isLoading || importPreview.valid_rows === 0}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  Commit Import ({importPreview.valid_rows} records)
                </button>
              </div>
            </div>
          )}

          {/* Past Import Jobs Audit Trail */}
          <div className="space-y-3">
            <h3 className="font-semibold text-sm">Import Jobs Audit Trail</h3>
            {importJobs.length === 0 ? (
              <div className="rounded-2xl border border-line bg-paper p-6 text-center text-xs text-ink-soft">
                No past import jobs recorded for this institution.
              </div>
            ) : (
              <div className="rounded-2xl border border-line bg-paper overflow-hidden shadow-sm">
                <table className="w-full text-left text-xs">
                  <thead className="bg-paper-warm border-b border-line text-ink-soft uppercase tracking-wider font-semibold">
                    <tr>
                      <th className="p-3">Filename</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Accepted</th>
                      <th className="p-3">Skipped</th>
                      <th className="p-3">Rejected</th>
                      <th className="p-3">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {importJobs.map((j) => (
                      <tr key={j.id} className="hover:bg-paper-warm/50 transition">
                        <td className="p-3 font-semibold text-ink">{j.filename}</td>
                        <td className="p-3 capitalize">{j.status}</td>
                        <td className="p-3 text-emerald-600 font-bold">{j.accepted_rows}</td>
                        <td className="p-3 text-amber-600">{j.skipped_rows}</td>
                        <td className="p-3 text-rose-600">{j.rejected_rows}</td>
                        <td className="p-3 text-ink-soft">{new Date(j.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 4: PILOT & RELEASE ANALYTICS */}
      {/* ==================================================================== */}
      {subTab === "metrics" && (
        <div className="space-y-6">
          {(currentUser?.is_demo || metrics?.institution_id === "demo-inst-apex-tech-001") && (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-900 shadow-2xs flex items-start gap-3">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-200 text-amber-900 font-bold text-xs mt-0.5">
                !
              </div>
              <div className="text-xs space-y-1">
                <div className="font-bold uppercase tracking-wider text-amber-950">
                  DEMONSTRATION METRICS / DEMO DATA
                </div>
                <p className="text-amber-800 leading-relaxed">
                  The figures displayed below are derived strictly from isolated synthetic demonstration records persisted in the demo workspace database. They illustrate platform functionality and audit reporting capabilities, and must not be presented as genuine institutional adoption, real-world engagement, or commercial pilot revenue.
                </p>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-xl font-bold">Pilot & Release Operational Metrics</h2>
              <p className="text-xs text-ink-soft mt-0.5">
                Auditable operational indicators calculated from actual persisted records in {metrics?.institution_name || "this college"}.
              </p>
            </div>
            {metrics && (
              <span className="rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 px-3 py-1 text-xs font-bold uppercase tracking-wider">
                {(metrics.readiness_status || "").replace(/_/g, " ")}
              </span>
            )}
          </div>

          {!metrics ? (
            <div className="rounded-2xl border border-line bg-paper p-8 text-center text-sm text-ink-soft">
              Loading pilot metrics from persisted records...
            </div>
          ) : (
            <div className="space-y-6">
              {/* Stat Cards Grid */}
              <div className="grid gap-4 sm:grid-cols-4">
                <div className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-1">
                  <div className="text-xs uppercase font-semibold text-ink-soft tracking-wider">Opportunities</div>
                  <div className="text-2xl font-bold text-ink">{metrics.opportunities.total}</div>
                  <div className="text-[11px] text-ink-soft">
                    {metrics.opportunities.high_evidence} High Evidence | {metrics.opportunities.moderate_evidence} Moderate
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-1">
                  <div className="text-xs uppercase font-semibold text-ink-soft tracking-wider">Student Needs</div>
                  <div className="text-2xl font-bold text-ink">{metrics.student_needs.total}</div>
                  <div className="text-[11px] text-ink-soft">
                    {metrics.student_needs.matched} Matched | {metrics.student_needs.resolved} Resolved
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-1">
                  <div className="text-xs uppercase font-semibold text-ink-soft tracking-wider">Helper Matches</div>
                  <div className="text-2xl font-bold text-ink">{metrics.helper_matches.total_evaluated}</div>
                  <div className="text-[11px] text-ink-soft">
                    {metrics.helper_matches.accepted} Accepted by students
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-1">
                  <div className="text-xs uppercase font-semibold text-ink-soft tracking-wider">Institutional Memory</div>
                  <div className="text-2xl font-bold text-ink">{metrics.legacy_knowledge.handovers_total}</div>
                  <div className="text-[11px] text-ink-soft">
                    {metrics.legacy_knowledge.handovers_acknowledged} Acknowledged handovers
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-1">
                  <div className="text-xs uppercase font-semibold text-ink-soft tracking-wider">Sponsorship Requests</div>
                  <div className="text-2xl font-bold text-ink">{metrics.sponsorship.requests_total}</div>
                  <div className="text-[11px] text-ink-soft">
                    {metrics.sponsorship.accepted} Agreed terms | {metrics.sponsorship.under_review} Under review
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-1">
                  <div className="text-xs uppercase font-semibold text-ink-soft tracking-wider">Cross-College Campaigns</div>
                  <div className="text-2xl font-bold text-ink">{metrics.cross_college_promotion.campaigns_created}</div>
                  <div className="text-[11px] text-ink-soft">
                    {metrics.cross_college_promotion.campaigns_approved} Approved & active
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-1">
                  <div className="text-xs uppercase font-semibold text-ink-soft tracking-wider">Alumni Network</div>
                  <div className="text-2xl font-bold text-ink">{metrics.alumni_network.alumni_count}</div>
                  <div className="text-[11px] text-ink-soft">
                    {metrics.alumni_network.imported_rows_accepted} Imported via directory
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-1">
                  <div className="text-xs uppercase font-semibold text-ink-soft tracking-wider">Total Campus Members</div>
                  <div className="text-2xl font-bold text-ink">{metrics.alumni_network.total_members}</div>
                  <div className="text-[11px] text-ink-soft">
                    {metrics.alumni_network.student_count} Enrolled students
                  </div>
                </div>
              </div>

              {/* Methodology Notes */}
              <div className="rounded-2xl border border-line bg-paper p-5 shadow-sm space-y-2">
                <h4 className="font-semibold text-xs text-ink uppercase tracking-wider">Evaluation Principles</h4>
                <ul className="list-disc list-inside text-xs text-ink-soft space-y-1">
                  {metrics.notes.map((n, idx) => (
                    <li key={idx}>{n}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
