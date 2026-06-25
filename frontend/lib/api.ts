import type { BoardMeetingResult, StartupBriefPayload } from "@/lib/types";

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

export function boardMeetingWebSocketUrl() {
  const base = new URL(API_BASE_URL);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  base.pathname = "/api/v1/board-meetings/live";
  base.search = "";
  return base.toString();
}
