import React, { useEffect, useState } from "react";
import type { MediaStatus } from "../types/media";
import { fetchMediaStatus } from "../services/mediaService";

interface CloudinaryStatusCheckerProps {
  className?: string;
  variant?: "card" | "pill";
}

export const CloudinaryStatusChecker: React.FC<CloudinaryStatusCheckerProps> = ({
  className = "",
  variant = "card",
}) => {
  const [status, setStatus] = useState<MediaStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [lastChecked, setLastChecked] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const checkConnection = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const data = await fetchMediaStatus();
      const elapsed = Math.round(performance.now() - start);
      setStatus(data);
      setLatencyMs(elapsed);
      setLastChecked(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to connect to media service");
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkConnection();
  }, []);

  const isConnected = status !== null && status.enabled && Boolean(status.cloud_name);

  // Compact Pill Variant (e.g. for header)
  if (variant === "pill") {
    return (
      <div
        data-testid="cloudinary-status-pill"
        className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-medium transition ${
          loading
            ? "border-line bg-page text-ink-soft"
            : isConnected
            ? "border-emerald-300/80 bg-emerald-50 text-emerald-800"
            : "border-amber-300/80 bg-amber-50 text-amber-800"
        } ${className}`}
      >
        <span
          className={`h-2 w-2 rounded-full ${
            loading
              ? "bg-ink-soft/40 animate-pulse"
              : isConnected
              ? "bg-emerald-500 animate-pulse"
              : "bg-amber-500"
          }`}
          aria-hidden="true"
        />
        <svg className="h-3.5 w-3.5 opacity-80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
        </svg>
        <span className="font-semibold">
          {loading ? "Checking Cloudinary..." : isConnected ? `Cloudinary: Connected (${status.cloud_name})` : "Cloudinary: Not Connected"}
        </span>
      </div>
    );
  }

  // Full Card Variant (for main page area)
  return (
    <div
      data-testid="cloudinary-checker"
      aria-label="Cloudinary Integration Status Checker"
      className={`rounded-xl border border-line bg-card p-4 shadow-xs transition ${className}`}
    >
      {/* Header & Status Indicator */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div
            className={`flex h-8 w-8 items-center justify-center rounded-lg ${
              isConnected
                ? "bg-emerald-100 text-emerald-700"
                : loading
                ? "bg-teal-wash text-teal"
                : "bg-amber-100 text-amber-700"
            }`}
          >
            <svg className="h-4.5 w-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-xs font-bold text-ink">Cloudinary Media Integration</h4>
              <span
                data-testid="cloudinary-status-badge"
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                  loading
                    ? "bg-page text-ink-soft border border-line"
                    : isConnected
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-300"
                    : "bg-amber-50 text-amber-800 border border-amber-300"
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    loading ? "bg-ink-soft/40" : isConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
                  }`}
                  aria-hidden="true"
                />
                <span>
                  {loading
                    ? "Checking..."
                    : isConnected
                    ? "Connected"
                    : "Not Connected (Fallback Mode)"}
                </span>
              </span>
            </div>
            <p className="text-[11px] text-ink-soft mt-0.5">
              {isConnected
                ? `Live Cloud CDN connected to cloud '${status.cloud_name}'. Posters and event galleries ready.`
                : loading
                ? "Checking server media configuration and Cloudinary provider status..."
                : "Media uploads run in graceful fallback mode. System operates normally with SVG identicons."}
            </p>
          </div>
        </div>

        {/* Live Check Button */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={checkConnection}
            disabled={loading}
            aria-label="Check Cloudinary connection"
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-page px-2.5 py-1.5 text-xs font-semibold text-ink-soft hover:bg-card hover:text-ink hover:border-teal/40 disabled:opacity-50 transition shadow-2xs"
          >
            <svg
              className={`h-3.5 w-3.5 text-teal ${loading ? "animate-spin" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>{loading ? "Checking..." : "Check Connection"}</span>
          </button>

          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="text-[11px] font-medium text-teal hover:underline px-1 py-1"
          >
            {showDetails ? "Hide Details" : "View Details"}
          </button>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="mt-3 rounded-lg border border-alert/30 bg-alert-wash p-2.5 text-[11px] text-alert flex items-center justify-between">
          <span>{error}</span>
          <button
            type="button"
            onClick={checkConnection}
            className="font-bold underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Expanded Diagnostic Details */}
      {showDetails && (
        <div className="mt-3.5 pt-3 border-t border-line/70 grid sm:grid-cols-4 gap-2.5 text-[11px]">
          <div className="rounded-lg bg-page p-2 border border-line/60">
            <span className="text-ink-soft block text-[10px] uppercase font-semibold">Cloud Name</span>
            <span className="font-mono font-bold text-ink truncate block">
              {status?.cloud_name ?? "None (Not Configured)"}
            </span>
          </div>
          <div className="rounded-lg bg-page p-2 border border-line/60">
            <span className="text-ink-soft block text-[10px] uppercase font-semibold">Upload Mode</span>
            <span className="font-bold text-ink block">
              {isConnected ? "Server-Signed Direct" : "Local Fallback"}
            </span>
          </div>
          <div className="rounded-lg bg-page p-2 border border-line/60">
            <span className="text-ink-soft block text-[10px] uppercase font-semibold">Max File Limit</span>
            <span className="font-bold text-ink block">
              {status?.max_file_size_bytes
                ? `${Math.round(status.max_file_size_bytes / (1024 * 1024))} MB`
                : "5 MB"}
            </span>
          </div>
          <div className="rounded-lg bg-page p-2 border border-line/60">
            <span className="text-ink-soft block text-[10px] uppercase font-semibold">Ping Latency</span>
            <span className="font-bold text-teal block">
              {latencyMs !== null ? `${latencyMs} ms` : "—"}
              {lastChecked && <span className="text-[10px] text-ink-soft font-normal ml-1">({lastChecked})</span>}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

