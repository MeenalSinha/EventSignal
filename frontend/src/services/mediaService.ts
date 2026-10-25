/** Service for Cloudinary media upload, signature authorization, and record association. */

import type {
  CompleteUploadRequest,
  MediaAsset,
  MediaStatus,
  UploadSignatureRequest,
  UploadSignatureResponse,
} from "../types/media";
import { requestJson, ApiError } from "./apiClient";
import { getAuthHeaders } from "./authService";

function makeHeaders(institutionId?: string | null): Record<string, string> {
  const headers = getAuthHeaders();
  if (institutionId) {
    headers["X-Institution-Id"] = institutionId;
  }
  return headers;
}

/** Check if Cloudinary media integration is enabled on the backend. */
export async function fetchMediaStatus(): Promise<MediaStatus> {
  const { body } = await requestJson("/api/v1/media/status");
  return body as MediaStatus;
}

/** Request upload signature authorization from the backend. */
export async function authorizeMediaUpload(
  params: UploadSignatureRequest
): Promise<UploadSignatureResponse> {
  const { body } = await requestJson("/api/v1/media/authorize-upload", {
    method: "POST",
    headers: makeHeaders(params.institution_id),
    body: params,
  });
  return body as UploadSignatureResponse;
}

export interface CloudinaryUploadResult {
  public_id: string;
  secure_url: string;
  format: string;
  bytes: number;
  width?: number;
  height?: number;
  resource_type: string;
}

/**
 * Upload file directly to Cloudinary using server-generated signature.
 * Cloudinary API secret is never exposed.
 */
export async function uploadFileToCloudinary(
  file: File,
  signatureData: UploadSignatureResponse,
  onProgress?: (progressPercent: number) => void
): Promise<CloudinaryUploadResult> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();

    formData.append("file", file);
    formData.append("api_key", signatureData.api_key);
    formData.append("timestamp", String(signatureData.timestamp));
    formData.append("signature", signatureData.signature);
    formData.append("folder", signatureData.folder);
    formData.append("tags", signatureData.tags);

    if (signatureData.upload_preset) {
      formData.append("upload_preset", signatureData.upload_preset);
    }

    if (onProgress && xhr.upload) {
      xhr.upload.onprogress = (evt) => {
        if (evt.lengthComputable) {
          const percent = Math.round((evt.loaded / evt.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.open("POST", signatureData.upload_url);

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText) as CloudinaryUploadResult;
          resolve(res);
        } catch {
          reject(new ApiError("invalid-response", "Failed to parse Cloudinary response."));
        }
      } else {
        let msg = `Cloudinary upload failed (HTTP ${xhr.status})`;
        try {
          const parsed = JSON.parse(xhr.responseText) as { error?: { message?: string } };
          if (parsed.error?.message) {
            msg = parsed.error.message;
          }
        } catch {
          // fallback to generic message
        }
        reject(new ApiError("http", msg, xhr.status));
      }
    };

    xhr.onerror = () => {
      reject(new ApiError("network", "Failed to connect to Cloudinary upload endpoint."));
    };

    xhr.ontimeout = () => {
      reject(new ApiError("timeout", "Cloudinary upload timed out."));
    };

    xhr.send(formData);
  });
}

/** Complete upload and associate asset with the application record. */
export async function completeMediaUpload(
  payload: CompleteUploadRequest
): Promise<MediaAsset> {
  const { body } = await requestJson("/api/v1/media/complete-upload", {
    method: "POST",
    headers: makeHeaders(payload.institution_id),
    body: payload,
  });
  return body as MediaAsset;
}

/** Delete an uploaded media asset. */
export async function deleteMediaAsset(
  assetId: string,
  institutionId?: string | null
): Promise<{ ok: boolean }> {
  const { body } = await requestJson(`/api/v1/media/${encodeURIComponent(assetId)}`, {
    method: "DELETE",
    headers: makeHeaders(institutionId),
  });
  return body as { ok: boolean };
}

/** Remove an opportunity poster. */
export async function removeOpportunityPoster(
  institutionId: string,
  opportunityId: string
): Promise<{ ok: boolean }> {
  const { body } = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/opportunities/${encodeURIComponent(opportunityId)}/poster`,
    {
      method: "DELETE",
      headers: makeHeaders(institutionId),
    }
  );
  return body as { ok: boolean };
}
