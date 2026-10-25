import React, { useEffect, useRef, useState } from "react";
import type { MediaAsset, MediaStatus } from "../types/media";
import {
  authorizeMediaUpload,
  completeMediaUpload,
  deleteMediaAsset,
  fetchMediaStatus,
  removeOpportunityPoster,
  uploadFileToCloudinary,
} from "../services/mediaService";

export interface MediaUploadWidgetProps {
  purpose: "opportunity_poster" | "event_memory" | "handover_artifact" | "profile_avatar" | "general_media";
  institutionId?: string | null | undefined;
  opportunityId?: string | null | undefined;
  eventMemoryId?: string | null | undefined;
  legacyHandoverId?: string | null | undefined;
  currentImageUrl?: string | null | undefined;
  currentAssetId?: string | null | undefined;
  onUploadSuccess?: ((asset: MediaAsset) => void) | undefined;
  onDeleteSuccess?: (() => void) | undefined;
  disabled?: boolean | undefined;
  label?: string | undefined;
  helperText?: string | undefined;
  compact?: boolean | undefined;
  canDelete?: boolean | undefined;
}

export const MediaUploadWidget: React.FC<MediaUploadWidgetProps> = ({
  purpose,
  institutionId,
  opportunityId,
  eventMemoryId,
  legacyHandoverId,
  currentImageUrl,
  currentAssetId,
  onUploadSuccess,
  onDeleteSuccess,
  disabled = false,
  label = "Upload Media / Poster",
  helperText = "Supported formats: PNG, JPG, WebP, GIF (up to 10MB)",
  compact = false,
  canDelete = true,
}) => {
  const [status, setStatus] = useState<MediaStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(currentImageUrl ?? null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Sync preview if currentImageUrl changes externally
  const [prevImageUrl, setPrevImageUrl] = useState(currentImageUrl);
  if (currentImageUrl !== prevImageUrl) {
    setPrevImageUrl(currentImageUrl);
    if (!selectedFile) {
      setPreviewUrl(currentImageUrl ?? null);
    }
  }

  // Check Cloudinary feature status on mount
  useEffect(() => {
    let active = true;
    fetchMediaStatus()
      .then((s) => {
        if (active) {
          setStatus(s);
          setStatusLoading(false);
        }
      })
      .catch(() => {
        if (active) {
          // If status endpoint fails, assume media is disabled
          setStatus({
            enabled: false,
            cloud_name: null,
            max_file_size_bytes: 10485760,
            allowed_formats: ["jpg", "jpeg", "png", "webp", "gif"],
          });
          setStatusLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const allowedFormats = status?.allowed_formats ?? ["jpg", "jpeg", "png", "webp", "gif"];
  const maxBytes = status?.max_file_size_bytes ?? 10485760;

  const validateFile = (file: File): string | null => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !allowedFormats.includes(ext)) {
      return `File type .${ext ?? "unknown"} is not supported. Allowed: ${allowedFormats.join(", ")}`;
    }
    if (file.size > maxBytes) {
      const maxMb = Math.round(maxBytes / (1024 * 1024));
      return `File size (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds limit of ${maxMb}MB.`;
    }
    if (file.size === 0) {
      return "Cannot upload an empty file.";
    }
    return null;
  };

  const handleFileSelect = (file: File) => {
    setError(null);
    setSuccessMsg(null);

    const validationErr = validateFile(file);
    if (validationErr) {
      setError(validationErr);
      return;
    }

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled || uploading || status?.enabled === false) return;
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const handleStartUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setProgress(0);
    setError(null);
    setSuccessMsg(null);

    try {
      // 1. Authorize upload with backend
      const sigData = await authorizeMediaUpload({
        purpose,
        institution_id: institutionId,
        opportunity_id: opportunityId,
        event_memory_id: eventMemoryId,
        legacy_handover_id: legacyHandoverId,
      });

      // 2. Upload directly to Cloudinary with progress tracking
      const cldResult = await uploadFileToCloudinary(selectedFile, sigData, (pct) => {
        setProgress(pct);
      });

      // 3. Complete and associate with backend
      const asset = await completeMediaUpload({
        cloudinary_public_id: cldResult.public_id,
        resource_type: cldResult.resource_type || "image",
        delivery_url: cldResult.secure_url,
        format: cldResult.format,
        bytes: cldResult.bytes,
        width: cldResult.width,
        height: cldResult.height,
        purpose,
        institution_id: institutionId,
        opportunity_id: opportunityId,
        event_memory_id: eventMemoryId,
        legacy_handover_id: legacyHandoverId,
      });

      setSelectedFile(null);
      setPreviewUrl(asset.optimized_url || asset.delivery_url);
      setSuccessMsg("Image uploaded and associated successfully!");
      if (onUploadSuccess) {
        onUploadSuccess(asset);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed.";
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    if (disabled || isDeleting) return;
    if (!confirm("Are you sure you want to remove this image?")) return;

    setIsDeleting(true);
    setError(null);
    try {
      if (purpose === "opportunity_poster" && institutionId && opportunityId) {
        await removeOpportunityPoster(institutionId, opportunityId);
      } else if (currentAssetId) {
        await deleteMediaAsset(currentAssetId, institutionId);
      }
      setPreviewUrl(null);
      setSelectedFile(null);
      setSuccessMsg("Image removed.");
      if (onDeleteSuccess) {
        onDeleteSuccess();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to remove image.";
      setError(msg);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCancelSelection = () => {
    setSelectedFile(null);
    setPreviewUrl(currentImageUrl ?? null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  if (statusLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 text-center text-xs text-slate-500">
        Checking media configuration...
      </div>
    );
  }

  // Graceful degradation when Cloudinary is disabled
  if (status && !status.enabled) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-4 text-center">
        <p className="text-sm font-medium text-slate-700">{label}</p>
        <p className="mt-1 text-xs text-slate-500">
          Cloudinary media storage is currently not configured or disabled on this server.
          Non-media workflows operate normally.
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${compact ? "text-sm" : ""}`}>
      <div className="flex items-center justify-between">
        <label className="block text-sm font-semibold text-slate-800" id={`upload-label-${purpose}`}>
          {label}
        </label>
        {previewUrl && canDelete && !uploading && (
          <button
            type="button"
            onClick={handleDelete}
            disabled={disabled || isDeleting}
            className="text-xs font-medium text-rose-600 hover:text-rose-700 disabled:opacity-50"
            aria-label="Remove attached image"
          >
            {isDeleting ? "Removing..." : "Remove Image"}
          </button>
        )}
      </div>

      {/* Preview or Drop Area */}
      {previewUrl ? (
        <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-slate-900/5 group shadow-inner">
          <img
            src={previewUrl}
            alt="Media preview"
            className={`w-full object-cover ${compact ? "h-36" : "h-52"} transition group-hover:opacity-95`}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent flex items-end p-3 opacity-90">
            <div className="flex w-full items-center justify-between text-white text-xs">
              <span className="font-medium truncate max-w-[70%]">
                {selectedFile ? selectedFile.name : "Optimized Cloudinary Asset"}
              </span>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled || uploading}
                className="rounded-lg bg-white/20 backdrop-blur-xs px-2.5 py-1 hover:bg-white/30 font-medium transition"
              >
                Change
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/80 p-6 text-center hover:border-teal-500 hover:bg-teal-50/20 transition cursor-pointer"
          role="button"
          tabIndex={0}
          aria-labelledby={`upload-label-${purpose}`}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-teal-100 text-teal-700">
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
          <p className="mt-2 text-sm font-medium text-slate-700">
            <span className="text-teal-700 underline font-semibold">Click to select</span> or drag and drop
          </p>
          <p className="mt-1 text-xs text-slate-500">{helperText}</p>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        data-testid="media-file-input"
        accept={allowedFormats.map((f) => `.${f}`).join(",")}
        onChange={handleInputChange}
        className="hidden"
        disabled={disabled || uploading}
        aria-label={label}
      />

      {/* Staged file action bar */}
      {selectedFile && (
        <div className="flex items-center justify-between rounded-xl bg-teal-50 p-3 border border-teal-200 text-xs">
          <div className="flex items-center space-x-2 truncate">
            <span className="font-semibold text-teal-900 truncate">{selectedFile.name}</span>
            <span className="text-teal-600">({(selectedFile.size / 1024).toFixed(0)} KB)</span>
          </div>
          <div className="flex space-x-2 shrink-0">
            <button
              type="button"
              onClick={handleCancelSelection}
              disabled={uploading}
              className="px-2.5 py-1 text-slate-600 hover:text-slate-800 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleStartUpload}
              disabled={uploading}
              className="rounded-lg bg-teal-700 px-3 py-1 font-medium text-white hover:bg-teal-800 disabled:opacity-50 shadow-2xs"
            >
              {uploading ? "Uploading..." : "Upload & Save"}
            </button>
          </div>
        </div>
      )}

      {/* Upload Progress Bar */}
      {uploading && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs font-medium text-slate-600">
            <span>Uploading to Cloudinary...</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full bg-teal-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Feedback alerts */}
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-700 flex items-center justify-between">
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-rose-500 hover:text-rose-700 font-bold ml-2"
          >
            ×
          </button>
        </div>
      )}

      {successMsg && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-2.5 text-xs text-emerald-800">
          {successMsg}
        </div>
      )}
    </div>
  );
};
