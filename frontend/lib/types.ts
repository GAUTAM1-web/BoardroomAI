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
