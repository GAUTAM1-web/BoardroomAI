"use client";

import { motion } from "framer-motion";
import {
  Activity,
  BarChart3,
  Bookmark,
  BookmarkCheck,
  CheckCircle2,
  CircleAlert,
  CircleDotDashed,
  Download,
  FileJson,
  FileText,
  Gauge,
  History,
  Layers3,
  LineChart,
  Loader2,
  Play,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Trash2,
  TrendingUp,
  type LucideIcon,
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

import {
  boardMeetingWebSocketUrl,
  deleteMeeting,
  fetchDashboard,
  fetchMeetingDetail,
  fetchMeetings,
  generateStartupIdeas,
  reportExportUrl,
  searchEverything,
  updateMeetingFavorite
} from "@/lib/api";
import type {
  BoardMeetingDetail,
  BoardMeetingResult,
  ConfidencePoint,
  DashboardSnapshot,
  GlobalSearchResults,
  LiveBoardroomEvent,
  LiveVote,
  MeetingSummary,
  MeetingTurn,
  StartupBriefPayload,
  StartupIdea,
  StartupIdeaGenerationPayload,
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
type AppView = "dashboard" | "ideas" | "meeting" | "history";

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

const initialIdeaForm: StartupIdeaGenerationPayload = {
  prompt: "Generate 8 startup ideas for AI workflow automation",
  interests: "AI operating systems, founder tools, workflow automation",
  industry: "AI productivity",
  country: "United States",
  budget: 150000,
  business_model: "B2B SaaS",
  funding_stage: "pre-seed",
  number_of_ideas: 8
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
  startup_overview: "Startup Overview",
  executive_opinions: "Executive Opinions",
  business_plan: "Business Plan",
  market_analysis: "Market Analysis",
  competitor_analysis: "Competitor Analysis",
  swot: "SWOT",
  business_model_canvas: "Business Model Canvas",
  customer_personas: "Customer Personas",
  technology_architecture: "Technology",
  database_design: "Database",
  financial_forecast: "Financials",
  financial_analysis: "Financial Analysis",
  hiring_plan: "Hiring",
  marketing_strategy: "Marketing",
  investment_readiness: "Investment Readiness",
  risk_assessment: "Risk",
  risk_matrix: "Risk Matrix",
  action_plan: "Action Plan",
  vc_readiness_score: "VC Readiness",
  pitch_deck_summary: "Pitch Deck",
  ninety_day_roadmap: "90-Day Roadmap",
  board_vote: "Board Vote",
  confidence_scores: "Confidence"
};

export function BoardroomApp() {
  const { setLatestResult, clearLatestResult } = useBoardroomStore();
  const [view, setView] = useState<AppView>("dashboard");
  const [form, setForm] = useState<BriefFormState>(initialForm);
  const [ideaForm, setIdeaForm] = useState<StartupIdeaGenerationPayload>(initialIdeaForm);
  const [ideas, setIdeas] = useState<StartupIdea[]>([]);
  const [dashboard, setDashboard] = useState<DashboardSnapshot | null>(null);
  const [history, setHistory] = useState<MeetingSummary[]>([]);
  const [historyQuery, setHistoryQuery] = useState("");
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [decisionFilter, setDecisionFilter] = useState("all");
  const [selectedMeetingIds, setSelectedMeetingIds] = useState<string[]>([]);
  const [historyDetail, setHistoryDetail] = useState<BoardMeetingDetail | null>(null);
  const [globalQuery, setGlobalQuery] = useState("");
  const [searchResults, setSearchResults] = useState<GlobalSearchResults | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [generatingIdeas, setGeneratingIdeas] = useState(false);
  const [searching, setSearching] = useState(false);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [liveState, setLiveState] = useState<LiveMeetingState>(initialLiveState);
  const [activeSection, setActiveSection] = useState("executive_summary");
  const socketRef = useRef<WebSocket | null>(null);

  const payload = useMemo<StartupBriefPayload>(() => formToPayload(form), [form]);

  const refreshWorkspace = useCallback(async () => {
    setLoadingDashboard(true);
    try {
      const [dashboardSnapshot, meetings] = await Promise.all([
        fetchDashboard(),
        fetchMeetings({ limit: 40 })
      ]);
      setDashboard(dashboardSnapshot);
      setHistory(meetings);
      setWorkspaceError(null);
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Workspace data failed to load");
    } finally {
      setLoadingDashboard(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      setHistory(
        await fetchMeetings({
          query: historyQuery,
          favoriteOnly,
          limit: 60
        })
      );
      setWorkspaceError(null);
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Meeting history failed to load");
    } finally {
      setLoadingHistory(false);
    }
  }, [favoriteOnly, historyQuery]);

  const handleEvent = useCallback(
    (event: LiveBoardroomEvent) => {
      if (event.event_type === "consensus_reached" && isRecord(event.payload.result)) {
        setLatestResult(event.payload.result as BoardMeetingResult);
        void refreshWorkspace();
      }

      setLiveState((current) => reduceLiveState(current, event));

      if (event.event_type === "report_section") {
        const key = String(event.payload.section_key ?? "executive_summary");
        setActiveSection(key);
      }
    },
    [refreshWorkspace, setLatestResult]
  );

  const startLiveMeeting = useCallback(
    (meetingPayload: StartupBriefPayload) => {
      socketRef.current?.close();
      clearLatestResult();
      setForm(formFromPayload(meetingPayload));
      setView("meeting");
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
        socket.send(JSON.stringify(meetingPayload));
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
    },
    [clearLatestResult, handleEvent]
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startLiveMeeting(payload);
  }

  async function handleGenerateIdeas(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setGeneratingIdeas(true);
    try {
      setIdeas(await generateStartupIdeas(ideaForm));
      setView("ideas");
      setWorkspaceError(null);
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Startup idea generation failed");
    } finally {
      setGeneratingIdeas(false);
    }
  }

  async function handleGlobalSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!globalQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      setSearchResults(await searchEverything(globalQuery.trim()));
      setWorkspaceError(null);
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function openHistoryDetail(meetingId: string) {
    setHistoryDetail(await fetchMeetingDetail(meetingId));
  }

  async function toggleFavorite(summary: MeetingSummary) {
    await updateMeetingFavorite(summary.meeting_id, !summary.is_favorite);
    await loadHistory();
    await refreshWorkspace();
  }

  async function removeHistory(summary: MeetingSummary) {
    const confirmed = window.confirm(`Delete ${summary.startup_idea}?`);
    if (!confirmed) {
      return;
    }
    await deleteMeeting(summary.meeting_id);
    if (historyDetail?.meeting_id === summary.meeting_id) {
      setHistoryDetail(null);
    }
    setSelectedMeetingIds((current) => current.filter((id) => id !== summary.meeting_id));
    await loadHistory();
    await refreshWorkspace();
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
    void refreshWorkspace();
    return () => {
      socketRef.current?.close();
    };
  }, [refreshWorkspace]);

  const pending = liveState.status === "connecting" || liveState.status === "running";
  const filteredHistory = history.filter((meeting) => {
    if (decisionFilter === "all") {
      return true;
    }
    return meeting.decision === decisionFilter;
  });

  return (
    <main className="board-grid min-h-screen overflow-x-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-[1760px] flex-col px-4 py-4 sm:px-6 lg:px-8">
        <header className="glass-panel sticky top-3 z-30 rounded-lg px-4 py-3">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex min-w-0 items-center gap-3">
              <div
                className="h-11 w-11 shrink-0 rounded-md border border-board-teal/30 bg-board-panel bg-cover bg-center"
                style={{ backgroundImage: "url('/boardroom-mark.svg')" }}
                aria-hidden="true"
              />
              <div className="min-w-0">
                <h1 className="text-xl font-semibold text-white sm:text-2xl">Boardroom AI</h1>
                <p className="text-sm text-board-muted">Founder operating system</p>
              </div>
            </div>

            <nav className="flex flex-wrap gap-2">
              <NavButton active={view === "dashboard"} icon={BarChart3} onClick={() => setView("dashboard")}>
                Dashboard
              </NavButton>
              <NavButton active={view === "ideas"} icon={Sparkles} onClick={() => setView("ideas")}>
                Ideas
              </NavButton>
              <NavButton active={view === "meeting"} icon={Wifi} onClick={() => setView("meeting")}>
                Boardroom
              </NavButton>
              <NavButton active={view === "history"} icon={History} onClick={() => setView("history")}>
                History
              </NavButton>
            </nav>

            <div className="flex flex-wrap items-center gap-2">
              <StatusPill state={liveState} />
              <Button variant="quiet" size="icon" title="Reset boardroom" onClick={resetBoardroom}>
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>

          <form className="mt-3 flex flex-col gap-2 lg:flex-row" onSubmit={handleGlobalSearch}>
            <div className="relative min-w-0 flex-1">
              <Search
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-board-muted"
                aria-hidden="true"
              />
              <Input
                value={globalQuery}
                onChange={(event) => setGlobalQuery(event.target.value)}
                placeholder="Search meetings, reports, executives, industries"
                className="pl-9"
              />
            </div>
            <Button type="submit" variant="quiet" disabled={searching}>
              {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Search
            </Button>
          </form>
        </header>

        {workspaceError ? (
          <div className="mt-4 rounded-md border border-board-amber/30 bg-board-amber/10 p-3 text-sm text-board-amber">
            {workspaceError}
          </div>
        ) : null}

        {searchResults ? (
          <GlobalSearchPanel
            results={searchResults}
            onOpen={(meetingId) => {
              setView("history");
              void openHistoryDetail(meetingId);
            }}
          />
        ) : null}

        <div className="flex-1 py-4">
          {view === "dashboard" ? (
            <DashboardView
              dashboard={dashboard}
              loading={loadingDashboard}
              ideas={ideas}
              history={history}
              onGenerate={() => setView("ideas")}
              onStart={startLiveMeeting}
              onOpenHistory={(meetingId) => {
                setView("history");
                void openHistoryDetail(meetingId);
              }}
            />
          ) : null}

          {view === "ideas" ? (
            <IdeasView
              form={ideaForm}
              setForm={setIdeaForm}
              ideas={ideas}
              generating={generatingIdeas}
              onSubmit={handleGenerateIdeas}
              onStart={startLiveMeeting}
            />
          ) : null}

          {view === "meeting" ? (
            <MeetingView
              form={form}
              setForm={setForm}
              onSubmit={handleSubmit}
              pending={pending}
              liveState={liveState}
              activeSection={activeSection}
              setActiveSection={setActiveSection}
            />
          ) : null}

          {view === "history" ? (
            <HistoryView
              meetings={filteredHistory}
              allMeetings={history}
              query={historyQuery}
              setQuery={setHistoryQuery}
              favoriteOnly={favoriteOnly}
              setFavoriteOnly={setFavoriteOnly}
              decisionFilter={decisionFilter}
              setDecisionFilter={setDecisionFilter}
              loading={loadingHistory}
              selectedMeetingIds={selectedMeetingIds}
              setSelectedMeetingIds={setSelectedMeetingIds}
              detail={historyDetail}
              onLoad={loadHistory}
              onOpen={openHistoryDetail}
              onStart={startLiveMeeting}
              onFavorite={toggleFavorite}
              onDelete={removeHistory}
            />
          ) : null}
        </div>
      </div>
    </main>
  );
}

function DashboardView({
  dashboard,
  loading,
  ideas,
  history,
  onGenerate,
  onStart,
  onOpenHistory
}: {
  dashboard: DashboardSnapshot | null;
  loading: boolean;
  ideas: StartupIdea[];
  history: MeetingSummary[];
  onGenerate: () => void;
  onStart: (payload: StartupBriefPayload) => void;
  onOpenHistory: (meetingId: string) => void;
}) {
  const recentIdeas = ideas.slice(0, 4);
  const recentMeetings = dashboard?.recent_meetings ?? history.slice(0, 6);

  return (
    <div className="space-y-4">
      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          icon={Layers3}
          label="Meetings"
          value={loading ? "..." : String(dashboard?.total_meetings ?? 0)}
          detail="completed and streaming"
        />
        <MetricCard
          icon={FileText}
          label="Reports"
          value={loading ? "..." : String(dashboard?.reports_generated ?? 0)}
          detail="investor artifacts"
        />
        <MetricCard
          icon={CheckCircle2}
          label="Approval Rate"
          value={loading ? "..." : percent(dashboard?.approval_rate ?? 0)}
          detail="approve or conditional"
        />
        <MetricCard
          icon={Gauge}
          label="Avg Confidence"
          value={loading ? "..." : percent(dashboard?.average_confidence ?? 0)}
          detail="final board signal"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <Panel icon={TrendingUp} title="Command Center" subtitle="Recent board decisions">
          {loading ? (
            <SkeletonRows />
          ) : recentMeetings.length ? (
            <div className="grid gap-3 lg:grid-cols-2">
              {recentMeetings.map((meeting) => (
                <button
                  type="button"
                  key={meeting.meeting_id}
                  onClick={() => onOpenHistory(meeting.meeting_id)}
                  className="min-w-0 rounded-md border border-white/10 bg-white/[0.035] p-3 text-left transition hover:border-board-teal/40 hover:bg-white/[0.06]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-white">{meeting.startup_idea}</div>
                      <div className="mt-1 text-xs text-board-muted">
                        {meeting.industry} - {meeting.country}
                      </div>
                    </div>
                    {meeting.is_favorite ? (
                      <BookmarkCheck className="h-4 w-4 shrink-0 text-board-amber" />
                    ) : null}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Badge tone={decisionTone(meeting.decision)}>{formatDecision(meeting.decision)}</Badge>
                    <Badge>{percent(meeting.aggregate_confidence)} confidence</Badge>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState icon={Layers3} label="No meetings yet" />
          )}
        </Panel>

        <Panel icon={LineChart} title="Market Signals" subtitle="Top industries">
          {loading ? (
            <SkeletonRows />
          ) : dashboard?.top_industries.length ? (
            <div className="space-y-3">
              {dashboard.top_industries.map((item) => (
                <div key={item.industry}>
                  <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                    <span className="break-words text-board-muted">{item.industry}</span>
                    <span className="text-board-mist">{item.count}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]">
                    <div
                      className="h-full rounded-full bg-board-teal"
                      style={{
                        width: `${Math.max(12, Math.min(100, item.count * 18))}%`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon={LineChart} label="No industry data" />
          )}
        </Panel>
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(360px,0.8fr)_minmax(0,1.2fr)]">
        <Panel icon={Sparkles} title="Generated Startup Ideas" subtitle={`${recentIdeas.length} ready briefs`}>
          {recentIdeas.length ? (
            <div className="space-y-3">
              {recentIdeas.map((idea) => (
                <StartupIdeaMiniCard key={idea.startup_name} idea={idea} onStart={onStart} />
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              <EmptyState icon={Sparkles} label="Idea queue empty" />
              <Button type="button" onClick={onGenerate}>
                <Sparkles className="h-4 w-4" />
                Generate Ideas
              </Button>
            </div>
          )}
        </Panel>

        <Panel icon={FileText} title="Recent Reports" subtitle="Investor-ready exports">
          {dashboard?.recent_reports.length ? (
            <div className="grid gap-3 md:grid-cols-2">
              {dashboard.recent_reports.map((meeting) => (
                <ReportSummaryCard key={meeting.meeting_id} meeting={meeting} onOpen={onOpenHistory} />
              ))}
            </div>
          ) : (
            <EmptyState icon={FileText} label="No completed reports" />
          )}
        </Panel>
      </section>
    </div>
  );
}

function IdeasView({
  form,
  setForm,
  ideas,
  generating,
  onSubmit,
  onStart
}: {
  form: StartupIdeaGenerationPayload;
  setForm: (form: StartupIdeaGenerationPayload) => void;
  ideas: StartupIdea[];
  generating: boolean;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onStart: (payload: StartupBriefPayload) => void;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
      <form className="glass-panel rounded-lg p-4" onSubmit={onSubmit}>
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-white">Startup Generator</h2>
            <p className="text-sm text-board-muted">AI incubation brief</p>
          </div>
          <Button type="submit" disabled={generating}>
            {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Generate
          </Button>
        </div>

        <div className="space-y-4">
          <Field label="Prompt">
            <Textarea
              value={form.prompt ?? ""}
              onChange={(event) => setForm({ ...form, prompt: event.target.value })}
              placeholder="Generate 20 startup ideas"
            />
          </Field>
          <Field label="Interests">
            <Input
              value={form.interests ?? ""}
              onChange={(event) => setForm({ ...form, interests: event.target.value })}
            />
          </Field>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            <Field label="Industry">
              <Input
                value={form.industry ?? ""}
                onChange={(event) => setForm({ ...form, industry: event.target.value })}
              />
            </Field>
            <Field label="Country">
              <Input
                value={form.country ?? ""}
                onChange={(event) => setForm({ ...form, country: event.target.value })}
              />
            </Field>
            <Field label="Budget">
              <Input
                type="number"
                min={1}
                value={form.budget ?? ""}
                onChange={(event) => setForm({ ...form, budget: Number(event.target.value) })}
              />
            </Field>
            <Field label="Number of ideas">
              <Input
                type="number"
                min={1}
                max={30}
                value={form.number_of_ideas ?? ""}
                onChange={(event) =>
                  setForm({ ...form, number_of_ideas: Number(event.target.value) })
                }
              />
            </Field>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            <Field label="Business model">
              <Input
                value={form.business_model ?? ""}
                onChange={(event) => setForm({ ...form, business_model: event.target.value })}
              />
            </Field>
            <Field label="Funding stage">
              <Input
                value={form.funding_stage ?? ""}
                onChange={(event) => setForm({ ...form, funding_stage: event.target.value })}
              />
            </Field>
          </div>
        </div>
      </form>

      <section className="min-w-0">
        {generating ? (
          <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <SkeletonCard key={index} />
            ))}
          </div>
        ) : ideas.length ? (
          <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
            {ideas.map((idea) => (
              <StartupIdeaCard key={`${idea.startup_name}-${idea.tagline}`} idea={idea} onStart={onStart} />
            ))}
          </div>
        ) : (
          <Panel icon={Sparkles} title="Generated Ideas" subtitle="No cards yet">
            <EmptyState icon={Sparkles} label="Generator ready" />
          </Panel>
        )}
      </section>
    </div>
  );
}

function MeetingView({
  form,
  setForm,
  onSubmit,
  pending,
  liveState,
  activeSection,
  setActiveSection
}: {
  form: BriefFormState;
  setForm: (form: BriefFormState) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  pending: boolean;
  liveState: LiveMeetingState;
  activeSection: string;
  setActiveSection: (section: string) => void;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
      <FounderBriefPanel
        form={form}
        setForm={setForm}
        onSubmit={onSubmit}
        pending={pending}
        error={liveState.error}
      />

      <section className="grid min-w-0 gap-4 2xl:grid-cols-[minmax(0,1.2fr)_minmax(420px,0.8fr)]">
        <div className="min-w-0 space-y-4">
          <BoardroomStage state={liveState} />
          <TimelinePanel state={liveState} />
        </div>
        <div className="grid min-w-0 gap-4 xl:grid-cols-2 2xl:grid-cols-1">
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
  );
}

function HistoryView({
  meetings,
  allMeetings,
  query,
  setQuery,
  favoriteOnly,
  setFavoriteOnly,
  decisionFilter,
  setDecisionFilter,
  loading,
  selectedMeetingIds,
  setSelectedMeetingIds,
  detail,
  onLoad,
  onOpen,
  onStart,
  onFavorite,
  onDelete
}: {
  meetings: MeetingSummary[];
  allMeetings: MeetingSummary[];
  query: string;
  setQuery: (query: string) => void;
  favoriteOnly: boolean;
  setFavoriteOnly: (value: boolean) => void;
  decisionFilter: string;
  setDecisionFilter: (value: string) => void;
  loading: boolean;
  selectedMeetingIds: string[];
  setSelectedMeetingIds: (ids: string[]) => void;
  detail: BoardMeetingDetail | null;
  onLoad: () => Promise<void>;
  onOpen: (meetingId: string) => Promise<void>;
  onStart: (payload: StartupBriefPayload) => void;
  onFavorite: (summary: MeetingSummary) => Promise<void>;
  onDelete: (summary: MeetingSummary) => Promise<void>;
}) {
  const selected = allMeetings.filter((meeting) => selectedMeetingIds.includes(meeting.meeting_id));

  function toggleSelected(meetingId: string) {
    if (selectedMeetingIds.includes(meetingId)) {
      setSelectedMeetingIds(selectedMeetingIds.filter((id) => id !== meetingId));
      return;
    }
    setSelectedMeetingIds([...selectedMeetingIds.slice(-1), meetingId]);
  }

  return (
    <div className="grid gap-4 2xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.8fr)]">
      <div className="min-w-0 space-y-4">
        <Panel icon={History} title="Meeting History" subtitle={`${meetings.length} results`}>
          <form
            className="mb-4 grid gap-2 lg:grid-cols-[minmax(0,1fr)_170px_auto_auto]"
            onSubmit={(event) => {
              event.preventDefault();
              void onLoad();
            }}
          >
            <div className="relative min-w-0">
              <Search
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-board-muted"
                aria-hidden="true"
              />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search history"
                className="pl-9"
              />
            </div>
            <select
              value={decisionFilter}
              onChange={(event) => setDecisionFilter(event.target.value)}
              className="h-10 rounded-md border border-white/10 bg-board-panel px-3 text-sm text-board-mist outline-none"
            >
              <option value="all">All decisions</option>
              <option value="approve">Approve</option>
              <option value="approve_with_conditions">Conditional</option>
              <option value="defer_pending_de_risking">Deferred</option>
              <option value="reject">Reject</option>
            </select>
            <Button
              type="button"
              variant={favoriteOnly ? "primary" : "quiet"}
              onClick={() => setFavoriteOnly(!favoriteOnly)}
            >
              {favoriteOnly ? <BookmarkCheck className="h-4 w-4" /> : <Bookmark className="h-4 w-4" />}
              Favorites
            </Button>
            <Button type="submit" variant="quiet" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Filter
            </Button>
          </form>

          {loading ? (
            <SkeletonRows />
          ) : meetings.length ? (
            <div className="space-y-3">
              {meetings.map((meeting) => (
                <article
                  key={meeting.meeting_id}
                  className="rounded-md border border-white/10 bg-white/[0.035] p-3"
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <button
                      type="button"
                      className="min-w-0 flex-1 text-left"
                      onClick={() => void onOpen(meeting.meeting_id)}
                    >
                      <div className="break-words text-sm font-semibold text-white">
                        {meeting.startup_idea}
                      </div>
                      <div className="mt-1 text-xs text-board-muted">
                        {meeting.industry} - {formatDate(meeting.completed_at ?? meeting.created_at)}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Badge tone={decisionTone(meeting.decision)}>{formatDecision(meeting.decision)}</Badge>
                        <Badge>{percent(meeting.aggregate_confidence)} confidence</Badge>
                        <Badge>{meeting.country}</Badge>
                      </div>
                    </button>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant={selectedMeetingIds.includes(meeting.meeting_id) ? "primary" : "quiet"}
                        onClick={() => toggleSelected(meeting.meeting_id)}
                      >
                        <BarChart3 className="h-4 w-4" />
                        Compare
                      </Button>
                      <Button
                        type="button"
                        size="icon"
                        variant="quiet"
                        title="Favorite"
                        onClick={() => void onFavorite(meeting)}
                      >
                        {meeting.is_favorite ? (
                          <BookmarkCheck className="h-4 w-4 text-board-amber" />
                        ) : (
                          <Bookmark className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        type="button"
                        size="icon"
                        variant="danger"
                        title="Delete"
                        onClick={() => void onDelete(meeting)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState icon={History} label="No matching meetings" />
          )}
        </Panel>

        {selected.length ? <ComparePanel meetings={selected} /> : null}
      </div>

      <div className="min-w-0 space-y-4">
        {detail ? (
          <HistoryDetailPanel detail={detail} onStart={onStart} />
        ) : (
          <Panel icon={FileText} title="Report Preview" subtitle="No report selected">
            <EmptyState icon={FileText} label="Open a meeting report" />
          </Panel>
        )}
      </div>
    </div>
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
    <form className="glass-panel rounded-lg p-4" onSubmit={onSubmit}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white">Founder Brief</h2>
          <p className="text-sm text-board-muted">Manual board meeting</p>
        </div>
        <Button type="submit" disabled={pending} title="Start live board meeting">
          {pending ? <Activity className="h-4 w-4 animate-pulse" /> : <Play className="h-4 w-4" />}
          Convene
        </Button>
      </div>

      <div className="max-h-[calc(100vh-220px)] space-y-4 overflow-y-auto pr-1">
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
  const top = roles.slice(0, 5);
  const left = roles.slice(5, 9);
  const right = roles.slice(9, 13);
  const bottom = roles.slice(13);

  return (
    <Panel
      icon={Wifi}
      title="Executive Boardroom"
      subtitle={state.meetingId ? `Meeting ${state.meetingId.slice(0, 8)}` : "Awaiting brief"}
    >
      <div className="grid gap-2 lg:hidden">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
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
      </div>

      <div className="hidden min-h-[640px] min-w-0 rounded-lg border border-white/10 bg-black/15 p-3 xl:block">
        <div className="grid h-full min-h-[612px] grid-rows-[auto_minmax(0,1fr)_auto] gap-3">
          <div className="grid grid-cols-5 gap-2">
            {top.map((role) => (
              <ExecutiveSeat key={role} role={role} state={state} active={state.activeRole === role} />
            ))}
          </div>

          <div className="grid min-h-0 grid-cols-[minmax(120px,170px)_minmax(0,1fr)_minmax(120px,170px)] gap-3">
            <div className="grid content-between gap-2">
              {left.map((role) => (
                <ExecutiveSeat key={role} role={role} state={state} active={state.activeRole === role} />
              ))}
            </div>

            <motion.div
              className="relative flex min-h-[360px] min-w-0 flex-col items-center justify-center overflow-hidden rounded-[2rem] border border-board-teal/25 bg-[radial-gradient(circle_at_center,rgba(56,214,198,0.16),rgba(17,21,27,0.72)_46%,rgba(7,9,13,0.9))] p-6 text-center shadow-glow"
              animate={{
                boxShadow:
                  state.status === "completed"
                    ? "0 0 0 1px rgba(56,214,198,0.45), 0 0 70px rgba(56,214,198,0.2)"
                    : "0 0 0 1px rgba(255,255,255,0.08), 0 24px 80px rgba(0,0,0,0.45)"
              }}
            >
              <div className="absolute inset-x-10 top-12 h-px bg-gradient-to-r from-transparent via-board-teal/40 to-transparent" />
              <div className="text-xs uppercase tracking-[0.18em] text-board-muted">Live Session</div>
              <div className="mt-3 max-w-xl break-words text-2xl font-semibold text-white">
                {state.status === "completed"
                  ? formatDecision(state.result?.decision ?? "Consensus")
                  : state.activeRole ?? "Board ready"}
              </div>
              <p className="mt-3 max-w-2xl break-words text-sm leading-6 text-board-muted">
                {latestTurn?.message ?? activeStatusLabel(state)}
              </p>
              <div className="mt-5 grid w-full max-w-xl grid-cols-3 gap-3">
                <StatPill label="Statements" value={String(state.timeline.length)} />
                <StatPill label="Votes" value={String(Object.keys(state.votes).length)} />
                <StatPill
                  label="Confidence"
                  value={
                    state.result ? percent(state.result.aggregate_confidence) : percent(averageLiveConfidence(state))
                  }
                />
              </div>
              {state.status === "running" ? <ThinkingDots /> : null}
            </motion.div>

            <div className="grid content-between gap-2">
              {right.map((role) => (
                <ExecutiveSeat key={role} role={role} state={state} active={state.activeRole === role} />
              ))}
            </div>
          </div>

          <div className="grid grid-cols-5 gap-2">
            {bottom.map((role) => (
              <ExecutiveSeat key={role} role={role} state={state} active={state.activeRole === role} />
            ))}
          </div>
        </div>
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
        scale: active ? 1.025 : 1,
        borderColor: active ? "rgba(56,214,198,0.7)" : "rgba(255,255,255,0.1)"
      }}
      className={cn(
        "min-w-0 rounded-md border bg-white/[0.045] p-2.5 transition",
        active ? "shadow-[0_0_35px_rgba(56,214,198,0.22)]" : "",
        compact ? "min-h-[112px]" : "min-h-[122px]"
      )}
    >
      <div className="flex min-w-0 items-start gap-2">
        <div
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-md border text-xs font-semibold",
            active
              ? "border-board-teal/60 bg-board-teal text-board-ink"
              : "border-white/10 bg-board-ink text-board-teal"
          )}
        >
          {initials(role)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="break-words text-sm font-medium leading-5 text-white">{role}</div>
          <div className="mt-1 break-words text-xs leading-4 text-board-muted">
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
        <span className={cn("break-words", voteColor(vote?.vote ?? "abstain"))}>
          {vote ? formatDecision(vote.vote) : "No vote"}
        </span>
        <span className="shrink-0 text-board-muted">
          {confidence ? Math.round(confidence * 100) : "--"}
        </span>
      </div>
      {active && state.status === "running" ? <ThinkingDots small /> : null}
    </motion.div>
  );
}

function TimelinePanel({ state }: { state: LiveMeetingState }) {
  return (
    <Panel icon={Layers3} title="Live Timeline" subtitle={`${state.timeline.length} statements`}>
      {state.timeline.length > 0 ? (
        <div className="max-h-[430px] overflow-y-auto pr-1">
          <div className="space-y-3">
            {state.timeline.map((turn, index) => (
              <motion.article
                key={`${turn.speaker_role}-${turn.sequence ?? index}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.22 }}
                className="grid min-w-0 gap-3 rounded-md border border-white/10 bg-white/[0.025] p-3 sm:grid-cols-[128px_minmax(0,1fr)]"
              >
                <div className="min-w-0">
                  <div className="text-xs text-board-muted">{formatTime(turn.occurred_at)}</div>
                  <div className="mt-2 break-words text-sm font-medium text-white">{turn.speaker_role}</div>
                  <div className="mt-1 break-words text-xs text-board-teal">{turn.topic ?? turn.turn_type}</div>
                  <div className="mt-2 text-xs text-board-muted">
                    {Math.round(turn.confidence * 100)} confidence
                  </div>
                </div>
                <div className="min-w-0">
                  <p className="break-words text-sm leading-6 text-board-mist">{turn.message}</p>
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
                "min-w-0 rounded-md border p-3",
                vote.changed
                  ? "border-board-amber/50 bg-board-amber/10"
                  : "border-white/10 bg-white/[0.035]"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="break-words text-sm font-medium text-white">{vote.role}</div>
                  <div className={cn("mt-1 break-words text-xs", voteColor(vote.vote))}>
                    {vote.previous_vote && vote.changed
                      ? `${formatDecision(vote.previous_vote)} -> ${formatDecision(vote.vote)}`
                      : formatDecision(vote.vote)}
                  </div>
                </div>
                <div className="shrink-0 text-sm text-board-mist">{Math.round(vote.confidence * 100)}</div>
              </div>
              <p className="mt-2 break-words text-xs leading-5 text-board-muted">{vote.rationale}</p>
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
              <div key={role} className="min-w-0">
                <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                  <span className="break-words text-board-muted">{role}</span>
                  <span className="shrink-0 text-board-mist">
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
                <p className="mt-1 break-words text-xs leading-5 text-board-muted">{latest?.reason}</p>
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
    <Panel icon={ShieldCheck} title="Risk Signals" subtitle={state.assessment ? "Board assessment" : "No assessment"}>
      {state.assessment ? (
        <div className="space-y-3">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-semibold text-white">
              {Math.round(state.assessment.overall_risk * 100)}
            </div>
            <div className="text-sm text-board-muted">overall risk</div>
          </div>
          <div className="max-h-[250px] space-y-3 overflow-y-auto pr-1">
            {riskEntries.map(([key, value]) => (
              <div key={key}>
                <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                  <span className="break-words text-board-muted">{titleCase(key)}</span>
                  <span className="shrink-0 text-board-mist">{Math.round(value * 100)}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className={cn(
                      "h-full rounded-full",
                      value > 0.72 ? "bg-board-rose" : value > 0.55 ? "bg-board-amber" : "bg-board-teal"
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
  const meetingId = state.result?.meeting_id ?? state.meetingId;

  return (
    <Panel
      icon={FileText}
      title="Board Report"
      subtitle={`${sections.length} streamed sections`}
      className="xl:col-span-2 2xl:col-span-1"
    >
      {meetingId && state.result ? (
        <div className="mb-4 flex flex-wrap gap-2">
          <ExportButton meetingId={meetingId} format="pdf" icon={Download}>
            PDF
          </ExportButton>
          <ExportButton meetingId={meetingId} format="markdown" icon={FileText}>
            Markdown
          </ExportButton>
          <ExportButton meetingId={meetingId} format="json" icon={FileJson}>
            JSON
          </ExportButton>
        </div>
      ) : null}

      {sections.length > 0 ? (
        <div className="grid min-h-0 gap-4 lg:grid-cols-[190px_minmax(0,1fr)] 2xl:grid-cols-1">
          <nav className="flex min-w-0 gap-2 overflow-x-auto pb-2 lg:max-h-[360px] lg:flex-col lg:overflow-y-auto lg:pb-0 lg:pr-1 2xl:max-h-none 2xl:flex-row 2xl:pb-2">
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
          <div className="max-h-[380px] min-w-0 overflow-y-auto rounded-md border border-white/10 bg-white/[0.025] p-4">
            <h3 className="mb-4 break-words text-lg font-semibold text-white">
              {state.reportSections[activeSection]?.section_title ?? sectionTitles[activeSection] ?? "Report Section"}
            </h3>
            {activeSection === "vc_readiness_score" && isScoreRecord(activeValue) ? (
              <ScoreGrid scores={activeValue} />
            ) : (
              <SectionValue value={activeValue} />
            )}
          </div>
        </div>
      ) : (
        <EmptyState icon={FileText} label="Report pending" />
      )}
    </Panel>
  );
}

function HistoryDetailPanel({
  detail,
  onStart
}: {
  detail: BoardMeetingDetail;
  onStart: (payload: StartupBriefPayload) => void;
}) {
  const sections = Object.entries(detail.report.sections);
  const vcScores = detail.report.sections.vc_readiness_score;

  return (
    <Panel icon={FileText} title="Report Preview" subtitle={formatDecision(detail.decision)}>
      <div className="space-y-4">
        <div className="rounded-md border border-white/10 bg-white/[0.035] p-3">
          <div className="break-words text-sm font-semibold text-white">{detail.startup_brief.startup_idea}</div>
          <div className="mt-1 text-xs text-board-muted">
            {detail.startup_brief.industry} - {detail.startup_brief.country}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge tone={decisionTone(detail.decision)}>{formatDecision(detail.decision)}</Badge>
            <Badge>{percent(detail.aggregate_confidence)} confidence</Badge>
            <Badge>{detail.status}</Badge>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={() => onStart(detail.startup_brief)}>
            <Play className="h-4 w-4" />
            Relaunch
          </Button>
          <ExportButton meetingId={detail.meeting_id} format="pdf" icon={Download}>
            PDF
          </ExportButton>
          <ExportButton meetingId={detail.meeting_id} format="markdown" icon={FileText}>
            Markdown
          </ExportButton>
          <ExportButton meetingId={detail.meeting_id} format="json" icon={FileJson}>
            JSON
          </ExportButton>
        </div>

        {isScoreRecord(vcScores) ? <ScoreGrid scores={vcScores} /> : null}

        <div className="max-h-[520px] space-y-3 overflow-y-auto pr-1">
          {sections.map(([key, value]) => (
            <details key={key} className="rounded-md border border-white/10 bg-white/[0.025] p-3" open={key === "executive_summary"}>
              <summary className="cursor-pointer text-sm font-semibold text-white">
                {sectionTitles[key] ?? titleCase(key)}
              </summary>
              <div className="mt-3">
                <SectionValue value={value} />
              </div>
            </details>
          ))}
        </div>
      </div>
    </Panel>
  );
}

function GlobalSearchPanel({
  results,
  onOpen
}: {
  results: GlobalSearchResults;
  onOpen: (meetingId: string) => void;
}) {
  return (
    <section className="mt-4 grid gap-4 xl:grid-cols-3">
      <Panel icon={Search} title="Search Results" subtitle={`"${results.query}"`}>
        <div className="space-y-3">
          {results.meetings.map((meeting) => (
            <button
              key={meeting.meeting_id}
              type="button"
              onClick={() => onOpen(meeting.meeting_id)}
              className="w-full rounded-md border border-white/10 bg-white/[0.035] p-3 text-left transition hover:border-board-teal/40"
            >
              <div className="break-words text-sm font-medium text-white">{meeting.startup_idea}</div>
              <div className="mt-1 text-xs text-board-muted">{formatDecision(meeting.decision)}</div>
            </button>
          ))}
          {!results.meetings.length ? <EmptyState icon={Search} label="No meeting matches" /> : null}
        </div>
      </Panel>

      <Panel icon={FileText} title="Reports" subtitle={`${results.reports.length} sections`}>
        <div className="space-y-3">
          {results.reports.map((report) => (
            <button
              key={`${report.report_id}-${report.section_key}`}
              type="button"
              onClick={() => onOpen(report.meeting_id)}
              className="w-full rounded-md border border-white/10 bg-white/[0.035] p-3 text-left transition hover:border-board-teal/40"
            >
              <div className="break-words text-sm font-medium text-white">{report.title}</div>
              <div className="mt-1 text-xs text-board-muted">{report.section_title}</div>
            </button>
          ))}
          {!results.reports.length ? <EmptyState icon={FileText} label="No report matches" /> : null}
        </div>
      </Panel>

      <Panel icon={Star} title="Executives" subtitle={`${results.executives.length} matches`}>
        <div className="space-y-3">
          {results.executives.map((executive) => (
            <div key={executive.role} className="rounded-md border border-white/10 bg-white/[0.035] p-3">
              <div className="text-sm font-medium text-white">{executive.role}</div>
              <p className="mt-1 break-words text-xs leading-5 text-board-muted">{executive.charter}</p>
            </div>
          ))}
          {!results.executives.length ? <EmptyState icon={Star} label="No executive matches" /> : null}
        </div>
      </Panel>
    </section>
  );
}

function StartupIdeaCard({
  idea,
  onStart
}: {
  idea: StartupIdea;
  onStart: (payload: StartupBriefPayload) => void;
}) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel flex min-w-0 flex-col rounded-lg p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="break-words text-lg font-semibold text-white">{idea.startup_name}</h3>
          <p className="mt-1 break-words text-sm text-board-muted">{idea.tagline}</p>
        </div>
        <GaugeCircle value={idea.success_probability} label="P" />
      </div>
      <div className="mt-4 grid gap-2">
        <IdeaFact label="Problem" value={idea.problem} />
        <IdeaFact label="Solution" value={idea.solution} />
        <IdeaFact label="Audience" value={idea.target_audience} />
        <IdeaFact label="TAM" value={idea.estimated_tam} />
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2">
        <StatPill label="Innov." value={String(idea.innovation_score)} />
        <StatPill label="Scale" value={String(idea.scalability_score)} />
        <StatPill label="Cost" value={compactMoney(idea.estimated_startup_cost)} />
      </div>
      <p className="mt-4 break-words text-xs leading-5 text-board-muted">{idea.competitive_advantage}</p>
      <div className="mt-4">
        <Button type="button" className="w-full" onClick={() => onStart(idea.meeting_brief)}>
          <Play className="h-4 w-4" />
          Launch Board Meeting
        </Button>
      </div>
    </motion.article>
  );
}

function StartupIdeaMiniCard({
  idea,
  onStart
}: {
  idea: StartupIdea;
  onStart: (payload: StartupBriefPayload) => void;
}) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.035] p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="break-words text-sm font-semibold text-white">{idea.startup_name}</div>
          <div className="mt-1 break-words text-xs text-board-muted">{idea.tagline}</div>
        </div>
        <Badge tone="teal">{idea.success_probability}%</Badge>
      </div>
      <Button type="button" size="sm" className="mt-3 w-full" onClick={() => onStart(idea.meeting_brief)}>
        <Play className="h-4 w-4" />
        Launch
      </Button>
    </div>
  );
}

function ReportSummaryCard({
  meeting,
  onOpen
}: {
  meeting: MeetingSummary;
  onOpen: (meetingId: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onOpen(meeting.meeting_id)}
      className="rounded-md border border-white/10 bg-white/[0.035] p-3 text-left transition hover:border-board-teal/40"
    >
      <div className="break-words text-sm font-semibold text-white">{meeting.report_title}</div>
      <div className="mt-1 break-words text-xs text-board-muted">{meeting.startup_idea}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Badge tone={decisionTone(meeting.decision)}>{formatDecision(meeting.decision)}</Badge>
        <Badge>{percent(meeting.aggregate_confidence)}</Badge>
      </div>
    </button>
  );
}

function ComparePanel({ meetings }: { meetings: MeetingSummary[] }) {
  return (
    <Panel icon={BarChart3} title="Comparison" subtitle={`${meetings.length} selected`}>
      <div className="grid gap-3 md:grid-cols-2">
        {meetings.map((meeting) => (
          <div key={meeting.meeting_id} className="rounded-md border border-white/10 bg-white/[0.035] p-3">
            <div className="break-words text-sm font-semibold text-white">{meeting.startup_idea}</div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <StatPill label="Decision" value={formatDecision(meeting.decision)} />
              <StatPill label="Confidence" value={percent(meeting.aggregate_confidence)} />
              <StatPill label="Industry" value={meeting.industry} />
              <StatPill label="Country" value={meeting.country} />
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function ScoreGrid({ scores }: { scores: Record<string, number> }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {Object.entries(scores).map(([key, value]) => (
        <div key={key} className="rounded-md border border-white/10 bg-white/[0.035] p-3">
          <div className="flex items-center justify-between gap-3">
            <span className="break-words text-sm text-board-muted">{titleCase(key)}</span>
            <span className="shrink-0 text-lg font-semibold text-white">{value}</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/[0.06]">
            <div
              className={cn("h-full rounded-full", value >= 76 ? "bg-board-teal" : value >= 56 ? "bg-board-amber" : "bg-board-rose")}
              style={{ width: `${Math.max(4, Math.min(100, value))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function ExportButton({
  meetingId,
  format,
  icon: Icon,
  children
}: {
  meetingId: string;
  format: "pdf" | "markdown" | "json";
  icon: LucideIcon;
  children: ReactNode;
}) {
  return (
    <Button type="button" variant="quiet" size="sm" asChild>
      <a href={reportExportUrl(meetingId, format)} target="_blank" rel="noreferrer">
        <Icon className="h-4 w-4" />
        {children}
      </a>
    </Button>
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
    <div className="inline-flex h-10 max-w-full items-center gap-2 rounded-md border border-white/10 bg-white/[0.04] px-3 text-sm text-board-mist">
      <Icon className={cn("h-4 w-4 shrink-0 text-board-teal", state.status === "running" && "animate-pulse")} />
      <span className="break-words">{label}</span>
    </div>
  );
}

function NavButton({
  active,
  icon: Icon,
  children,
  onClick
}: {
  active: boolean;
  icon: LucideIcon;
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <Button type="button" variant={active ? "primary" : "quiet"} size="sm" onClick={onClick}>
      <Icon className="h-4 w-4" />
      {children}
    </Button>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="glass-panel min-w-0 rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm text-board-muted">{label}</p>
          <div className="mt-2 break-words text-3xl font-semibold text-white">{value}</div>
          <p className="mt-1 break-words text-xs text-board-muted">{detail}</p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-board-teal">
          <Icon className="h-4 w-4" />
        </div>
      </div>
    </div>
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
    <section className={cn("glass-panel min-w-0 rounded-lg p-4", className)}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h2 className="break-words text-base font-semibold text-white">{title}</h2>
          <p className="break-words text-sm text-board-muted">{subtitle}</p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-board-teal">
          <Icon className="h-4 w-4" />
        </div>
      </div>
      {children}
    </section>
  );
}

function EmptyState({ icon: Icon, label }: { icon: LucideIcon; label: string }) {
  return (
    <div className="flex min-h-36 flex-col items-center justify-center rounded-md border border-dashed border-white/10 bg-white/[0.02] p-4 text-center">
      <Icon className="mb-3 h-5 w-5 text-board-muted" />
      <p className="break-words text-sm text-board-muted">{label}</p>
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

function Badge({
  children,
  tone = "muted"
}: {
  children: ReactNode;
  tone?: "muted" | "teal" | "amber" | "rose";
}) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center rounded-sm border px-2 py-1 text-xs",
        tone === "teal" && "border-board-teal/30 bg-board-teal/10 text-board-teal",
        tone === "amber" && "border-board-amber/30 bg-board-amber/10 text-board-amber",
        tone === "rose" && "border-board-rose/30 bg-board-rose/10 text-board-rose",
        tone === "muted" && "border-white/10 bg-white/[0.04] text-board-muted"
      )}
    >
      <span className="break-words">{children}</span>
    </span>
  );
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md border border-white/10 bg-white/[0.035] p-2">
      <div className="text-[11px] uppercase text-board-muted">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

function IdeaFact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] uppercase text-board-muted">{label}</div>
      <p className="mt-1 break-words text-sm leading-5 text-board-mist">{value}</p>
    </div>
  );
}

function GaugeCircle({ value, label }: { value: number; label: string }) {
  return (
    <div
      className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full"
      style={{
        background: `conic-gradient(#38d6c6 ${value * 3.6}deg, rgba(255,255,255,0.08) 0deg)`
      }}
      title={`${label} ${value}`}
    >
      <div className="flex h-12 w-12 flex-col items-center justify-center rounded-full bg-board-panel text-center">
        <span className="text-xs text-board-muted">{label}</span>
        <span className="text-sm font-semibold text-white">{value}</span>
      </div>
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
        <CircleAlert className="h-4 w-4 shrink-0" />
        Section unavailable
      </div>
    );
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return <p className="break-words text-sm leading-6 text-board-mist">{String(value)}</p>;
  }

  if (Array.isArray(value)) {
    return (
      <div className="space-y-3">
        {value.map((item, index) => (
          <div key={index} className="min-w-0 border-b border-white/10 pb-3 last:border-0 last:pb-0">
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
          <div key={key} className="min-w-0 border-b border-white/10 pb-4 last:border-0 last:pb-0">
            <div className="mb-2 break-words text-xs font-medium text-board-muted">{titleCase(key)}</div>
            <SectionValue value={nestedValue} />
          </div>
        ))}
      </div>
    );
  }

  return <p className="text-sm text-board-muted">Unsupported section value</p>;
}

function SkeletonRows() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="h-16 animate-pulse rounded-md bg-white/[0.05]" />
      ))}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="glass-panel rounded-lg p-4">
      <div className="h-5 w-2/3 animate-pulse rounded bg-white/[0.07]" />
      <div className="mt-3 h-4 w-full animate-pulse rounded bg-white/[0.05]" />
      <div className="mt-2 h-4 w-5/6 animate-pulse rounded bg-white/[0.05]" />
      <div className="mt-6 grid grid-cols-3 gap-2">
        <div className="h-14 animate-pulse rounded bg-white/[0.05]" />
        <div className="h-14 animate-pulse rounded bg-white/[0.05]" />
        <div className="h-14 animate-pulse rounded bg-white/[0.05]" />
      </div>
    </div>
  );
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

function formToPayload(form: BriefFormState): StartupBriefPayload {
  return {
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
  };
}

function formFromPayload(payload: StartupBriefPayload): BriefFormState {
  return {
    ...payload,
    competitorsText: payload.competitors.join(", ")
  };
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

function latestConfidence(points: ConfidencePoint[] | undefined) {
  return points?.at(-1)?.confidence ?? null;
}

function averageLiveConfidence(state: LiveMeetingState) {
  const values = Object.values(state.confidence)
    .map((points) => points.at(-1)?.confidence)
    .filter((value): value is number => typeof value === "number");
  if (!values.length) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
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
    .replace("Ai", "AI")
    .replace("Vc", "VC");
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

function formatDate(value?: string | null) {
  if (!value) {
    return "No date";
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    year: "numeric"
  }).format(new Date(value));
}

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function compactMoney(value: number) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1
  }).format(value);
}

function voteColor(vote: string) {
  if (vote === "approve") {
    return "text-board-teal";
  }
  if (vote === "approve_with_conditions") {
    return "text-board-amber";
  }
  if (vote === "reject" || vote === "defer_pending_de_risking") {
    return "text-board-rose";
  }
  return "text-board-muted";
}

function decisionTone(value: string): "muted" | "teal" | "amber" | "rose" {
  if (value === "approve") {
    return "teal";
  }
  if (value === "approve_with_conditions") {
    return "amber";
  }
  if (value === "reject" || value === "defer_pending_de_risking") {
    return "rose";
  }
  return "muted";
}

function isScoreRecord(value: unknown): value is Record<string, number> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    Object.values(value as Record<string, unknown>).every((item) => typeof item === "number")
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
