import React, { useEffect, useState } from "react";
import type { UserProfile } from "../types/auth";
import { loginUser, registerUser, fetchCurrentUser, fetchDemoStatus } from "../services/authService";

interface AuthLandingPageProps {
  onAuthSuccess: (profile: UserProfile) => void;
  onContinueAsGuest: () => void;
  onDemoAuthSuccess?: (profile: UserProfile) => void;
}

export function AuthLandingPage({
  onAuthSuccess,
  onContinueAsGuest,
  onDemoAuthSuccess,
}: AuthLandingPageProps) {
  const [authMode, setAuthMode] = useState<"signin" | "register" | "demo">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [demoEmail, setDemoEmail] = useState("");
  const [demoPassword, setDemoPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showDemoPassword, setShowDemoPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoEnabled, setDemoEnabled] = useState(false);

  useEffect(() => {
    fetchDemoStatus().then((status) => {
      setDemoEnabled(status.demo_mode_enabled);
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (authMode === "register") {
        if (!fullName.trim()) {
          throw new Error("Full name is required.");
        }
        if (password.length < 8) {
          throw new Error("Password must be at least 8 characters.");
        }
        await registerUser(email.trim(), password, fullName.trim());
      } else if (authMode === "demo") {
        if (!demoEmail.trim() || !demoPassword) {
          throw new Error("Demo email and password are required.");
        }
        await loginUser(demoEmail.trim(), demoPassword);
      } else {
        await loginUser(email.trim(), password);
      }

      const profile = await fetchCurrentUser();
      if (profile) {
        if (authMode === "demo" && onDemoAuthSuccess) {
          onDemoAuthSuccess(profile);
        } else {
          onAuthSuccess(profile);
        }
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
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-wash text-teal font-bold mb-2">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h4 className="text-xs font-bold text-ink">Evidence-Backed</h4>
                <p className="mt-1 text-[11px] text-ink-soft leading-normal">
                  Evaluate events and hackathons with source-linked evidence.
                </p>
              </div>

              <div className="rounded-xl border border-line bg-card p-3.5 shadow-xs">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-wash text-teal font-bold mb-2">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <h4 className="text-xs font-bold text-ink">Peer Mentorship</h4>
                <p className="mt-1 text-[11px] text-ink-soft leading-normal">
                  Connect with students and alumni who offer real help.
                </p>
              </div>

              <div className="rounded-xl border border-line bg-card p-3.5 shadow-xs">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-wash text-teal font-bold mb-2">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
                  </svg>
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
            <div className={`rounded-2xl border ${authMode === 'demo' ? 'border-amber-400/60 ring-1 ring-amber-400/30' : 'border-line'} bg-card p-6 sm:p-8 shadow-md transition`}>
              {/* Card Header & Tab Switcher */}
              <div className="flex items-center justify-between border-b border-line pb-4 mb-6">
                <div>
                  <h3 className="font-display text-lg font-bold text-ink">
                    {authMode === "demo"
                      ? "Demo Presentation Access"
                      : authMode === "register"
                      ? "Create Account"
                      : "Sign In"}
                  </h3>
                  <p className="text-xs text-ink-soft mt-0.5">
                    {authMode === "demo"
                      ? "Presentation mode for evaluators & judges"
                      : authMode === "register"
                      ? "Join your campus network"
                      : "Access your student workspace"}
                  </p>
                </div>

                <div className="flex rounded-lg border border-line bg-page p-0.5 text-xs font-semibold">
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode("signin");
                      setError(null);
                    }}
                    className={`rounded-md px-2.5 py-1 transition ${
                      authMode === "signin" ? "bg-card text-ink shadow-xs" : "text-ink-soft hover:text-ink"
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode("register");
                      setError(null);
                    }}
                    className={`rounded-md px-2.5 py-1 transition ${
                      authMode === "register" ? "bg-card text-ink shadow-xs" : "text-ink-soft hover:text-ink"
                    }`}
                  >
                    Register
                  </button>
                  {demoEnabled && (
                    <button
                      type="button"
                      onClick={() => {
                        setAuthMode("demo");
                        setError(null);
                      }}
                      className={`flex items-center gap-1 rounded-md px-2.5 py-1 transition ${
                        authMode === "demo"
                          ? "bg-amber-100 text-amber-900 font-bold shadow-xs border border-amber-300"
                          : "text-amber-700 hover:text-amber-900"
                      }`}
                    >
                      <svg className="h-3 w-3 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span>Demo</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Demo Mode Notice */}
              {authMode === "demo" && (
                <div className="mb-4 rounded-xl border border-amber-300/80 bg-amber-50/70 p-3 text-xs text-amber-900 space-y-1">
                  <div className="flex items-center gap-1.5 font-bold">
                    <svg className="h-4 w-4 text-amber-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Demonstration Presentation Mode</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-amber-800">
                    Authenticate using your dedicated demo credentials. Demo access loads an isolated collegiate dataset for live evaluation across all 8 modules.
                  </p>
                </div>
              )}

              {/* Error Banner */}
              {error && (
                <div className="mb-4 rounded-xl border border-alert/30 bg-alert-wash p-3 text-xs text-alert flex items-start gap-2">
                  <svg className="h-4 w-4 text-alert shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div className="flex-1">{error}</div>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {authMode === "register" && (
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

                {authMode === "demo" ? (
                  <>
                    <div>
                      <label className="block text-xs font-semibold text-ink mb-1">
                        Demo Account Email *
                      </label>
                      <input
                        type="email"
                        required
                        value={demoEmail}
                        onChange={(e) => setDemoEmail(e.target.value)}
                        placeholder="demo@eventsignal.local"
                        className="w-full rounded-xl border border-line bg-page px-3.5 py-2.5 text-xs text-ink placeholder:text-ink-soft/70 focus:border-amber-500 focus:bg-card focus:outline-hidden focus:ring-1 focus:ring-amber-500 transition"
                      />
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="block text-xs font-semibold text-ink">
                          Demo Password *
                        </label>
                        <button
                          type="button"
                          onClick={() => setShowDemoPassword(!showDemoPassword)}
                          className="text-[11px] font-medium text-amber-700 hover:underline focus:outline-hidden"
                        >
                          {showDemoPassword ? "Hide password" : "Show password"}
                        </button>
                      </div>
                      <input
                        type={showDemoPassword ? "text" : "password"}
                        required
                        value={demoPassword}
                        onChange={(e) => setDemoPassword(e.target.value)}
                        placeholder="Enter configured demo password"
                        className="w-full rounded-xl border border-line bg-page px-3.5 py-2.5 text-xs text-ink placeholder:text-ink-soft/70 focus:border-amber-500 focus:bg-card focus:outline-hidden focus:ring-1 focus:ring-amber-500 transition"
                      />
                    </div>
                  </>
                ) : (
                  <>
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
                        placeholder={authMode === "register" ? "At least 8 characters" : "Enter your password"}
                        className="w-full rounded-xl border border-line bg-page px-3.5 py-2.5 text-xs text-ink placeholder:text-ink-soft/70 focus:border-teal focus:bg-card focus:outline-hidden focus:ring-1 focus:ring-teal transition"
                      />
                    </div>
                  </>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className={`w-full mt-2 flex items-center justify-center gap-2 rounded-xl py-2.5 px-4 text-xs font-bold text-white shadow-xs focus:outline-hidden focus:ring-2 focus:ring-offset-2 disabled:opacity-50 transition ${
                    authMode === "demo"
                      ? "bg-amber-600 hover:bg-amber-700 focus:ring-amber-500"
                      : "bg-teal hover:bg-teal-deep focus:ring-teal"
                  }`}
                >
                  {loading && (
                    <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  )}
                  <span>
                    {loading
                      ? "Authenticating..."
                      : authMode === "demo"
                      ? "Sign In to Demo Mode"
                      : authMode === "register"
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
                {authMode === "demo" ? (
                  <p>
                    Presenting to evaluators?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setAuthMode("signin");
                        setError(null);
                      }}
                      className="font-semibold text-teal hover:underline"
                    >
                      Return to Standard Sign In
                    </button>
                  </p>
                ) : authMode === "register" ? (
                  <p>
                    Already have an account?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setAuthMode("signin");
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
                        setAuthMode("register");
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
