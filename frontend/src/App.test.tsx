import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import App from "./App";
import { emptyEvents, healthBody, jsonResponse, networkDown, stubFetch } from "./test/helpers";

const HEALTH = "/api/v1/health";
const EVENTS = "/api/v1/events";

describe("App shell", () => {
  it("renders branding and tagline", async () => {
    stubFetch({ [HEALTH]: () => jsonResponse(healthBody()), [EVENTS]: () => jsonResponse(emptyEvents) });
    render(<App />);
    expect(screen.getByText("EventSignal")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Evidence Before You Register." })).toBeInTheDocument();
    await screen.findByText("Backend connected");
  });

  it("shows a loading state before the backend answers", async () => {
    stubFetch({ [HEALTH]: () => new Promise<Response>(() => undefined), [EVENTS]: () => new Promise<Response>(() => undefined) });
    render(<App />);
    expect(screen.getByText("Checking backend")).toBeInTheDocument();
    expect(screen.getByText("Checking the backend")).toBeInTheDocument();
    expect(screen.getByText("Loading your events")).toBeInTheDocument();
  });

  it("shows the real health response when the backend is healthy", async () => {
    stubFetch({ [HEALTH]: () => jsonResponse(healthBody()), [EVENTS]: () => jsonResponse(emptyEvents) });
    render(<App />);
    expect(await screen.findByText("Backend connected")).toBeInTheDocument();
    expect(screen.getByText(/Version 9\.8\.7-test/)).toBeInTheDocument();
    expect(screen.getByText("Database reachable and schema present.")).toBeInTheDocument();
  });

  it("does not show a green state when the backend reports an unhealthy database", async () => {
    const body = healthBody({
      status: "unhealthy",
      message: "A required dependency is unavailable.",
      components: { api: { status: "ok", message: "API responding." }, database: { status: "unavailable", message: "Database connection failed." } },
    });
    stubFetch({ [HEALTH]: () => jsonResponse(body, 503), [EVENTS]: () => jsonResponse(emptyEvents) });
    render(<App />);
    expect(await screen.findByText("Backend unhealthy")).toBeInTheDocument();
    expect(screen.queryByText("Backend connected")).not.toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
  });

  it("shows an honest error state when the backend cannot be reached", async () => {
    stubFetch({ [HEALTH]: networkDown, [EVENTS]: networkDown });
    render(<App />);
    expect(await screen.findByText("Cannot connect to backend")).toBeInTheDocument();
    expect(screen.queryByText("Backend connected")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Cannot connect to the backend" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Your events could not be loaded" })).toBeInTheDocument();
    // An unreachable backend must not be presented as an empty workspace.
    expect(screen.queryByText(/no events yet/i)).not.toBeInTheDocument();
  });

  it("retries the health check and recovers", async () => {
    let up = false;
    stubFetch({
      [HEALTH]: () => (up ? jsonResponse(healthBody()) : networkDown()),
      [EVENTS]: () => jsonResponse(emptyEvents),
    });
    render(<App />);
    await screen.findByText("Cannot connect to backend");

    up = true;
    await userEvent.click(screen.getByRole("button", { name: "Retry connection" }));
    expect(await screen.findByText("Backend connected")).toBeInTheDocument();
    expect(screen.queryByText("Cannot connect to backend")).not.toBeInTheDocument();
  });
});

describe("Event workspace", () => {
  it("shows an empty state without any fictional events, metrics or assessments", async () => {
    stubFetch({ [HEALTH]: () => jsonResponse(healthBody()), [EVENTS]: () => jsonResponse(emptyEvents) });
    render(<App />);
    expect(await screen.findByText("The workspace is ready, with no events yet")).toBeInTheDocument();
    const workspace = screen.getByRole("region", { name: "Event workspace" });
    expect(within(workspace).queryByRole("list")).not.toBeInTheDocument();
    expect(within(workspace).queryByRole("listitem")).not.toBeInTheDocument();
    expect(workspace.textContent).not.toMatch(/\d/);
    expect(screen.queryByRole("form")).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("lists events only when the API returns them", async () => {
    const events = {
      items: [
        { id: "1", event_name: "Synthetic Test Event", organizer: "Synthetic Org" },
        { id: "2", event_name: null, organizer: null },
      ],
      total: 2,
      limit: 50,
      offset: 0,
    };
    stubFetch({ [HEALTH]: () => jsonResponse(healthBody()), [EVENTS]: () => jsonResponse(events) });
    render(<App />);
    expect(await screen.findByText("Synthetic Test Event")).toBeInTheDocument();
    expect(screen.getByText("Untitled event")).toBeInTheDocument();
    expect(screen.getByText("Organizer not stated")).toBeInTheDocument();
    expect(screen.queryByText(/no events yet/i)).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("2 events stored")).toBeInTheDocument());
  });

  it("can retry loading events independently", async () => {
    let up = false;
    stubFetch({
      [HEALTH]: () => jsonResponse(healthBody()),
      [EVENTS]: () => (up ? jsonResponse(emptyEvents) : networkDown()),
    });
    render(<App />);
    await screen.findByText("Your events could not be loaded");
    up = true;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("The workspace is ready, with no events yet")).toBeInTheDocument();
  });
});
