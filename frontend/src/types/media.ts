/** Media and Cloudinary integration types. */

export interface MediaAsset {
  id: string;
  cloudinary_public_id: string;
  resource_type: string;
  delivery_url: string;
  optimized_url?: string | null | undefined;
  thumbnail_url?: string | null | undefined;
  format: string;
  bytes: number;
  width?: number | null | undefined;
  height?: number | null | undefined;
  alt_text?: string | null | undefined;
  caption?: string | null | undefined;
  purpose: string;
  institution_id?: string | null | undefined;
  uploaded_by_user_id?: string | null | undefined;
  opportunity_id?: string | null | undefined;
  event_memory_id?: string | null | undefined;
  legacy_handover_id?: string | null | undefined;
  created_at: string;
}

export interface UploadSignatureRequest {
  purpose: "opportunity_poster" | "event_memory" | "handover_artifact" | "profile_avatar" | "general_media";
  institution_id?: string | null | undefined;
  opportunity_id?: string | null | undefined;
  event_memory_id?: string | null | undefined;
  legacy_handover_id?: string | null | undefined;
}

export interface UploadSignatureResponse {
  cloud_name: string;
  api_key: string;
  timestamp: number;
  signature: string;
  folder: string;
  upload_preset?: string | null | undefined;
  tags: string;
  allowed_formats: string[];
  max_file_size_bytes: number;
  upload_url: string;
}

export interface CompleteUploadRequest {
  cloudinary_public_id: string;
  resource_type: string;
  delivery_url: string;
  format: string;
  bytes: number;
  width?: number | null | undefined;
  height?: number | null | undefined;
  alt_text?: string | null | undefined;
  caption?: string | null | undefined;
  purpose: string;
  institution_id?: string | null | undefined;
  opportunity_id?: string | null | undefined;
  event_memory_id?: string | null | undefined;
  legacy_handover_id?: string | null | undefined;
}

export interface MediaStatus {
  enabled: boolean;
  cloud_name: string | null;
  max_file_size_bytes: number;
  allowed_formats: string[];
  folder_prefix?: string;
}
