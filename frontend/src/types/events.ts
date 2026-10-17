/** Subset of backend `EventRead` the Phase 1 interface uses. */
export interface EventSummary {
  id: string;
  event_name: string | null;
  organizer: string | null;
}

export interface EventList {
  items: EventSummary[];
  total: number;
  limit: number;
  offset: number;
}
