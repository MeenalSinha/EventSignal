import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { jsonResponse, stubFetch } from "../test/helpers";
import { MediaUploadWidget } from "./MediaUploadWidget";

describe("MediaUploadWidget", () => {
  it("renders disabled state when Cloudinary media is not enabled", async () => {
    stubFetch({
      "/api/v1/media/status": () =>
        jsonResponse({
          enabled: false,
          cloud_name: null,
          max_file_size_bytes: 10485760,
          allowed_formats: ["jpg", "jpeg", "png", "webp", "gif"],
        }),
    });

    render(<MediaUploadWidget purpose="opportunity_poster" label="Test Poster Upload" />);

    await waitFor(() => {
      expect(screen.getByText("Test Poster Upload")).toBeInTheDocument();
      expect(
        screen.getByText(/Cloudinary media storage is currently not configured or disabled/)
      ).toBeInTheDocument();
    });
  });

  it("renders upload area when Cloudinary is enabled", async () => {
    stubFetch({
      "/api/v1/media/status": () =>
        jsonResponse({
          enabled: true,
          cloud_name: "test-cloud",
          max_file_size_bytes: 10485760,
          allowed_formats: ["jpg", "jpeg", "png", "webp", "gif"],
        }),
    });

    render(<MediaUploadWidget purpose="opportunity_poster" label="Opportunity Poster" />);

    await waitFor(() => {
      expect(screen.getByText("Opportunity Poster")).toBeInTheDocument();
      expect(screen.getByText(/Click to select/)).toBeInTheDocument();
    });
  });

  it("validates file extension against allowed formats", async () => {
    stubFetch({
      "/api/v1/media/status": () =>
        jsonResponse({
          enabled: true,
          cloud_name: "test-cloud",
          max_file_size_bytes: 10485760,
          allowed_formats: ["jpg", "jpeg", "png"],
        }),
    });

    render(<MediaUploadWidget purpose="opportunity_poster" label="Poster" />);

    await waitFor(() => {
      expect(screen.getByText(/Click to select/)).toBeInTheDocument();
    });

    const fileInput = screen.getByTestId("media-file-input");
    const invalidFile = new File(["fake-exe-content"], "malicious.exe", {
      type: "application/x-msdownload",
    });

    fireEvent.change(fileInput, { target: { files: [invalidFile] } });

    await waitFor(() => {
      expect(screen.getByText(/File type \.exe is not supported/)).toBeInTheDocument();
    });
  });

  it("renders existing image and supports removal", async () => {
    stubFetch({
      "/api/v1/media/status": () =>
        jsonResponse({
          enabled: true,
          cloud_name: "test-cloud",
          max_file_size_bytes: 10485760,
          allowed_formats: ["jpg", "jpeg", "png"],
        }),
      "/api/v1/institutions/inst-123/opportunities/opp-456/poster": () =>
        jsonResponse({ ok: true }),
    });

    const user = userEvent.setup();
    const onDelete = vi.fn();
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(
      <MediaUploadWidget
        purpose="opportunity_poster"
        institutionId="inst-123"
        opportunityId="opp-456"
        currentImageUrl="https://res.cloudinary.com/test-cloud/image/upload/v1/poster.jpg"
        label="Opportunity Poster"
        onDeleteSuccess={onDelete}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Remove attached image/i })).toBeInTheDocument();
    });

    const removeBtn = screen.getByRole("button", { name: /Remove attached image/i });
    await user.click(removeBtn);

    await waitFor(() => {
      expect(onDelete).toHaveBeenCalled();
      expect(screen.getByText("Image removed.")).toBeInTheDocument();
    });
  });
});
