import { useState } from "react";
import type { Opportunity } from "../types/opportunity";
import type { HelpOffer } from "../types/helpOffer";
import { AssessmentPanel } from "./AssessmentPanel";
import { OpportunityIntakeForm } from "./OpportunityIntakeForm";
import { requestHelpOffer } from "../services/helpOfferService";
import { createStudentNeed, runMatchingForNeed } from "../services/legacyService";

// 1. Opportunity Details Modal
interface OpportunityDetailModalProps {
  opportunity: Opportunity | null;
  onClose: () => void;
  onRefresh: () => void;
}

export function OpportunityDetailModal({ opportunity, onClose, onRefresh }: OpportunityDetailModalProps) {
  if (!opportunity) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="relative w-full max-w-3xl rounded-2xl border border-line bg-card shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-line px-6 py-4 bg-page">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal">Opportunity Provenance</span>
            <h3 className="font-display text-lg font-bold text-ink truncate max-w-lg">
              {opportunity.title || opportunity.event_name || "Opportunity Details"}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-soft hover:bg-card hover:text-ink transition"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <AssessmentPanel
            opportunityId={opportunity.id}
            opportunityTitle={opportunity.title || opportunity.event_name || null}
          />
        </div>

        {/* Footer */}
        <div className="border-t border-line px-6 py-3 bg-page flex justify-between items-center">
          <button
            onClick={() => onRefresh()}
            className="text-xs font-semibold text-teal hover:underline"
          >
            Refresh evidence
          </button>
          <button
            onClick={onClose}
            className="rounded-lg bg-ink px-4 py-2 text-xs font-semibold text-white transition hover:bg-teal"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
}

// 2. Submit Opportunity / Share Event Modal
interface QuickIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (opportunity: Opportunity) => void;
  title?: string;
}

export function QuickIntakeModal({ isOpen, onClose, onSuccess, title = "Submit Opportunity" }: QuickIntakeModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="relative w-full max-w-lg rounded-2xl border border-line bg-card shadow-2xl overflow-hidden my-8">
        <div className="flex items-center justify-between border-b border-line px-5 py-4 bg-page">
          <div className="flex items-center gap-2">
            <span className="text-teal font-bold">🔗</span>
            <h3 className="font-display text-base font-bold text-ink">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-lg text-ink-soft hover:bg-card hover:text-ink transition"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="p-5">
          <p className="text-xs text-ink-soft mb-4 leading-relaxed">
            Submit a public opportunity or campus event URL. EventSignal will safely retrieve the page, extract key
            provenance fields, and attach structured evidence.
          </p>

          <OpportunityIntakeForm
            onIngestSuccess={(response) => {
              onSuccess(response.opportunity);
              onClose();
            }}
            onClose={onClose}
          />
        </div>
      </div>
    </div>
  );
}

// 3. Connect to Mentor / Helper Modal
interface ConnectModalProps {
  offer: HelpOffer | null;
  institutionId?: string | undefined;
  onClose: () => void;
  onSuccess: () => void;
}

export function ConnectModal({ offer, institutionId, onClose, onSuccess }: ConnectModalProps) {
  const [purpose, setPurpose] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!offer || !institutionId) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!purpose.trim()) {
      setError("Please specify the purpose of your request.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const fullMessage = message.trim() ? `${purpose.trim()}: ${message.trim()}` : purpose.trim();
      await requestHelpOffer(institutionId, offer.id, fullMessage);
      onSuccess();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to send request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-xs p-4">
      <div className="relative w-full max-w-md rounded-2xl border border-line bg-card shadow-2xl p-5">
        <div className="flex items-center justify-between pb-3 border-b border-line">
          <div>
            <h3 className="font-display text-base font-bold text-ink">Request Connection</h3>
            <p className="text-xs text-ink-soft">Connect with {offer.creator_name || "Mentor"}</p>
          </div>
          <button onClick={onClose} className="text-ink-soft hover:text-ink">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-3.5">
          {error && <div className="rounded-lg bg-alert-wash p-2.5 text-xs text-alert">{error}</div>}

          <div>
            <label className="block text-xs font-semibold text-ink">Purpose of Request *</label>
            <input
              type="text"
              required
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              placeholder="e.g., Code review, mock interview, project advice"
              className="mt-1 w-full rounded-lg border border-line bg-page px-3 py-2 text-xs text-ink focus:border-teal focus:bg-card focus:outline-hidden"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink">Introduction Note (Optional)</label>
            <textarea
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Share context on what you're working on..."
              className="mt-1 w-full rounded-lg border border-line bg-page px-3 py-2 text-xs text-ink focus:border-teal focus:bg-card focus:outline-hidden"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-line">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-ink hover:bg-page"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-lg bg-teal px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-teal-deep disabled:opacity-50"
            >
              {isSubmitting ? "Sending..." : "Send Request"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// 4. Quick Ask for Help Modal (Student Need Declaration)
interface QuickNeedModalProps {
  isOpen: boolean;
  institutionId?: string | undefined;
  onClose: () => void;
  onSuccess: () => void;
}

export function QuickNeedModal({ isOpen, institutionId, onClose, onSuccess }: QuickNeedModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [urgency, setUrgency] = useState<"low" | "medium" | "high">("medium");
  const [category, setCategory] = useState("general_mentorship");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !institutionId) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) {
      setError("Please fill in both title and description.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const need = await createStudentNeed(institutionId, {
        title: title.trim(),
        description: description.trim(),
        category,
        urgency,
        preferred_delivery_mode: "virtual",
      });
      // Optionally trigger matching
      try {
        await runMatchingForNeed(institutionId, need.id);
      } catch {
        // non-blocking
      }
      onSuccess();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to post challenge.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-xs p-4">
      <div className="relative w-full max-w-md rounded-2xl border border-line bg-card shadow-2xl p-5">
        <div className="flex items-center justify-between pb-3 border-b border-line">
          <div>
            <h3 className="font-display text-base font-bold text-ink">Ask for Help</h3>
            <p className="text-xs text-ink-soft">Declare a challenge for deterministic helper matching</p>
          </div>
          <button onClick={onClose} className="text-ink-soft hover:text-ink">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          {error && <div className="rounded-lg bg-alert-wash p-2 text-xs text-alert">{error}</div>}

          <div>
            <label className="block text-xs font-semibold text-ink">Challenge Title *</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., GSoC proposal review or React state debugging"
              className="mt-1 w-full rounded-lg border border-line bg-page px-3 py-1.5 text-xs text-ink focus:border-teal focus:bg-card focus:outline-hidden"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="mt-1 w-full rounded-lg border border-line bg-page px-2 py-1.5 text-xs text-ink focus:border-teal focus:bg-card focus:outline-hidden"
            >
              <option value="general_mentorship">General Mentorship</option>
              <option value="career_guidance">Career Guidance</option>
              <option value="interview_prep">Interview Prep</option>
              <option value="code_review">Code / Project Review</option>
              <option value="research_advice">Research Guidance</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink">Description & Context *</label>
            <textarea
              rows={3}
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe where you're blocked and what help you need..."
              className="mt-1 w-full rounded-lg border border-line bg-page px-3 py-1.5 text-xs text-ink focus:border-teal focus:bg-card focus:outline-hidden"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink">Urgency</label>
            <select
              value={urgency}
              onChange={(e) => setUrgency(e.target.value as "low" | "medium" | "high")}
              className="mt-1 w-full rounded-lg border border-line bg-page px-2 py-1.5 text-xs text-ink focus:border-teal focus:bg-card focus:outline-hidden"
            >
              <option value="low">Low (Flexible timing)</option>
              <option value="medium">Medium (Within 1-2 weeks)</option>
              <option value="high">High (Upcoming deadline)</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-line">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-ink hover:bg-page"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-lg bg-teal px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-teal-deep disabled:opacity-50"
            >
              {isSubmitting ? "Submitting..." : "Post Need"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
