import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { CloudinaryStatusChecker } from "./CloudinaryStatusChecker";
import * as mediaService from "../services/mediaService";

describe("CloudinaryStatusChecker", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders Connected status when Cloudinary is enabled and configured", async () => {
    vi.spyOn(mediaService, "fetchMediaStatus").mockResolvedValue({
      enabled: true,
      cloud_name: "snwg6j7w",
      allowed_formats: ["jpg", "png", "webp", "gif"],
      max_file_size_bytes: 5242880,
      folder_prefix: "eventsignal",
    });

    render(<CloudinaryStatusChecker variant="card" />);

    expect(screen.getByText("Cloudinary Media Integration")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("cloudinary-status-badge")).toHaveTextContent("Connected");
    });

    expect(screen.getByText(/Live Cloud CDN connected to cloud 'snwg6j7w'/i)).toBeInTheDocument();

    // Toggle details
    await userEvent.click(screen.getByRole("button", { name: /View Details/i }));
    expect(screen.getByText("snwg6j7w")).toBeInTheDocument();
    expect(screen.getByText("Server-Signed Direct")).toBeInTheDocument();
    expect(screen.getByText("5 MB")).toBeInTheDocument();
  });

  it("renders Not Connected (Fallback Mode) when Cloudinary is disabled", async () => {
    vi.spyOn(mediaService, "fetchMediaStatus").mockResolvedValue({
      enabled: false,
      cloud_name: null,
      allowed_formats: [],
      max_file_size_bytes: 5242880,
    });

    render(<CloudinaryStatusChecker variant="card" />);

    await waitFor(() => {
      expect(screen.getByTestId("cloudinary-status-badge")).toHaveTextContent("Not Connected (Fallback Mode)");
    });

    expect(screen.getByText(/Media uploads run in graceful fallback mode/i)).toBeInTheDocument();
  });

  it("re-checks connection when Check Connection button is clicked", async () => {
    const fetchSpy = vi.spyOn(mediaService, "fetchMediaStatus").mockResolvedValue({
      enabled: true,
      cloud_name: "snwg6j7w",
      allowed_formats: ["png"],
      max_file_size_bytes: 5242880,
    });

    render(<CloudinaryStatusChecker variant="card" />);

    await waitFor(() => {
      expect(screen.getByTestId("cloudinary-status-badge")).toHaveTextContent("Connected");
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    const checkBtn = screen.getByRole("button", { name: "Check Cloudinary connection" });
    await userEvent.click(checkBtn);

    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("renders pill variant for compact navigation display", async () => {
    vi.spyOn(mediaService, "fetchMediaStatus").mockResolvedValue({
      enabled: true,
      cloud_name: "snwg6j7w",
      allowed_formats: ["png"],
      max_file_size_bytes: 5242880,
    });

    render(<CloudinaryStatusChecker variant="pill" />);

    await waitFor(() => {
      expect(screen.getByTestId("cloudinary-status-pill")).toHaveTextContent("Cloudinary: Connected (snwg6j7w)");
    });
  });
});

