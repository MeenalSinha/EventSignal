/**
 * Runs the real application against real servers. No fetch stubbing.
 * Requires LIVE_API_URL (running backend) and LIVE_DEAD_URL (nothing listening).
 * Run through: python scripts/integration_test.py
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const LIVE = process.env.LIVE_API_URL;
const DEAD = process.env.LIVE_DEAD_URL;

async function renderAppAgainst(baseUrl: string) {
  vi.resetModules();
  vi.stubEnv("VITE_API_BASE_URL", baseUrl);
  vi.stubEnv("VITE_REQUEST_TIMEOUT_MS", "3000");
  const { default: App } = await import("./App");
  return render(<App />);
}

describe("live integration", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("is configured by the orchestrator", () => {
    expect(LIVE, "LIVE_API_URL must be set; run scripts/integration_test.py").toBeTruthy();
    expect(DEAD, "LIVE_DEAD_URL must be set; run scripts/integration_test.py").toBeTruthy();
  });

  it("shows the backend's actual health and an honest empty workspace", async () => {
    const actual = (await (await fetch(`${LIVE}/api/v1/health`)).json()) as { version: string; environment: string };
    await renderAppAgainst(LIVE!);
    expect(await screen.findByText("Backend connected")).toBeInTheDocument();
    expect(screen.getByText(new RegExp(`Version ${actual.version.replace(/\./g, "\\.")}, ${actual.environment} environment`))).toBeInTheDocument();
    expect(screen.getByText("Database reachable and schema present.")).toBeInTheDocument();
    expect(await screen.findByText("The workspace is ready, with no events yet")).toBeInTheDocument();
  });

  it("reports an unreachable backend and keeps the retry control available", async () => {
    await renderAppAgainst(DEAD!);
    expect(await screen.findByText("Cannot connect to backend")).toBeInTheDocument();
    expect(screen.queryByText("Backend connected")).not.toBeInTheDocument();
    const retry = screen.getByRole("button", { name: "Retry connection" });
    await userEvent.click(retry);
    expect(await screen.findByText("Cannot connect to backend")).toBeInTheDocument();
  });
});
