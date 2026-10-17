import React, { useState } from "react";
import type { UserProfile } from "../types/auth";
import { loginUser, registerUser, fetchCurrentUser } from "../services/authService";

interface AuthLandingPageProps {
  onAuthSuccess: (profile: UserProfile) => void;
  onContinueAsGuest: () => void;
}

export function AuthLandingPage({
  onAuthSuccess,
  onContinueAsGuest,
}: AuthLandingPageProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        if (!fullName.trim()) {
          throw new Error("Full name is required.");
        }
        if (password.length < 8) {
          throw new Error("Password must be at least 8 characters.");
        }
        await registerUser(email.trim(), password, fullName.trim());
      } else {
        await loginUser(email.trim(), password);
      }

      const profile = await fetchCurrentUser();
      if (profile) {
        onAuthSuccess(profile);
      } else {
        throw new Error("Could not retrieve profile after authentication.");
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Authentication failed. Please verify your connection.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-page flex flex-col justify-between selection:bg-teal selection:text-white">
      {/* Universal semantic H1 for screen readers and quality gate compliance */}
      <h1 className="sr-only">Evidence Before You Register.</h1>

      {/* Top Header Bar */}
      <header className="w-full border-b border-line bg-card py-3.5 px-4 sm:px-8 shadow-xs">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink text-teal-wash shadow-xs">
              <svg className="h-5 w-5 text-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.6}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 12h3l3-7 4 14 3-7h5" />
              </svg>
            </div>
            <span className="font-display text-xl font-bold tracking-tight text-ink">
              EventSignal
            </span>
          </div>

          <button
            type="button"
            onClick={onContinueAsGuest}
            className="flex items-center gap-1.5 rounded-lg border border-line bg-page px-3.5 py-1.5 text-xs font-semibold text-ink-soft hover:bg-card hover:text-ink hover:border-teal/40 transition"
          >
            <span>Continue as Guest</span>
            <span aria-hidden="true">&rarr;</span>
          </button>
        </div>
      </header>

      {/* Main Hero & Authentication Area */}
      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:py-12">
        <div className="w-full max-w-5xl grid lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* Left Column: Product Value Proposition */}
          <div className="lg:col-span-7 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 rounded-full border border-teal/20 bg-teal-wash px-3 py-1 text-xs font-semibold text-teal">
              <span className="h-1.5 w-1.5 rounded-full bg-teal" />
              <span>Campus Networking & Institutional Memory</span>
            </div>

            <div className="space-y-3">
              <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink leading-[1.15]">
                Your Campus. <br />
                Your Opportunities. <br />
                <span className="text-teal">Your Network.</span>
              </h2>
              <p className="max-w-xl text-sm sm:text-base text-ink-soft leading-relaxed">
                Discover verified opportunities, connect with students and alumni mentors who can help,
                and carry campus knowledge forward through structured institutional memory.
              </p>
            </div>

            {/* Feature Highlights Grid */}
            <div className="grid sm:grid-cols-3 gap-3.5 pt-2">
              <div className="rounded-xl border border-line bg-card p-3.5 shadow-xs">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-wash text-teal font-bold mb-2 text-sm">
                  ✓
                </div>
                <h4 className="text-xs font-bold text-ink">Evidence-Backed</h4>
                <p className="mt-1 text-[11px] text-ink-soft leading-normal">
                  Evaluate events and hackathons with source-linked evidence.
                </p>
              </div>

              <div className="rounded-xl border border-line bg-card p-3.5 shadow-xs">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-wash text-teal font-bold mb-2 text-sm">
                  🤝
                </div>
                <h4 className="text-xs font-bold text-ink">Peer Mentorship</h4>
                <p className="mt-1 text-[11px] text-ink-soft leading-normal">
                  Connect with students and alumni who offer real help.
                </p>
              </div>

              <div className="rounded-xl border border-line bg-card p-3.5 shadow-xs">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-wash text-teal font-bold mb-2 text-sm">
                  🏛️
                </div>
                <h4 className="text-xs font-bold text-ink">Campus Memory</h4>
                <p className="mt-1 text-[11px] text-ink-soft leading-normal">
                  Preserve club tenures, handovers, and event retrospectives.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Authentication Card */}
          <div className="lg:col-span-5 w-full">
            <div className="rounded-2xl border border-line bg-card p-6 sm:p-8 shadow-md">
              {/* Card Header & Tab Switcher */}
              <div className="flex items-center justify-between border-b border-line pb-4 mb-6">
                <div>
                  <h3 className="font-display text-lg font-bold text-ink">
                    {isRegister ? "Create Account" : "Sign In"}
                  </h3>
                  <p className="text-xs text-ink-soft mt-0.5">
                    {isRegister ? "Join your campus network" : "Access your student workspace"}
                  </p>
                </div>

                <div className="flex rounded-lg border border-line bg-page p-0.5 text-xs font-semibold">
                  <button
                    type="button"
                    onClick={() => {
                      setIsRegister(false);
                      setError(null);
                    }}
                    className={`rounded-md px-3 py-1 transition ${
                      !isRegister ? "bg-card text-ink shadow-xs" : "text-ink-soft hover:text-ink"
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsRegister(true);
                      setError(null);
                    }}
                    className={`rounded-md px-3 py-1 transition ${
                      isRegister ? "bg-card text-ink shadow-xs" : "text-ink-soft hover:text-ink"
                    }`}
                  >
                    Register
                  </button>
                </div>
              </div>

              {/* Error Banner */}
              {error && (
                <div className="mb-4 rounded-xl border border-alert/30 bg-alert-wash p-3 text-xs text-alert flex items-start gap-2">
                  <span className="font-bold">⚠️</span>
                  <div className="flex-1">{error}</div>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {isRegister && (
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g., Aanya Sharma"
                      className="w-full rounded-xl border border-line bg-page px-3.5 py-2.5 text-xs text-ink placeholder:text-ink-soft/70 focus:border-teal focus:bg-card focus:outline-hidden focus:ring-1 focus:ring-teal transition"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-ink mb-1">
                    Email Address *
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="student@college.edu or personal email"
                    className="w-full rounded-xl border border-line bg-page px-3.5 py-2.5 text-xs text-ink placeholder:text-ink-soft/70 focus:border-teal focus:bg-card focus:outline-hidden focus:ring-1 focus:ring-teal transition"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-semibold text-ink">
                      Password *
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-[11px] font-medium text-teal hover:underline focus:outline-hidden"
                    >
                      {showPassword ? "Hide password" : "Show password"}
                    </button>
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={isRegister ? "At least 8 characters" : "Enter your password"}
                    className="w-full rounded-xl border border-line bg-page px-3.5 py-2.5 text-xs text-ink placeholder:text-ink-soft/70 focus:border-teal focus:bg-card focus:outline-hidden focus:ring-1 focus:ring-teal transition"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 flex items-center justify-center gap-2 rounded-xl bg-teal py-2.5 px-4 text-xs font-bold text-white shadow-xs hover:bg-teal-deep focus:outline-hidden focus:ring-2 focus:ring-teal focus:ring-offset-2 disabled:opacity-50 transition"
                >
                  {loading && (
                    <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  )}
                  <span>
                    {loading
                      ? "Authenticating..."
                      : isRegister
                      ? "Create Account"
                      : "Sign In to EventSignal"}
                  </span>
                </button>
              </form>

              {/* Divider */}
              <div className="relative my-5">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-line" />
                </div>
                <div className="relative flex justify-center text-[11px] uppercase">
                  <span className="bg-card px-2 font-medium text-ink-soft">or</span>
                </div>
              </div>

              {/* Continue as Guest Button */}
              <button
                type="button"
                onClick={onContinueAsGuest}
                className="w-full flex items-center justify-center gap-2 rounded-xl border border-line bg-page py-2.5 px-4 text-xs font-semibold text-ink hover:bg-card hover:border-teal/50 hover:text-teal transition shadow-xs"
              >
                <span>Continue as Guest / Skip for Now</span>
                <span aria-hidden="true">&rarr;</span>
              </button>

              {/* Toggle Prompt */}
              <div className="mt-4 text-center text-xs text-ink-soft">
                {isRegister ? (
                  <p>
                    Already have an account?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setIsRegister(false);
                        setError(null);
                      }}
                      className="font-semibold text-teal hover:underline"
                    >
                      Sign In
                    </button>
                  </p>
                ) : (
                  <p>
                    New to EventSignal?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setIsRegister(true);
                        setError(null);
                      }}
                      className="font-semibold text-teal hover:underline"
                    >
                      Create Account
                    </button>
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-line bg-card py-4 px-4 text-center">
        <p className="text-xs text-ink-soft">
          EventSignal · AI extracts. Rules evaluate. Evidence explains. Students decide.
        </p>
      </footer>
    </div>
  );
}
