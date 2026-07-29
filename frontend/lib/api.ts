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
  EnterpriseAssistantAnswer,
  EnterpriseDashboard,
  EnterpriseDocumentImportPayload,
  EnterpriseDocumentImportResult,
  EnterpriseIntelligenceSuite,
  EnterpriseWorkflowRunPayload,
  EnterpriseWorkflowRunResult,
  GlobalEnterpriseSearchResults,
  GlobalSearchResults,
  MeetingSummary,
  OperationsJob,
  OperationsJobStats,
  OperationsJobType,
  OperationsJobsResponse,
  OperationsMonitoringSnapshot,
  OperationsPluginManifest,
  OperationsSchedulesResponse,
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

export async function fetchEnterpriseIntelligenceSuite(): Promise<EnterpriseIntelligenceSuite> {
  try {
    return await requestJson<EnterpriseIntelligenceSuite>(
      `${API_PREFIX}/enterprise/intelligence-suite`,
      {
        cache: "no-store"
      },
      "Enterprise intelligence failed to load"
    );
  } catch (error) {
    if (isApiStatus(error, 404)) {
      return fetchEnterpriseIntelligenceFallback();
    }
    throw error;
  }
}

export async function askEnterpriseAssistant(
  question: string
): Promise<EnterpriseAssistantAnswer> {
  const data = await requestJson<{ answer: EnterpriseAssistantAnswer }>(
    `${API_PREFIX}/enterprise/assistant`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question })
    },
    "Enterprise assistant failed"
  );
  return data.answer;
}

export async function importEnterpriseDocument(
  payload: EnterpriseDocumentImportPayload
): Promise<EnterpriseDocumentImportResult> {
  return requestJson<EnterpriseDocumentImportResult>(
    `${API_PREFIX}/documents/import`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    },
    "Document import failed"
  );
}

export async function runEnterpriseWorkflow(
  payload: EnterpriseWorkflowRunPayload
): Promise<EnterpriseWorkflowRunResult> {
  return requestJson<EnterpriseWorkflowRunResult>(
    `${API_PREFIX}/workflows/run`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    },
    "Workflow automation failed"
  );
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
  const recentMeetings = dashboard.recent_meetings.length
    ? dashboard.recent_meetings
    : meetings.slice(0, 8);

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

async function fetchEnterpriseIntelligenceFallback(): Promise<EnterpriseIntelligenceSuite> {
  const dashboard = await fetchEnterpriseDashboard();
  const recentMeetings = dashboard.recent_meetings ?? [];
  const now = new Date().toISOString();
  const nodes = [
    {
      id: "organization:legacy-default-organization",
      type: "organization",
      label: String(dashboard.organization.name ?? "Default Organization")
    },
    ...recentMeetings.slice(0, 12).map((meeting) => ({
      id: `meeting:${meeting.meeting_id}`,
      type: "board_meeting",
      label: meeting.startup_idea,
      metadata: {
        decision: meeting.decision,
        confidence: meeting.aggregate_confidence
      }
    }))
  ];
  const edges = recentMeetings.slice(0, 12).map((meeting) => ({
    id: `organization:legacy-default-organization:owns_decision:meeting:${meeting.meeting_id}`,
    source: "organization:legacy-default-organization",
    target: `meeting:${meeting.meeting_id}`,
    relationship: "owns_decision"
  }));

  return {
    memory: {
      organization_id: dashboard.organization.id,
      executive_memory: [],
      decision_history: {
        total: recentMeetings.length,
        approved_or_conditionally_approved: recentMeetings.filter((meeting) =>
          ["approve", "approve_with_conditions"].includes(meeting.decision)
        ).length,
        rejected_or_deferred: recentMeetings.filter((meeting) =>
          meeting.decision.startsWith("reject") || meeting.decision.startsWith("defer")
        ).length,
        recent: recentMeetings
      },
      confidence_history: recentMeetings.map((meeting) => ({
        meeting_id: meeting.meeting_id,
        confidence: meeting.aggregate_confidence,
        decision: meeting.decision,
        date: meeting.completed_at ?? meeting.created_at
      })),
      generated_at: now
    },
    knowledge_graph: {
      organization_id: dashboard.organization.id,
      nodes,
      edges,
      counts: {
        nodes: nodes.length,
        edges: edges.length,
        meetings: recentMeetings.length,
        business_analyses: 0,
        knowledge_items: 0
      },
      generated_at: now
    },
    analytics: {
      analytics: dashboard.analytics,
      executive_dashboard: dashboard.executive_dashboard,
      meeting_effectiveness: {
        total_meetings: recentMeetings.length,
        completed_meetings: recentMeetings.filter((meeting) => meeting.status === "completed")
          .length,
        average_confidence: dashboard.analytics.average_confidence ?? 0
      },
      department_scorecards: {
        open_tasks: dashboard.tasks.length,
        tasks_by_status: {}
      }
    },
    assistant_suggestions: [
      {
        title: "Upgrade backend for full intelligence suite",
        reason: "The current API is serving the compatibility enterprise dashboard.",
        action: "Use the RC5 backend routes for memory, graph, assistant, and workflows.",
        priority: "medium"
      }
    ],
    collaboration: {
      active_users: dashboard.users,
      meeting_collaborators: [],
      recent_comments: [],
      notifications: []
    },
    observability: {
      database: {
        source: "frontend_compatibility_fallback"
      },
      provider_health: [],
      recent_errors: [],
      generated_at: now
    },
    workflows: {
      available_triggers: ["manual"],
      available_actions: ["assign_tasks", "notify_executives", "update_dashboard"],
      email_ready: true,
      desktop_ready: true
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

export async function fetchGlobalEnterpriseSearch(
  query: string
): Promise<GlobalEnterpriseSearchResults> {
  const params = new URLSearchParams({ q: query });
  try {
    return await requestJson<GlobalEnterpriseSearchResults>(
      `${API_PREFIX}/search/global?${params.toString()}`,
      {
        cache: "no-store"
      },
      "Enterprise search failed"
    );
  } catch (error) {
    if (!isApiStatus(error, 404)) {
      throw error;
    }
    const fallback = await searchEverything(query);
    const collections = {
      meetings: fallback.meetings,
      reports: fallback.reports,
      executives: fallback.executives
    };
    return {
      ...fallback,
      collections,
      items: Object.entries(collections).flatMap(([collection, items]) =>
        items.map((item) => ({ collection, ...item }))
      ),
      total: fallback.meetings.length + fallback.reports.length + fallback.executives.length
    };
  }
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

export async function fetchOperationsMonitoring(): Promise<OperationsMonitoringSnapshot> {
  try {
    return await requestJson<OperationsMonitoringSnapshot>(
      `${API_PREFIX}/operations/monitoring`,
      {
        cache: "no-store",
        headers: {
          "X-Boardroom-Role": "Administrator"
        }
      },
      "Operations monitoring failed to load"
    );
  } catch (error) {
    if (isApiStatus(error, 404)) {
      return fetchOperationsMonitoringFallback();
    }
    throw error;
  }
}

export async function fetchOperationsJobs(limit = 20): Promise<OperationsJobsResponse> {
  try {
    return await requestJson<OperationsJobsResponse>(
      `${API_PREFIX}/operations/jobs?limit=${limit}`,
      {
        cache: "no-store",
        headers: {
          "X-Boardroom-Role": "Administrator"
        }
      },
      "Operations jobs failed to load"
    );
  } catch (error) {
    if (isApiStatus(error, 404)) {
      return {
        jobs: [],
        stats: operationsJobStatsFallback()
      };
    }
    throw error;
  }
}

export async function createOperationsJob(
  jobType: OperationsJobType,
  payload: Record<string, unknown> = {}
): Promise<OperationsJob> {
  const data = await requestJson<{ job: OperationsJob }>(
    `${API_PREFIX}/operations/jobs`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Boardroom-Role": "Administrator"
      },
      body: JSON.stringify({
        job_type: jobType,
        payload
      })
    },
    "Operations job creation failed"
  );
  return data.job;
}

export async function fetchOperationsSchedules(
  limit = 20
): Promise<OperationsSchedulesResponse> {
  try {
    return await requestJson<OperationsSchedulesResponse>(
      `${API_PREFIX}/operations/schedules?limit=${limit}`,
      {
        cache: "no-store",
        headers: {
          "X-Boardroom-Role": "Administrator"
        }
      },
      "Operations schedules failed to load"
    );
  } catch (error) {
    if (isApiStatus(error, 404)) {
      return { schedules: [] };
    }
    throw error;
  }
}

export async function fetchOperationsPlugins(): Promise<OperationsPluginManifest> {
  try {
    return await requestJson<OperationsPluginManifest>(
      `${API_PREFIX}/operations/plugins`,
      {
        cache: "no-store",
        headers: {
          "X-Boardroom-Role": "Administrator"
        }
      },
      "Operations plugins failed to load"
    );
  } catch (error) {
    if (isApiStatus(error, 404)) {
      return {
        generated_at: new Date().toISOString(),
        plugin_types: [],
        plugins: [],
        counts: {}
      };
    }
    throw error;
  }
}

async function fetchOperationsMonitoringFallback(): Promise<OperationsMonitoringSnapshot> {
  const providers = await fetchBusinessProviderStatus();
  const now = new Date().toISOString();
  return {
    generated_at: now,
    api: {
      started_at: now,
      uptime_seconds: 0,
      request_count: 0,
      active_requests: 0,
      status_counts: {},
      latency_ms: {
        count: 0,
        average: 0,
        p95: 0,
        max: 0
      }
    },
    process: {
      platform: "compatibility",
      memory_bytes: {}
    },
    active_users: 1,
    dependencies: {
      api: {
        status: "compatibility",
        note: "Operations endpoints are unavailable on this backend."
      },
      redis: {
        status: "unknown"
      },
      qdrant: {
        status: "unknown"
      },
      database: {
        status: "unknown"
      }
    },
    providers,
    jobs: operationsJobStatsFallback(),
    cache: {
      backend: "memory",
      status: "compatibility"
    }
  };
}

function operationsJobStatsFallback(): OperationsJobStats {
  return {
    backend: "memory",
    counts: {
      queued: 0,
      running: 0,
      completed: 0,
      failed: 0,
      canceled: 0,
      dead_letter: 0
    },
    queue_size: 0,
    dead_letter_size: 0,
    supported_job_types: [
      "report_generation",
      "scheduled_workflow",
      "provider_sync",
      "document_processing",
      "email_delivery",
      "analytics_refresh",
      "scheduled_export"
    ]
  };
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
