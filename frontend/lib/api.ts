import type {
  BoardMeetingDetail,
  BoardMeetingResult,
  DashboardSnapshot,
  GlobalSearchResults,
  MeetingSummary,
  StartupBriefPayload,
  StartupIdea,
  StartupIdeaGenerationPayload
} from "@/lib/types";

const API_PREFIX = "/api/v1";
const DEFAULT_WS_BASE_URL = "ws://localhost:8000";

const API_BASE_URL = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);

function normalizeBaseUrl(value: string | undefined) {
  const trimmed = value?.trim() ?? "";
  return trimmed.replace(/\/+$/, "");
}

function apiUrl(path: string) {
  return `${API_BASE_URL}${path}`;
}

async function requestJson<T>(
  path: string,
  init: RequestInit | undefined,
  context: string
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), init);
  } catch (error) {
    throw new Error(
      `${context}: unable to reach API at ${apiUrl(path)}${
        error instanceof Error ? ` (${error.message})` : ""
      }`
    );
  }

  if (!response.ok) {
    throw new Error(
      `${context}: ${response.status} ${response.statusText}${await errorDetail(response)}`
    );
  }

  return response.json() as Promise<T>;
}

async function requestNoContent(
  path: string,
  init: RequestInit | undefined,
  context: string
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), init);
  } catch (error) {
    throw new Error(
      `${context}: unable to reach API at ${apiUrl(path)}${
        error instanceof Error ? ` (${error.message})` : ""
      }`
    );
  }

  if (!response.ok) {
    throw new Error(
      `${context}: ${response.status} ${response.statusText}${await errorDetail(response)}`
    );
  }
}

async function errorDetail(response: Response) {
  const text = await response.text();
  if (!text) {
    return "";
  }

  try {
    const data = JSON.parse(text) as { detail?: unknown };
    if (typeof data.detail === "string") {
      return ` - ${data.detail}`;
    }
  } catch {
    return ` - ${text}`;
  }

  return ` - ${text}`;
}

export async function createBoardMeeting(payload: StartupBriefPayload): Promise<BoardMeetingResult> {
  return requestJson<BoardMeetingResult>(
    `${API_PREFIX}/board-meetings`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    },
    "Board meeting failed"
  );
}

export async function generateStartupIdeas(
  payload: StartupIdeaGenerationPayload
): Promise<StartupIdea[]> {
  const data = await requestJson<{ ideas: StartupIdea[] }>(
    `${API_PREFIX}/startup-ideas/generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    },
    "Startup idea generation failed"
  );
  return data.ideas;
}

export async function fetchDashboard(): Promise<DashboardSnapshot> {
  return requestJson<DashboardSnapshot>(
    `${API_PREFIX}/dashboard`,
    {
      cache: "no-store"
    },
    "Dashboard failed to load"
  );
}

export async function fetchMeetings(options?: {
  query?: string;
  favoriteOnly?: boolean;
  limit?: number;
}): Promise<MeetingSummary[]> {
  const params = new URLSearchParams();
  if (options?.query) {
    params.set("q", options.query);
  }
  if (options?.favoriteOnly) {
    params.set("favorite_only", "true");
  }
  if (options?.limit) {
    params.set("limit", String(options.limit));
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const data = await requestJson<{ meetings: MeetingSummary[] }>(
    `${API_PREFIX}/board-meetings${suffix}`,
    {
      cache: "no-store"
    },
    "Meeting history failed to load"
  );
  return data.meetings;
}

export async function fetchMeetingDetail(meetingId: string): Promise<BoardMeetingDetail> {
  return requestJson<BoardMeetingDetail>(
    `${API_PREFIX}/board-meetings/${meetingId}`,
    {
      cache: "no-store"
    },
    "Meeting report failed to load"
  );
}

export async function updateMeetingFavorite(meetingId: string, isFavorite: boolean) {
  return requestJson<{ meeting_id: string; is_favorite: boolean }>(
    `${API_PREFIX}/board-meetings/${meetingId}/favorite`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ is_favorite: isFavorite })
    },
    "Favorite update failed"
  );
}

export async function deleteMeeting(meetingId: string) {
  await requestNoContent(
    `${API_PREFIX}/board-meetings/${meetingId}`,
    {
      method: "DELETE"
    },
    "Meeting delete failed"
  );
}

export async function searchEverything(query: string): Promise<GlobalSearchResults> {
  const params = new URLSearchParams({ q: query });
  return requestJson<GlobalSearchResults>(
    `${API_PREFIX}/search?${params.toString()}`,
    {
      cache: "no-store"
    },
    "Search failed"
  );
}

export function reportExportUrl(
  meetingId: string,
  format: "pdf" | "markdown" | "json" = "pdf"
) {
  const params = new URLSearchParams({ format });
  return apiUrl(`${API_PREFIX}/reports/${meetingId}/export?${params.toString()}`);
}

export function boardMeetingWebSocketUrl() {
  const configuredWsBase = normalizeBaseUrl(process.env.NEXT_PUBLIC_WS_BASE_URL);

  if (configuredWsBase) {
    return websocketUrlFromBase(configuredWsBase);
  }

  if (API_BASE_URL) {
    return websocketUrlFromBase(API_BASE_URL);
  }

  if (typeof window !== "undefined") {
    const base = new URL(window.location.origin);
    if (base.hostname === "localhost" || base.hostname === "127.0.0.1") {
      base.port = "8000";
    }
    return websocketUrlFromBase(base.toString());
  }

  return websocketUrlFromBase(DEFAULT_WS_BASE_URL);
}

function websocketUrlFromBase(value: string) {
  const base =
    typeof window === "undefined" ? new URL(value) : new URL(value, window.location.origin);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  base.pathname = `${API_PREFIX}/board-meetings/live`;
  base.search = "";
  return base.toString();
}
