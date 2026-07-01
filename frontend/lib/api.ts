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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function createBoardMeeting(payload: StartupBriefPayload): Promise<BoardMeetingResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/board-meetings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Board meeting failed");
  }

  return response.json() as Promise<BoardMeetingResult>;
}

export async function generateStartupIdeas(
  payload: StartupIdeaGenerationPayload
): Promise<StartupIdea[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/startup-ideas/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Startup idea generation failed");
  }

  const data = (await response.json()) as { ideas: StartupIdea[] };
  return data.ideas;
}

export async function fetchDashboard(): Promise<DashboardSnapshot> {
  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Dashboard failed to load");
  }

  return response.json() as Promise<DashboardSnapshot>;
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
  const response = await fetch(`${API_BASE_URL}/api/v1/board-meetings${suffix}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Meeting history failed to load");
  }

  const data = (await response.json()) as { meetings: MeetingSummary[] };
  return data.meetings;
}

export async function fetchMeetingDetail(meetingId: string): Promise<BoardMeetingDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/board-meetings/${meetingId}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Meeting report failed to load");
  }

  return response.json() as Promise<BoardMeetingDetail>;
}

export async function updateMeetingFavorite(meetingId: string, isFavorite: boolean) {
  const response = await fetch(`${API_BASE_URL}/api/v1/board-meetings/${meetingId}/favorite`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ is_favorite: isFavorite })
  });

  if (!response.ok) {
    throw new Error("Favorite update failed");
  }

  return response.json() as Promise<{ meeting_id: string; is_favorite: boolean }>;
}

export async function deleteMeeting(meetingId: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/board-meetings/${meetingId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error("Meeting delete failed");
  }
}

export async function searchEverything(query: string): Promise<GlobalSearchResults> {
  const params = new URLSearchParams({ q: query });
  const response = await fetch(`${API_BASE_URL}/api/v1/search?${params.toString()}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Search failed");
  }

  return response.json() as Promise<GlobalSearchResults>;
}

export function reportExportUrl(
  meetingId: string,
  format: "pdf" | "markdown" | "json" = "pdf"
) {
  const params = new URLSearchParams({ format });
  return `${API_BASE_URL}/api/v1/reports/${meetingId}/export?${params.toString()}`;
}

export function boardMeetingWebSocketUrl() {
  const base = new URL(API_BASE_URL);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  base.pathname = "/api/v1/board-meetings/live";
  base.search = "";
  return base.toString();
}
