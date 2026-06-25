"use client";

import { motion } from "framer-motion";
import {
  Activity,
  CheckCircle2,
  CircleAlert,
  CircleDotDashed,
  FileText,
  Gauge,
  Layers3,
  type LucideIcon,
  Play,
  RotateCcw,
  ShieldCheck,
  Vote,
  Wifi
} from "lucide-react";
import {
  type FormEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import { boardMeetingWebSocketUrl } from "@/lib/api";
import type {
  BoardMeetingResult,
  ConfidencePoint,
  LiveBoardroomEvent,
  LiveVote,
  MeetingTurn,
  StartupBriefPayload,
  StreamedReportSection
} from "@/lib/types";
import { cn } from "@/lib/utils";
import { useBoardroomStore } from "@/store/use-boardroom-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type BriefFormState = StartupBriefPayload & {
  competitorsText: string;
};

type LiveStatus = "idle" | "connecting" | "running" | "completed" | "error";

type LiveMeetingState = {
  status: LiveStatus;
  meetingId: string | null;
  activeRole: string | null;
  executives: string[];
  statuses: Record<string, string>;
  assessment: BoardMeetingResult["assessment"] | null;
  timeline: MeetingTurn[];
  confidence: Record<string, ConfidencePoint[]>;
  votes: Record<string, LiveVote>;
  reportSections: Record<string, StreamedReportSection>;
  result: BoardMeetingResult | null;
  error: string | null;
};

const executiveRoles = [
  "CEO",
  "CTO",
  "CFO",
  "COO",
  "CMO",
  "Product Manager",
  "Investor",
  "VC Partner",
  "Market Research Analyst",
  "Competitive Intelligence Analyst",
  "Legal Advisor",
  "Cybersecurity Expert",
  "Economist",
  "Growth Strategist",
  "UX Designer",
  "Data Scientist",
  "Operations Advisor",
  "AI Ethics Advisor"
];

const initialForm: BriefFormState = {
  startup_idea: "AI operating system that helps independent clinics manage cash flow",
  industry: "healthcare fintech",
  country: "United States",
  budget: 150000,
  timeline_months: 6,
  competitors: ["QuickBooks", "Brex", "Ramp"],
  competitorsText: "QuickBooks, Brex, Ramp",
  target_audience: "clinic owners with 5-50 employees",
  funding_stage: "pre-seed",
  business_model: "B2B SaaS"
};

const initialLiveState: LiveMeetingState = {
  status: "idle",
  meetingId: null,
  activeRole: null,
  executives: executiveRoles,
  statuses: {},
  assessment: null,
  timeline: [],
  confidence: {},
  votes: {},
  reportSections: {},
  result: null,
  error: null
};

const sectionTitles: Record<string, string> = {
  executive_summary: "Executive Summary",
  business_plan: "Business Plan",
  market_analysis: "Market Analysis",
  competitor_analysis: "Competitor Analysis",
  swot: "SWOT",
  business_model_canvas: "Business Model Canvas",
  customer_personas: "Customer Personas",
  technology_architecture: "Technology",
  database_design: "Database",
  financial_forecast: "Financials",
  hiring_plan: "Hiring",
  marketing_strategy: "Marketing",
  investment_readiness: "Investment Readiness",
  risk_assessment: "Risk",
  pitch_deck_summary: "Pitch Deck",
  ninety_day_roadmap: "90-Day Roadmap",
  board_vote: "Board Vote",
  confidence_scores: "Confidence"
};

export function BoardroomApp() {
  const { setLatestResult, clearLatestResult } = useBoardroomStore();
  const [form, setForm] = useState<BriefFormState>(initialForm);
  const [liveState, setLiveState] = useState<LiveMeetingState>(initialLiveState);
  const [activeSection, setActiveSection] = useState("executive_summary");
  const socketRef = useRef<WebSocket | null>(null);

  const payload = useMemo<StartupBriefPayload>(
    () => ({
      startup_idea: form.startup_idea,
      industry: form.industry,
      country: form.country,
      budget: Number(form.budget),
      timeline_months: Number(form.timeline_months),
      competitors: form.competitorsText
        .split(",")
        .map((competitor) => competitor.trim())
        .filter(Boolean),
      target_audience: form.target_audience,
      funding_stage: form.funding_stage,
      business_model: form.business_model
    }),
    [form]
  );

  const handleEvent = useCallback(
    (event: LiveBoardroomEvent) => {
      if (event.event_type === "consensus_reached" && isRecord(event.payload.result)) {
        setLatestResult(event.payload.result as BoardMeetingResult);
      }

      setLiveState((current) => reduceLiveState(current, event));

      if (event.event_type === "report_section") {
        const key = String(event.payload.section_key ?? "executive_summary");
        setActiveSection(key);
      }
    },
    [setLatestResult]
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    socketRef.current?.close();
    clearLatestResult();
    setActiveSection("executive_summary");
    setLiveState({
      ...initialLiveState,
      status: "connecting"
    });

    const socket = new WebSocket(boardMeetingWebSocketUrl());
    socketRef.current = socket;

    socket.onopen = () => {
      setLiveState((current) => ({
        ...current,
        status: "running"
      }));
      socket.send(JSON.stringify(payload));
    };

    socket.onmessage = (message) => {
      const eventPayload = JSON.parse(String(message.data)) as LiveBoardroomEvent;
      handleEvent(eventPayload);
    };

    socket.onerror = () => {
      setLiveState((current) => ({
        ...current,
        status: "error",
        error: "Live meeting connection failed."
      }));
    };

    socket.onclose = () => {
      setLiveState((current) => {
        if (current.status === "running" || current.status === "connecting") {
          return {
            ...current,
            status: current.result ? "completed" : "error",
            error: current.result ? null : "Live meeting connection closed before consensus."
          };
        }
        return current;
      });
    };
  }

  function resetBoardroom() {
    socketRef.current?.close();
    socketRef.current = null;
    setForm(initialForm);
    clearLatestResult();
    setActiveSection("executive_summary");
    setLiveState(initialLiveState);
  }

  useEffect(() => {
    return () => {
      socketRef.current?.close();
    };
  }, []);

  const pending = liveState.status === "connecting" || liveState.status === "running";

  return (
    <main className="board-grid min-h-screen overflow-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-4 py-4 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-3 border-b border-white/10 pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div
              className="h-11 w-11 rounded-md border border-board-teal/30 bg-board-panel bg-cover bg-center"
              style={{ backgroundImage: "url('/boardroom-mark.svg')" }}
              aria-hidden="true"
            />
            <div>
              <h1 className="text-xl font-semibold text-white sm:text-2xl">Boardroom AI</h1>
              <p className="text-sm text-board-muted">Live executive operating system</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill state={liveState} />
            <Button variant="quiet" size="icon" title="Reset boardroom" onClick={resetBoardroom}>
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </header>

        <div className="grid flex-1 gap-4 py-4 xl:grid-cols-[390px_minmax(0,1fr)]">
          <FounderBriefPanel
            form={form}
            setForm={setForm}
            onSubmit={handleSubmit}
            pending={pending}
            error={liveState.error}
          />

          <section className="grid min-h-0 gap-4 2xl:grid-cols-[minmax(0,1.15fr)_minmax(430px,0.85fr)]">
            <div className="flex min-h-0 flex-col gap-4">
              <BoardroomStage state={liveState} />
              <TimelinePanel state={liveState} />
            </div>
            <div className="grid min-h-0 gap-4 xl:grid-cols-2 2xl:grid-cols-1">
              <VotePanel state={liveState} />
              <ConfidencePanel state={liveState} />
              <RiskPanel state={liveState} />
              <ReportPanel
                state={liveState}
                activeSection={activeSection}
                setActiveSection={setActiveSection}
              />
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

function FounderBriefPanel({
  form,
  setForm,
  onSubmit,
  pending,
  error
}: {
  form: BriefFormState;
  setForm: (form: BriefFormState) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  pending: boolean;
  error: string | null;
}) {
  return (
    <form className="glass-panel flex min-h-0 flex-col rounded-lg p-4" onSubmit={onSubmit}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white">Founder Brief</h2>
          <p className="text-sm text-board-muted">Strategic intake</p>
        </div>
        <Button type="submit" disabled={pending} title="Start live board meeting">
          {pending ? (
            <Activity className="h-4 w-4 animate-pulse" aria-hidden="true" />
          ) : (
            <Play className="h-4 w-4" aria-hidden="true" />
          )}
          Convene
        </Button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        <Field label="Startup idea">
          <Textarea
            value={form.startup_idea}
            onChange={(event) => setForm({ ...form, startup_idea: event.target.value })}
          />
        </Field>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
          <Field label="Industry">
            <Input
              value={form.industry}
              onChange={(event) => setForm({ ...form, industry: event.target.value })}
            />
          </Field>
          <Field label="Country">
            <Input
              value={form.country}
              onChange={(event) => setForm({ ...form, country: event.target.value })}
            />
          </Field>
          <Field label="Budget">
            <Input
              type="number"
              min={1}
              value={form.budget}
              onChange={(event) => setForm({ ...form, budget: Number(event.target.value) })}
            />
          </Field>
          <Field label="Timeline months">
            <Input
              type="number"
              min={1}
              value={form.timeline_months}
              onChange={(event) =>
                setForm({ ...form, timeline_months: Number(event.target.value) })
              }
            />
          </Field>
        </div>

        <Field label="Competitors">
          <Input
            value={form.competitorsText}
            onChange={(event) => setForm({ ...form, competitorsText: event.target.value })}
          />
        </Field>

        <Field label="Target audience">
          <Textarea
            value={form.target_audience}
            onChange={(event) => setForm({ ...form, target_audience: event.target.value })}
          />
        </Field>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
          <Field label="Funding stage">
            <Input
              value={form.funding_stage}
              onChange={(event) => setForm({ ...form, funding_stage: event.target.value })}
            />
          </Field>
          <Field label="Business model">
            <Input
              value={form.business_model}
              onChange={(event) => setForm({ ...form, business_model: event.target.value })}
            />
          </Field>
        </div>
      </div>

      {error ? (
        <div className="mt-4 rounded-md border border-board-rose/30 bg-board-rose/10 p-3 text-sm text-board-rose">
          {error}
        </div>
      ) : null}
    </form>
  );
}

function BoardroomStage({ state }: { state: LiveMeetingState }) {
  const roles = state.executives.length > 0 ? state.executives : executiveRoles;
  const latestTurn = state.timeline.at(-1);

  return (
    <Panel
      icon={Wifi}
      title="Executive Boardroom"
      subtitle={state.meetingId ? `Meeting ${state.meetingId.slice(0, 8)}` : "Awaiting brief"}
      className="min-h-[620px]"
    >
      <div className="grid grid-cols-2 gap-2 lg:hidden">
        {roles.map((role) => (
          <ExecutiveSeat
            key={role}
            role={role}
            state={state}
            compact
            active={state.activeRole === role}
          />
        ))}
      </div>

      <div className="relative hidden min-h-[520px] overflow-hidden rounded-lg border border-white/10 bg-black/15 lg:block">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(56,214,198,0.16),transparent_36%)]" />
        <motion.div
          className="absolute left-1/2 top-1/2 flex aspect-[1.7] w-[42%] -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-[50%] border border-board-teal/30 bg-board-panel/80 p-8 text-center shadow-glow"
          animate={{
            boxShadow:
              state.status === "completed"
                ? "0 0 0 1px rgba(56,214,198,0.45), 0 0 70px rgba(56,214,198,0.2)"
                : "0 0 0 1px rgba(255,255,255,0.08), 0 24px 80px rgba(0,0,0,0.45)"
          }}
        >
          <div className="text-xs uppercase tracking-[0.18em] text-board-muted">Live Session</div>
          <div className="mt-3 text-2xl font-semibold text-white">
            {state.status === "completed"
              ? formatDecision(state.result?.decision ?? "Consensus")
              : state.activeRole ?? "Board ready"}
          </div>
          <p className="mt-3 max-w-sm text-sm leading-6 text-board-muted">
            {latestTurn?.message ?? activeStatusLabel(state)}
          </p>
          {state.status === "running" ? <ThinkingDots /> : null}
        </motion.div>

        {roles.map((role, index) => {
          const position = seatPosition(index, roles.length);
          return (
            <div
              key={role}
              className="absolute w-[138px] -translate-x-1/2 -translate-y-1/2"
              style={position}
            >
              <ExecutiveSeat role={role} state={state} active={state.activeRole === role} />
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

function ExecutiveSeat({
  role,
  state,
  active,
  compact = false
}: {
  role: string;
  state: LiveMeetingState;
  active: boolean;
  compact?: boolean;
}) {
  const confidence = latestConfidence(state.confidence[role]);
  const vote = state.votes[role];
  const status = state.statuses[role];

  return (
    <motion.div
      layout
      animate={{
        scale: active ? 1.04 : 1,
        borderColor: active ? "rgba(56,214,198,0.7)" : "rgba(255,255,255,0.1)"
      }}
      className={cn(
        "rounded-md border bg-white/[0.045] p-3 transition",
        active ? "shadow-[0_0_35px_rgba(56,214,198,0.22)]" : "",
        compact ? "min-h-[118px]" : "min-h-[132px]"
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-white/10 bg-board-ink text-xs font-semibold text-board-teal">
          {initials(role)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-medium text-white">{role}</div>
          <div className="mt-1 truncate text-xs text-board-muted">
            {status ?? (vote ? formatDecision(vote.vote) : "Awaiting")}
          </div>
        </div>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.07]">
        <div
          className="h-full rounded-full bg-board-teal transition-all"
          style={{ width: `${Math.round((confidence ?? 0.38) * 100)}%` }}
        />
      </div>
      <div className="mt-3 flex items-center justify-between gap-2 text-xs">
        <span className={cn("truncate", voteColor(vote?.vote ?? "abstain"))}>
          {vote ? formatDecision(vote.vote) : "No vote"}
        </span>
        <span className="text-board-muted">{confidence ? Math.round(confidence * 100) : "--"}</span>
      </div>
      {active && state.status === "running" ? <ThinkingDots small /> : null}
    </motion.div>
  );
}

function TimelinePanel({ state }: { state: LiveMeetingState }) {
  return (
    <Panel
      icon={Layers3}
      title="Live Timeline"
      subtitle={`${state.timeline.length} statements`}
      className="min-h-[360px]"
    >
      {state.timeline.length > 0 ? (
        <div className="max-h-[430px] overflow-y-auto pr-1">
          <div className="space-y-3">
            {state.timeline.map((turn, index) => (
              <motion.article
                key={`${turn.speaker_role}-${turn.sequence ?? index}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.22 }}
                className="grid gap-3 border-l border-white/10 bg-white/[0.025] p-3 sm:grid-cols-[120px_minmax(0,1fr)]"
              >
                <div>
                  <div className="text-xs text-board-muted">{formatTime(turn.occurred_at)}</div>
                  <div className="mt-2 text-sm font-medium text-white">{turn.speaker_role}</div>
                  <div className="mt-1 text-xs text-board-teal">{turn.topic ?? turn.turn_type}</div>
                  <div className="mt-2 text-xs text-board-muted">
                    {Math.round(turn.confidence * 100)} confidence
                  </div>
                </div>
                <div>
                  <p className="text-sm leading-6 text-board-mist">{turn.message}</p>
                  {turn.memory_references?.length ? (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {turn.memory_references.map((reference) => (
                        <span
                          key={reference}
                          className="rounded-sm border border-white/10 px-2 py-1 text-xs text-board-muted"
                        >
                          referenced {reference}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </motion.article>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState icon={Layers3} label="Transcript idle" />
      )}
    </Panel>
  );
}

function VotePanel({ state }: { state: LiveMeetingState }) {
  const votes = Object.values(state.votes);

  return (
    <Panel
      icon={Vote}
      title="Live Vote"
      subtitle={state.result ? formatDecision(state.result.decision) : `${votes.length} votes`}
    >
      {votes.length > 0 ? (
        <div className="grid max-h-[320px] gap-2 overflow-y-auto pr-1 sm:grid-cols-2 2xl:grid-cols-1">
          {votes.map((vote) => (
            <motion.div
              key={vote.role}
              layout
              className={cn(
                "rounded-md border p-3",
                vote.changed
                  ? "border-board-amber/50 bg-board-amber/10"
                  : "border-white/10 bg-white/[0.035]"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium text-white">{vote.role}</div>
                  <div className={cn("mt-1 text-xs", voteColor(vote.vote))}>
                    {vote.previous_vote && vote.changed
                      ? `${formatDecision(vote.previous_vote)} -> ${formatDecision(vote.vote)}`
                      : formatDecision(vote.vote)}
                  </div>
                </div>
                <div className="text-sm text-board-mist">{Math.round(vote.confidence * 100)}</div>
              </div>
              <p className="mt-2 text-xs leading-5 text-board-muted">{vote.rationale}</p>
            </motion.div>
          ))}
        </div>
      ) : (
        <EmptyState icon={Vote} label="Votes pending" />
      )}
    </Panel>
  );
}

function ConfidencePanel({ state }: { state: LiveMeetingState }) {
  const entries = Object.entries(state.confidence);

  return (
    <Panel icon={Gauge} title="Confidence Evolution" subtitle={`${entries.length} executives`}>
      {entries.length > 0 ? (
        <div className="max-h-[320px] space-y-3 overflow-y-auto pr-1">
          {entries.map(([role, points]) => {
            const latest = points.at(-1);
            return (
              <div key={role}>
                <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                  <span className="truncate text-board-muted">{role}</span>
                  <span className="text-board-mist">
                    {latest ? Math.round(latest.confidence * 100) : "--"}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className="h-full rounded-full bg-board-violet transition-all"
                    style={{ width: `${Math.round((latest?.confidence ?? 0) * 100)}%` }}
                  />
                </div>
                <div className="mt-2 flex gap-1">
                  {points.slice(-8).map((point) => (
                    <span
                      key={`${role}-${point.sequence}`}
                      title={point.reason}
                      className={cn(
                        "h-1.5 flex-1 rounded-full",
                        point.delta == null
                          ? "bg-board-muted"
                          : point.delta >= 0
                            ? "bg-board-teal"
                            : "bg-board-rose"
                      )}
                    />
                  ))}
                </div>
                <p className="mt-1 line-clamp-2 text-xs leading-5 text-board-muted">
                  {latest?.reason}
                </p>
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState icon={Gauge} label="Confidence idle" />
      )}
    </Panel>
  );
}

function RiskPanel({ state }: { state: LiveMeetingState }) {
  const riskEntries = Object.entries(state.assessment?.risk_scores ?? {});

  return (
    <Panel
      icon={ShieldCheck}
      title="Risk Signals"
      subtitle={state.assessment ? "Board assessment" : "No assessment"}
    >
      {state.assessment ? (
        <div className="space-y-3">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-semibold text-white">
              {Math.round(state.assessment.overall_risk * 100)}
            </div>
            <div className="text-sm text-board-muted">overall risk</div>
          </div>
          <div className="space-y-3">
            {riskEntries.map(([key, value]) => (
              <div key={key}>
                <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                  <span className="text-board-muted">{titleCase(key)}</span>
                  <span className="text-board-mist">{Math.round(value * 100)}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className={cn(
                      "h-full rounded-full",
                      value > 0.72
                        ? "bg-board-rose"
                        : value > 0.55
                          ? "bg-board-amber"
                          : "bg-board-teal"
                    )}
                    style={{ width: `${Math.round(value * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState icon={ShieldCheck} label="Risk model idle" />
      )}
    </Panel>
  );
}

function ReportPanel({
  state,
  activeSection,
  setActiveSection
}: {
  state: LiveMeetingState;
  activeSection: string;
  setActiveSection: (section: string) => void;
}) {
  const sections = Object.values(state.reportSections).sort(
    (left, right) => (left.sequence ?? 0) - (right.sequence ?? 0)
  );
  const activeValue = state.reportSections[activeSection]?.content;

  return (
    <Panel
      icon={FileText}
      title="Streaming Report"
      subtitle={`${sections.length} / ${Object.keys(sectionTitles).length} sections`}
      className="xl:col-span-2 2xl:col-span-1"
    >
      {sections.length > 0 ? (
        <div className="grid min-h-0 gap-4 lg:grid-cols-[190px_minmax(0,1fr)] 2xl:grid-cols-1">
          <nav className="flex gap-2 overflow-x-auto pb-2 lg:max-h-[360px] lg:flex-col lg:overflow-y-auto lg:pb-0 lg:pr-1 2xl:max-h-none 2xl:flex-row 2xl:pb-2">
            {sections.map((section) => (
              <button
                type="button"
                key={section.section_key}
                onClick={() => setActiveSection(section.section_key)}
                className={cn(
                  "min-w-fit rounded-md px-3 py-2 text-left text-sm transition",
                  activeSection === section.section_key
                    ? "bg-board-teal text-board-ink"
                    : "bg-white/[0.04] text-board-muted hover:bg-white/[0.08] hover:text-board-mist"
                )}
              >
                {section.section_title}
              </button>
            ))}
          </nav>
          <div className="max-h-[360px] overflow-y-auto rounded-md border border-white/10 bg-white/[0.025] p-4">
            <h3 className="mb-4 text-lg font-semibold text-white">
              {state.reportSections[activeSection]?.section_title ?? "Report Section"}
            </h3>
            <SectionValue value={activeValue} />
          </div>
        </div>
      ) : (
        <EmptyState icon={FileText} label="Report pending" />
      )}
    </Panel>
  );
}

function StatusPill({ state }: { state: LiveMeetingState }) {
  const Icon =
    state.status === "running"
      ? Activity
      : state.status === "completed"
        ? CheckCircle2
        : state.status === "error"
          ? CircleAlert
          : CircleDotDashed;
  const label =
    state.status === "completed"
      ? formatDecision(state.result?.decision ?? "Consensus")
      : state.status === "running"
        ? activeStatusLabel(state)
        : titleCase(state.status);

  return (
    <div className="inline-flex h-10 items-center gap-2 rounded-md border border-white/10 bg-white/[0.04] px-3 text-sm text-board-mist">
      <Icon
        className={cn("h-4 w-4 text-board-teal", state.status === "running" && "animate-pulse")}
        aria-hidden="true"
      />
      <span>{label}</span>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-medium text-board-muted">{label}</span>
      {children}
    </label>
  );
}

function Panel({
  icon: Icon,
  title,
  subtitle,
  children,
  className
}: {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("glass-panel rounded-lg p-4", className)}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate text-base font-semibold text-white">{title}</h2>
          <p className="truncate text-sm text-board-muted">{subtitle}</p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-board-teal">
          <Icon className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>
      {children}
    </section>
  );
}

function EmptyState({ icon: Icon, label }: { icon: LucideIcon; label: string }) {
  return (
    <div className="flex min-h-36 flex-col items-center justify-center rounded-md border border-dashed border-white/10 bg-white/[0.02] text-center">
      <Icon className="mb-3 h-5 w-5 text-board-muted" aria-hidden="true" />
      <p className="text-sm text-board-muted">{label}</p>
    </div>
  );
}

function ThinkingDots({ small = false }: { small?: boolean }) {
  return (
    <div className={cn("mt-3 flex items-center justify-center gap-1", small && "justify-start")}>
      {[0, 1, 2].map((dot) => (
        <motion.span
          key={dot}
          className={cn("rounded-full bg-board-teal", small ? "h-1.5 w-1.5" : "h-2 w-2")}
          animate={{ opacity: [0.25, 1, 0.25], y: [0, -2, 0] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: dot * 0.12 }}
        />
      ))}
    </div>
  );
}

function SectionValue({ value }: { value: unknown }) {
  if (value == null) {
    return (
      <div className="flex items-center gap-2 text-sm text-board-muted">
        <CircleAlert className="h-4 w-4" aria-hidden="true" />
        Section unavailable
      </div>
    );
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return <p className="text-sm leading-6 text-board-mist">{String(value)}</p>;
  }

  if (Array.isArray(value)) {
    return (
      <div className="space-y-3">
        {value.map((item, index) => (
          <div key={index} className="border-b border-white/10 pb-3 last:border-0 last:pb-0">
            <SectionValue value={item} />
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === "object") {
    return (
      <div className="space-y-4">
        {Object.entries(value as Record<string, unknown>).map(([key, nestedValue]) => (
          <div key={key} className="border-b border-white/10 pb-4 last:border-0 last:pb-0">
            <div className="mb-2 text-xs font-medium text-board-muted">{titleCase(key)}</div>
            <SectionValue value={nestedValue} />
          </div>
        ))}
      </div>
    );
  }

  return <p className="text-sm text-board-muted">Unsupported section value</p>;
}

function reduceLiveState(state: LiveMeetingState, event: LiveBoardroomEvent): LiveMeetingState {
  const next: LiveMeetingState = {
    ...state,
    meetingId: event.meeting_id ?? state.meetingId
  };

  if (event.event_type === "error") {
    return {
      ...next,
      status: "error",
      error: String(event.payload.message ?? "Live meeting failed.")
    };
  }

  if (event.event_type === "meeting_started") {
    return {
      ...next,
      status: "running",
      executives: Array.isArray(event.payload.executives)
        ? event.payload.executives.map(String)
        : executiveRoles,
      assessment: isRecord(event.payload.assessment)
        ? (event.payload.assessment as BoardMeetingResult["assessment"])
        : null
    };
  }

  if (event.event_type === "executive_status") {
    const role = String(event.payload.role ?? event.role ?? "");
    return {
      ...next,
      activeRole: role,
      statuses: {
        ...next.statuses,
        [role]: String(event.payload.label ?? event.payload.status ?? "Thinking")
      }
    };
  }

  if (event.event_type === "confidence_changed") {
    const role = String(event.payload.role ?? event.role ?? "");
    const point: ConfidencePoint = {
      sequence: Number(event.sequence ?? 0),
      confidence: Number(event.payload.confidence ?? 0),
      previous_confidence:
        event.payload.previous_confidence == null
          ? null
          : Number(event.payload.previous_confidence),
      delta: event.payload.delta == null ? null : Number(event.payload.delta),
      reason: String(event.payload.reason ?? ""),
      timestamp: event.timestamp
    };
    return {
      ...next,
      confidence: {
        ...next.confidence,
        [role]: [...(next.confidence[role] ?? []), point]
      }
    };
  }

  if (event.event_type === "timeline_statement") {
    const turn = event.payload as unknown as MeetingTurn;
    return {
      ...next,
      activeRole: turn.speaker_role,
      timeline: [
        ...next.timeline,
        {
          ...turn,
          occurred_at: turn.occurred_at ?? event.timestamp ?? null
        }
      ]
    };
  }

  if (
    event.event_type === "vote_cast" ||
    event.event_type === "vote_changed" ||
    event.event_type === "vote_confirmed"
  ) {
    const vote = event.payload as unknown as LiveVote;
    return {
      ...next,
      votes: {
        ...next.votes,
        [vote.role]: {
          ...vote,
          sequence: event.sequence,
          changed: event.payload.changed === true
        }
      }
    };
  }

  if (event.event_type === "report_section") {
    const section = event.payload as unknown as StreamedReportSection;
    return {
      ...next,
      reportSections: {
        ...next.reportSections,
        [section.section_key]: {
          ...section,
          sequence: event.sequence
        }
      }
    };
  }

  if (event.event_type === "consensus_reached") {
    const result = isRecord(event.payload.result)
      ? (event.payload.result as BoardMeetingResult)
      : next.result;
    return {
      ...next,
      status: "completed",
      activeRole: null,
      result,
      error: null
    };
  }

  return next;
}

function activeStatusLabel(state: LiveMeetingState) {
  if (state.activeRole && state.statuses[state.activeRole]) {
    return state.statuses[state.activeRole];
  }
  if (state.status === "connecting") {
    return "Connecting...";
  }
  if (state.status === "running") {
    return "Meeting in session";
  }
  return "Ready";
}

function seatPosition(index: number, total: number) {
  const angle = -90 + index * (360 / total);
  const radians = (angle * Math.PI) / 180;
  const x = 50 + 42 * Math.cos(radians);
  const y = 50 + 42 * Math.sin(radians);
  return {
    left: `${x}%`,
    top: `${y}%`
  };
}

function latestConfidence(points: ConfidencePoint[] | undefined) {
  return points?.at(-1)?.confidence ?? null;
}

function initials(role: string) {
  return role
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
}

function titleCase(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
    .replace("Ai", "AI");
}

function formatDecision(value: string) {
  return titleCase(value.replace(/_/g, " "));
}

function formatTime(value?: string | null) {
  if (!value) {
    return "--:--";
  }
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  }).format(new Date(value));
}

function voteColor(vote: string) {
  if (vote === "approve") {
    return "text-board-teal";
  }
  if (vote === "approve_with_conditions") {
    return "text-board-amber";
  }
  if (vote === "reject") {
    return "text-board-rose";
  }
  return "text-board-muted";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
