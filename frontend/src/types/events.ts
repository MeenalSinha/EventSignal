export interface EventSummary {
  id: string;
  event_name?: string | null;
  title?: string | null;
  organizer: string | null;
}

export interface EventList {
  items: EventSummary[];
  total: number;
  limit: number;
  offset: number;
}
