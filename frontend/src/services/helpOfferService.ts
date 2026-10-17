/** Service for help offer management, discovery, and requests. */

import type { ConnectionRequest, HelpOffer, HelpOfferListResponse, HelpOfferStatus } from "../types/helpOffer";
import { requestJson } from "./apiClient";
import { getAuthHeaders } from "./authService";

export async function fetchHelpOffers(
  institutionId: string,
  params?: { category?: string | undefined; query?: string | undefined; skip?: number | undefined; limit?: number | undefined },
): Promise<HelpOfferListResponse> {
  const headers = {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
  const queryParams = new URLSearchParams({ institution_id: institutionId });
  if (params?.category) queryParams.set("category", params.category);
  if (params?.query) queryParams.set("q", params.query);
  if (params?.skip !== undefined) queryParams.set("skip", String(params.skip));
  if (params?.limit !== undefined) queryParams.set("limit", String(params.limit));

  const response = await requestJson(`/api/v1/help-offers/discovery?${queryParams.toString()}`, {
    headers,
  });
  return response.body as HelpOfferListResponse;
}

export async function fetchMyHelpOffers(institutionId: string): Promise<HelpOffer[]> {
  const headers = {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
  const response = await requestJson(`/api/v1/help-offers/me?institution_id=${encodeURIComponent(institutionId)}`, {
    headers,
  });
  return response.body as HelpOffer[];
}

export async function createHelpOffer(institutionId: string, data: Partial<HelpOffer>): Promise<HelpOffer> {
  const headers = {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
  const response = await requestJson(`/api/v1/help-offers?institution_id=${encodeURIComponent(institutionId)}`, {
    method: "POST",
    headers,
    body: data,
  });
  return response.body as HelpOffer;
}

export async function updateHelpOffer(
  institutionId: string,
  offerId: string,
  data: Partial<HelpOffer>,
): Promise<HelpOffer> {
  const headers = {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
  const response = await requestJson(`/api/v1/help-offers/${encodeURIComponent(offerId)}?institution_id=${encodeURIComponent(institutionId)}`, {
    method: "PUT",
    headers,
    body: data,
  });
  return response.body as HelpOffer;
}

export async function updateHelpOfferStatus(
  institutionId: string,
  offerId: string,
  status: HelpOfferStatus,
): Promise<HelpOffer> {
  const headers = {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
  const response = await requestJson(`/api/v1/help-offers/${encodeURIComponent(offerId)}/status?status=${encodeURIComponent(status)}&institution_id=${encodeURIComponent(institutionId)}`, {
    method: "PATCH",
    headers,
  });
  return response.body as HelpOffer;
}

export async function requestHelpOffer(
  institutionId: string,
  offerId: string,
  message: string,
): Promise<ConnectionRequest> {
  const headers = {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
  const response = await requestJson(`/api/v1/help-offers/${encodeURIComponent(offerId)}/request?institution_id=${encodeURIComponent(institutionId)}`, {
    method: "POST",
    headers,
    body: { message },
  });
  return response.body as ConnectionRequest;
}
