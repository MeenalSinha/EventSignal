/** Help offer and connection request types for Phase 6. */

export type HelpOfferStatus = "draft" | "active" | "paused" | "archived";
export type HelpOfferAudience = "all_students" | "undergrads" | "seniors" | "alumni_peers";
export type HelpOfferDeliveryMode = "virtual" | "in_person" | "async";

export interface HelpOffer {
  id: string;
  institution_id: string;
  user_id: string;
  title: string;
  category: string;
  description: string;
  topics: string[];
  target_audience: HelpOfferAudience;
  delivery_mode: HelpOfferDeliveryMode;
  capacity_per_month: number;
  status: HelpOfferStatus;
  creator_name?: string | null;
  creator_role?: string | null;
  created_at: string;
  updated_at: string;
}

export interface HelpOfferListResponse {
  total: number;
  items: HelpOffer[];
  categories: string[];
}

export interface ConnectionRequest {
  id: string;
  institution_id: string;
  help_offer_id: string;
  sender_id: string;
  recipient_id: string;
  message: string;
  status: "pending" | "accepted" | "declined" | "expired";
  created_at: string;
  updated_at: string;
}
