import type { EventList, EventSummary } from "../types/events";
import { requestJson } from "./apiClient";
import { invalid, isNullableString, isObject } from "./validation";

export const EVENTS_PATH = "/api/v1/events";

function parseEvent(value: unknown): EventSummary {
  if (
    !isObject(value) ||
    typeof value.id !== "string" ||
    !isNullableString(value.organizer)
  ) {
    throw invalid("event record");
  }
  const rawEventName = isNullableString(value.event_name) ? value.event_name : null;
  const rawTitle = isNullableString(value.title) ? value.title : null;
  const name = rawEventName ?? rawTitle;

  return { id: value.id, event_name: name, title: name, organizer: value.organizer };
}

export function parseEventList(body: unknown): EventList {
  if (
    !isObject(body) ||
    !Array.isArray(body.items) ||
    typeof body.total !== "number" ||
    typeof body.limit !== "number" ||
    typeof body.offset !== "number"
  ) {
    throw invalid("event list");
  }
  return { items: body.items.map(parseEvent), total: body.total, limit: body.limit, offset: body.offset };
}

export async function fetchEvents(signal?: AbortSignal): Promise<EventList> {
  const { body } = await requestJson(EVENTS_PATH, signal ? { signal } : {});
  return parseEventList(body);
}
