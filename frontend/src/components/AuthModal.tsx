import React, { useState } from "react";
import type { UserProfile } from "../types/auth";
import { loginUser, registerUser } from "../services/authService";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserProfile | null;
  onAuthSuccess: (profile: UserProfile | null) => void;
  onLogout: () => void;
}

export function AuthModal({
  isOpen,
  onClose,
  currentUser,
  onAuthSuccess,
  onLogout,
}: AuthModalProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        if (!fullName.trim()) {
          throw new Error("Full name is required.");
        }
        await registerUser(email, password, fullName);
      } else {
        await loginUser(email, password);
      }
      // Re-fetch current user profile
      const { fetchCurrentUser } = await import("../services/authService");
      const profile = await fetchCurrentUser();
      onAuthSuccess(profile);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Authentication failed.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-line bg-paper p-6 shadow-2xl sm:p-8">
        <div className="flex items-center justify-between border-b border-line pb-4">
          <h2 className="font-display text-xl font-bold tracking-tight">
            {currentUser
              ? "Account Profile"
              : isRegister
              ? "Create Student / Alumni Account"
              : "Sign In to EventSignal"}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-ink-soft hover:bg-paper-warm hover:text-ink"
            aria-label="Close dialog"
          >
            ✕
          </button>
        </div>

        {currentUser ? (
          <div className="mt-6 space-y-5">
            <div className="rounded-xl border border-line bg-paper-warm p-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft">
                Signed In As
              </div>
              <div className="mt-1 text-lg font-bold text-ink">
                {currentUser.user.full_name}
              </div>
              <div className="text-sm text-ink-soft">{currentUser.user.email}</div>
              {currentUser.user.is_superuser && (
                <span className="mt-2 inline-block rounded-full bg-accent/15 px-2.5 py-0.5 text-xs font-semibold text-accent">
                  Platform Administrator
                </span>
              )}
            </div>

            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-soft">
                College Affiliations ({currentUser.memberships.length})
              </div>
              {currentUser.memberships.length === 0 ? (
                <div className="rounded-lg border border-dashed border-line p-3 text-sm text-ink-soft">
                  No institutional memberships yet. Select a college workspace to join!
                </div>
              ) : (
                <div className="space-y-2">
                  {currentUser.memberships.map((m) => (
                    <div
                      key={m.id}
                      className="flex items-center justify-between rounded-lg border border-line bg-paper px-3 py-2 text-sm"
                    >
                      <span className="font-medium">
                        {m.institution_name || m.institution_slug || "Campus"}
                      </span>
                      <span className="rounded-full bg-paper-warm px-2 py-0.5 text-xs font-semibold capitalize text-ink">
                        {m.role}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-2">
              <button
                onClick={() => {
                  onLogout();
                  onClose();
                }}
                className="w-full rounded-xl border border-red-200 bg-red-50 py-2.5 text-sm font-semibold text-red-700 transition hover:bg-red-100"
              >
                Sign Out
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {isRegister && (
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Alex Rivera"
                  className="mt-1 w-full rounded-xl border border-line bg-paper px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                Institutional / Personal Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@university.edu"
                className="mt-1 w-full rounded-xl border border-line bg-paper px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                Password
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                className="mt-1 w-full rounded-xl border border-line bg-paper px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-4 w-full rounded-xl bg-ink py-2.5 text-sm font-semibold text-paper transition hover:bg-ink-light disabled:opacity-50"
            >
              {loading
                ? "Processing..."
                : isRegister
                ? "Create Account"
                : "Sign In"}
            </button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setIsRegister(!isRegister);
                  setError(null);
                }}
                className="text-xs font-medium text-accent hover:underline"
              >
                {isRegister
                  ? "Already have an account? Sign in"
                  : "Need an account? Register as student or alum"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
