import type {
  AuthConfig,
  AuthMode,
  AuthSession,
  BoardMeetingDetail,
  BoardMeetingResult,
  BusinessAnalysisPayload,
  BusinessAnalysisResult,
  BusinessAnalysisSummary,
  BusinessProviderStatus,
  DashboardSnapshot,
  EnterpriseDashboard,
  GlobalSearchResults,
  MeetingSummary,
  StartupBriefPayload,
  StartupIdea,
  StartupIdeaGenerationPayload
} from "@/lib/types";

const API_PREFIX = "/api/v1";
const DEFAULT_WS_BASE_URL = "ws://localhost:8000";

const API_BASE_URL = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);

class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly statusText: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

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
    throw new ApiError(
      `${context}: ${response.status} ${response.statusText}${await errorDetail(response)}`,
      response.status,
      response.statusText
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
    throw new ApiError(
      `${context}: ${response.status} ${response.statusText}${await errorDetail(response)}`,
      response.status,
      response.statusText
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

function isApiStatus(error: unknown, status: number) {
  return error instanceof ApiError && error.status === status;
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

export async function fetchEnterpriseDashboard(): Promise<EnterpriseDashboard> {
  try {
    return await requestJson<EnterpriseDashboard>(
      `${API_PREFIX}/enterprise/dashboard`,
      {
        cache: "no-store"
      },
      "Enterprise workspace failed to load"
    );
  } catch (error) {
    if (isApiStatus(error, 404)) {
      return fetchEnterpriseDashboardFallback();
    }
    throw error;
  }
}

export async function fetchAuthConfig(): Promise<AuthConfig> {
  return requestJson<AuthConfig>(
    `${API_PREFIX}/auth/config`,
    {
      cache: "no-store",
      credentials: "include"
    },
    "Authentication config failed to load"
  );
}

export async function fetchAuthSession(): Promise<{
  authenticated: boolean;
  session: AuthSession | null;
  capabilities: Record<string, unknown>;
}> {
  return requestJson<{
    authenticated: boolean;
    session: AuthSession | null;
    capabilities: Record<string, unknown>;
  }>(
    `${API_PREFIX}/auth/session`,
    {
      cache: "no-store",
      credentials: "include"
    },
    "Authentication session failed to load"
  );
}

export async function createAuthSession(payload: {
  mode: AuthMode;
  email?: string;
}): Promise<AuthSession> {
  return requestJson<AuthSession>(
    `${API_PREFIX}/auth/session`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify(payload)
    },
    "Authentication failed"
  );
}

export async function logoutAuthSession(): Promise<void> {
  await requestNoContent(
    `${API_PREFIX}/auth/logout`,
    {
      method: "POST",
      credentials: "include"
    },
    "Logout failed"
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

async function fetchEnterpriseDashboardFallback(): Promise<EnterpriseDashboard> {
  const [dashboard, meetings] = await Promise.all([
    fetchDashboard(),
    fetchMeetings({ limit: 40 })
  ]);
  const now = new Date().toISOString();
  const completedMeetings = meetings.filter((meeting) => meeting.status === "completed").length;
  const recentMeetings = dashboard.recent_meetings.length ? dashboard.recent_meetings : meetings.slice(0, 8);

  return {
    organization: {
      id: "legacy-default-organization",
      name: "Default Organization",
      slug: "default",
      status: "compatibility",
      default_locale: "en",
      created_at: now
    },
    departments: ["Marketing", "Finance", "HR", "Operations", "Product"].map((name) => ({
      id: `legacy-${name.toLowerCase()}`,
      name,
      status: "active"
    })),
    teams: [
      ["Executive Team", "Operations"],
      ["Finance Review", "Finance"],
      ["Product Council", "Product"],
      ["Marketing Strategy", "Marketing"],
      ["People Operations", "HR"]
    ].map(([name, department]) => ({
      id: `legacy-${name.toLowerCase().replace(/\s+/g, "-")}`,
      name,
      department,
      status: "active"
    })),
    users: [
      {
        id: "legacy-owner",
        display_name: "Workspace Owner",
        email: "owner@boardroom.local",
        role: "Administrator",
        status: "active"
      }
    ],
    recent_meetings: recentMeetings,
    pending_approvals: [],
    tasks: [],
    board_activity: recentMeetings.slice(0, 8).map((meeting, index) => ({
      id: `legacy-activity-${meeting.meeting_id}-${index}`,
      action: "meeting.available",
      entity_type: "board_meeting",
      entity_id: meeting.meeting_id,
      created_at: meeting.completed_at ?? meeting.created_at ?? now
    })),
    upcoming_reviews: [],
    analytics: {
      meetings: {
        total: dashboard.total_meetings,
        completed: completedMeetings || dashboard.reports_generated
      },
      decisions: {
        approval_rate: dashboard.approval_rate,
        average_confidence: dashboard.average_confidence
      },
      approval_time_hours: 0,
      success_rate: dashboard.approval_rate,
      evidence_quality: {
        source: "legacy_dashboard_fallback"
      }
    },
    executive_dashboard: {
      acceptance_rate: dashboard.approval_rate,
      confidence_trend: dashboard.average_confidence,
      replay_frequency: 0,
      recommendation_outcomes: dashboard.recent_board_decisions
    }
  };
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

export async function fetchBusinessProviderStatus(): Promise<BusinessProviderStatus> {
  return requestJson<BusinessProviderStatus>(
    `${API_PREFIX}/business-data/providers`,
    {
      cache: "no-store"
    },
    "Business data provider status failed to load"
  );
}

export async function retryBusinessProviders(): Promise<BusinessProviderStatus> {
  return requestJson<BusinessProviderStatus>(
    `${API_PREFIX}/business-data/providers/retry`,
    {
      method: "POST",
      cache: "no-store"
    },
    "Business data provider retry failed"
  );
}

export async function analyzeBusiness(
  payload: BusinessAnalysisPayload
): Promise<BusinessAnalysisResult> {
  return requestJson<BusinessAnalysisResult>(
    `${API_PREFIX}/business-analyses`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    },
    "Business analysis failed"
  );
}

export async function fetchBusinessAnalyses(): Promise<BusinessAnalysisSummary[]> {
  const data = await requestJson<{ analyses: BusinessAnalysisSummary[] }>(
    `${API_PREFIX}/business-analyses`,
    {
      cache: "no-store"
    },
    "Business analysis history failed to load"
  );
  return data.analyses;
}

export async function fetchBusinessAnalysisDetail(
  analysisId: string
): Promise<BusinessAnalysisResult> {
  return requestJson<BusinessAnalysisResult>(
    `${API_PREFIX}/business-analyses/${analysisId}`,
    {
      cache: "no-store"
    },
    "Business decision brief failed to load"
  );
}

export function businessAnalysisExportUrl(
  analysisId: string,
  format: "pdf" | "markdown" | "json" = "pdf"
) {
  const params = new URLSearchParams({ format });
  return apiUrl(`${API_PREFIX}/business-analyses/${analysisId}/export?${params.toString()}`);
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
