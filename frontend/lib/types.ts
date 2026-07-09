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
  missing_information: string[];
  warnings: string[];
  board_brief: StartupBriefPayload;
  report: BoardReport;
};

export type BusinessProviderStatus = {
  default_mode: string;
  maps_provider: string;
  live_maps_configured: boolean;
  live_places_configured: boolean;
  modes: Array<Record<string, unknown>>;
};
