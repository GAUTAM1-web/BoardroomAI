export type StartupBriefPayload = {
  startup_idea: string;
  industry: string;
  country: string;
  budget: number;
  timeline_months: number;
  competitors: string[];
  target_audience: string;
  funding_stage: string;
  business_model: string;
  meeting_mode?: string;
};

export type StartupIdeaGenerationPayload = {
  prompt?: string;
  interests?: string;
  industry?: string;
  country?: string;
  budget?: number;
  business_model?: string;
  funding_stage?: string;
  number_of_ideas?: number;
};

export type StartupIdea = {
  startup_name: string;
  tagline: string;
  problem: string;
  solution: string;
  target_audience: string;
  revenue_model: string;
  estimated_startup_cost: number;
  estimated_tam: string;
  innovation_score: number;
  scalability_score: number;
  difficulty: string;
  competitive_advantage: string;
  success_probability: number;
  meeting_brief: StartupBriefPayload;
};

export type MeetingTurn = {
  sequence?: number | null;
  round_number: number;
  speaker_role: string;
  turn_type: string;
  topic?: string | null;
  stance: string;
  confidence: number;
  message: string;
  concerns: string[];
  recommendations: string[];
  reasoning?: string[];
  memory_references?: string[];
  occurred_at?: string | null;
};

export type BoardVote = {
  role: string;
  vote: "approve" | "approve_with_conditions" | "reject" | string;
  confidence: number;
  rationale: string;
};

export type BoardReport = {
  title: string;
  decision: string;
  sections: Record<string, unknown>;
};

export type BoardMeetingResult = {
  meeting_id: string;
  consensus_reached: boolean;
  aggregate_confidence: number;
  decision: string;
  assessment: {
    overall_risk: number;
    risk_scores: Record<string, number>;
    signals: Record<string, string>;
  };
  turns: MeetingTurn[];
  votes: BoardVote[];
  report: BoardReport;
};

export type BoardMeetingDetail = BoardMeetingResult & {
  startup_brief: StartupBriefPayload;
  status: string;
  is_favorite: boolean;
  created_at?: string | null;
  completed_at?: string | null;
};

export type MeetingSummary = {
  meeting_id: string;
  startup_idea: string;
  industry: string;
  country: string;
  decision: string;
  status: string;
  aggregate_confidence: number;
  consensus_reached: boolean;
  is_favorite: boolean;
  created_at?: string | null;
  completed_at?: string | null;
  report_title?: string | null;
};

export type DashboardSnapshot = {
  total_meetings: number;
  reports_generated: number;
  approval_rate: number;
  average_confidence: number;
  top_industries: Array<{ industry: string; count: number }>;
  recent_meetings: MeetingSummary[];
  recent_reports: MeetingSummary[];
  recent_board_decisions: MeetingSummary[];
};

export type EnterpriseDashboard = {
  organization: Record<string, unknown>;
  departments: Array<Record<string, unknown>>;
  teams: Array<Record<string, unknown>>;
  users: Array<Record<string, unknown>>;
  recent_meetings: MeetingSummary[];
  pending_approvals: Array<Record<string, unknown>>;
  tasks: Array<Record<string, unknown>>;
  board_activity: Array<Record<string, unknown>>;
  upcoming_reviews: Array<Record<string, unknown>>;
  analytics: Record<string, unknown>;
  executive_dashboard: Record<string, unknown>;
};

export type EnterpriseIntelligenceSuite = {
  memory: Record<string, unknown>;
  knowledge_graph: Record<string, unknown>;
  analytics: Record<string, unknown>;
  assistant_suggestions: Array<Record<string, unknown>>;
  collaboration: Record<string, unknown>;
  observability: Record<string, unknown>;
  workflows: Record<string, unknown>;
};

export type EnterpriseAssistantAnswer = {
  question: string;
  answer: string;
  source_count: number;
  sources: Array<Record<string, unknown>>;
  recommended_actions: string[];
  limitations: string[];
  generated_at: string;
};

export type EnterpriseDocumentImportPayload = {
  filename: string;
  content_base64: string;
  mime_type?: string;
  meeting_id?: string;
  business_analysis_id?: string;
  tags?: string[];
};

export type EnterpriseDocumentImportResult = {
  document: Record<string, unknown>;
};

export type EnterpriseWorkflowRunPayload = {
  trigger: "meeting.completed" | "business_analysis.created" | "manual";
  meeting_id?: string;
  business_analysis_id?: string;
  actions: string[];
};

export type EnterpriseWorkflowRunResult = {
  workflow: Record<string, unknown>;
};

export type GlobalEnterpriseSearchResults = GlobalSearchResults & {
  collections: Record<string, Array<Record<string, unknown>>>;
  items: Array<Record<string, unknown>>;
  total: number;
};

export type AuthMode = "email" | "demo" | "guest";

export type AuthUser = {
  email: string;
  display_name: string;
  role: string;
  organization: string;
};

export type AuthSession = {
  authenticated: boolean;
  session_id: string;
  mode: AuthMode | string;
  user: AuthUser;
  issued_at: string;
  expires_at: string;
};

export type AuthConfig = {
  email_login: boolean;
  demo_account: boolean;
  guest_mode: boolean;
  session_persistence: boolean;
  oauth_ready: Array<Record<string, unknown>>;
};

export type GlobalSearchResults = {
  query: string;
  meetings: MeetingSummary[];
  reports: Array<{
    meeting_id: string;
    report_id: string;
    title: string;
    section_key: string;
    section_title: string;
    startup_idea: string;
    decision: string;
  }>;
  executives: Array<{
    role: string;
    charter: string;
    personality: string;
    goals: string[];
    risk_focus: string[];
  }>;
};

export type LiveBoardroomEventType =
  | "meeting_started"
  | "executive_status"
  | "confidence_changed"
  | "timeline_statement"
  | "vote_cast"
  | "vote_changed"
  | "vote_confirmed"
  | "report_section"
  | "consensus_reached"
  | "error";

export type LiveBoardroomEvent = {
  event_id?: string;
  meeting_id?: string;
  sequence?: number;
  event_type: LiveBoardroomEventType;
  role?: string | null;
  timestamp?: string;
  payload: Record<string, unknown>;
};

export type ConfidencePoint = {
  sequence: number;
  confidence: number;
  previous_confidence?: number | null;
  delta?: number | null;
  reason: string;
  timestamp?: string;
};

export type LiveVote = BoardVote & {
  previous_vote?: string | null;
  changed?: boolean;
  sequence?: number;
};

export type StreamedReportSection = {
  section_key: string;
  section_title: string;
  content: unknown;
  sequence?: number;
};

export type BusinessDataMode = "demo" | "manual" | "live";

export type BusinessLocationPayload = {
  country?: string;
  state?: string;
  city?: string;
  locality?: string;
  market?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  radius_km: number;
  map_zoom?: number;
  source: "manual" | "browser_permission" | "map_pin" | "search";
};

export type ManualCompetitorPayload = {
  name: string;
  category?: string;
  location_label?: string;
  distance_km?: number;
  rating?: number;
  review_count?: number;
  website?: string;
  services?: string[];
  notes?: string;
};

export type ManualSupplierPayload = {
  name: string;
  category?: string;
  location_label?: string;
  distance_km?: number;
  product_categories?: string[];
  delivery_available?: boolean;
  minimum_order_quantity?: string;
  public_pricing?: string;
  quotation_amount?: number;
  contact_status?: string;
  is_preferred?: boolean;
  notes?: string;
};

export type FinancialAssumptionsPayload = {
  expected_rent?: number;
  security_deposit?: number;
  renovation_cost?: number;
  equipment_budget?: number;
  opening_inventory_budget?: number;
  license_budget?: number;
  marketing_budget?: number;
  monthly_staff_cost?: number;
  utilities_monthly?: number;
  logistics_monthly?: number;
  desired_owner_income?: number;
  working_capital_months: number;
  average_transaction_value?: number;
  gross_margin_percent?: number;
  working_days_per_month: number;
};

export type BusinessAnalysisPayload = {
  workflow_type:
    | "existing_idea"
    | "find_opportunity"
    | "compare_ideas"
    | "existing_business"
    | "evaluate_location"
    | "improve_business"
    | "ask_board";
  business_idea?: string;
  business_category?: string;
  location: BusinessLocationPayload;
  budget?: number;
  priorities: string[];
  data_mode: BusinessDataMode;
  shop_size_sqft?: number;
  business_experience?: string;
  skills: string[];
  target_customers?: string;
  risk_tolerance: "low" | "medium" | "high";
  timeline?: string;
  manual_competitors: ManualCompetitorPayload[];
  manual_suppliers: ManualSupplierPayload[];
  candidate_locations: Array<{
    name: string;
    country?: string;
    city?: string;
    locality?: string;
    latitude?: number;
    longitude?: number;
    expected_rent?: number;
    notes?: string;
  }>;
  properties: Array<{
    name: string;
    address?: string;
    rent?: number;
    deposit?: number;
    purchase_price?: number;
    shop_size_sqft?: number;
    frontage_ft?: number;
    floor?: string;
    parking?: string;
    visibility?: string;
    lease_duration_months?: number;
    rent_increase_percent?: number;
    renovation_required?: string;
    observations?: string;
  }>;
  customer_observations: string[];
  customer_interviews: Array<{
    customer_segment: string;
    need: string;
    willingness_to_pay?: string;
    notes?: string;
  }>;
  financial_assumptions: FinancialAssumptionsPayload;
  optional_inputs: Record<string, unknown>;
};

export type EvidenceRecord = {
  id: string;
  claim: string;
  source_name: string;
  source_url?: string | null;
  source_type: string;
  source_category?: string | null;
  provider?: string | null;
  retrieval_time: string;
  location?: Record<string, unknown> | null;
  value?: unknown;
  confidence: string;
  verification_status: string;
  freshness: string;
  notes?: string | null;
  tags: string[];
};

export type BusinessAnalysisSummary = {
  analysis_id: string;
  business_idea: string;
  business_category: string;
  location_label: string;
  recommendation_label: string;
  opportunity_score: number;
  evidence_confidence: string;
  data_mode: string;
  created_at?: string | null;
};

export type BusinessAnalysisResult = {
  analysis_id: string;
  status: string;
  data_mode: string;
  provider_label: string;
  generated_at: string;
  demo_notice?: string | null;
  disclaimer: string;
  intake: Record<string, unknown>;
  recommendation: {
    label: string;
    plain_language: string;
    business: string;
    selected_area: string;
    top_reasons: string[];
    main_risks: string[];
    financial_view: Record<string, unknown>;
    important_claims: Array<Record<string, unknown>>;
  };
  opportunity_score: {
    label: string;
    score: number;
    meaning: string;
    breakdown: Array<Record<string, unknown>>;
    advantages: string[];
    disadvantages: string[];
    unknowns: string[];
    evidence_confidence: string;
  };
  evidence_confidence: string;
  evidence_panel: Record<string, unknown>;
  evidence: EvidenceRecord[];
  competitors: Array<Record<string, unknown>>;
  suppliers: Array<Record<string, unknown>>;
  candidate_areas: Array<Record<string, unknown>>;
  properties: Array<Record<string, unknown>>;
  customer_segments: Array<Record<string, unknown>>;
  procurement_plan: Record<string, unknown>;
  financials: Record<string, unknown>;
  daily_sales: Record<string, unknown>;
  validation_plan: Array<Record<string, unknown>>;
  performance_tracking: Record<string, unknown>;
  live_intelligence: Record<string, unknown>;
  missing_information: string[];
  warnings: string[];
  board_brief: StartupBriefPayload;
  report: BoardReport;
};

export type ProviderHealthEntry = {
  type: string;
  name: string;
  status: string;
  configured: boolean;
  last_sync?: string | null;
  latency_ms?: number | null;
  error?: string | null;
  cache_hit?: boolean;
  cache_ttl_seconds?: number;
};

export type BusinessProviderStatus = {
  default_mode: string;
  maps_provider: string;
  live_maps_configured: boolean;
  live_places_configured: boolean;
  providers: ProviderHealthEntry[];
  cache: Record<string, unknown>;
  last_updated?: string | null;
  modes: Array<Record<string, unknown>>;
};

export type OperationsJobType =
  | "report_generation"
  | "scheduled_workflow"
  | "provider_sync"
  | "document_processing"
  | "email_delivery"
  | "analytics_refresh"
  | "scheduled_export";

export type OperationsJobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "canceled"
  | "dead_letter";

export type OperationsJob = {
  id: string;
  type: OperationsJobType | string;
  status: OperationsJobStatus | string;
  payload: Record<string, unknown>;
  actor?: string | null;
  organization_id?: string | null;
  attempts: number;
  max_attempts: number;
  progress: number;
  scheduled_for?: string | null;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
  cancel_requested: boolean;
};

export type OperationsJobStats = {
  backend: string;
  counts: Record<OperationsJobStatus | string, number>;
  queue_size: number;
  dead_letter_size: number;
  supported_job_types: OperationsJobType[];
};

export type OperationsJobsResponse = {
  jobs: OperationsJob[];
  stats: OperationsJobStats;
};

export type OperationsSchedule = {
  id: string;
  name: string;
  cron: string;
  job_type: OperationsJobType | string;
  payload: Record<string, unknown>;
  actor?: string | null;
  organization_id?: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  last_run_at?: string | null;
  next_run_at?: string | null;
};

export type OperationsSchedulesResponse = {
  schedules: OperationsSchedule[];
};

export type OperationsPluginManifest = {
  generated_at: string;
  plugin_types: string[];
  plugins: Array<Record<string, unknown>>;
  counts: Record<string, number>;
};

export type OperationsMonitoringSnapshot = {
  generated_at: string;
  api: {
    started_at: string;
    uptime_seconds: number;
    request_count: number;
    active_requests: number;
    status_counts: Record<string, number>;
    latency_ms: {
      count: number;
      average: number;
      p95: number;
      max: number;
    };
  };
  process: {
    pid?: number;
    platform?: string;
    python?: string;
    process_time_seconds?: number;
    memory_bytes?: Record<string, number>;
    cpu_percent?: number | null;
    rss_bytes?: number | null;
    psutil?: string;
  };
  active_users: number;
  dependencies: Record<string, unknown>;
  providers: BusinessProviderStatus | Record<string, unknown>;
  jobs: OperationsJobStats;
  cache: Record<string, unknown>;
};
