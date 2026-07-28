"use client";

import {
  Activity,
  BrainCircuit,
  Database,
  FileText,
  GitBranch,
  Loader2,
  Search,
  Send,
  ShieldCheck,
  Upload,
  Users,
  Workflow
} from "lucide-react";
import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";

import {
  askEnterpriseAssistant,
  fetchEnterpriseIntelligenceSuite,
  fetchGlobalEnterpriseSearch,
  importEnterpriseDocument,
  runEnterpriseWorkflow
} from "@/lib/api";
import { ENTERPRISE_COPY } from "@/lib/enterprise-copy";
import type {
  EnterpriseAssistantAnswer,
  EnterpriseDocumentImportResult,
  EnterpriseIntelligenceSuite,
  EnterpriseWorkflowRunResult,
  GlobalEnterpriseSearchResults
} from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type IconComponent = typeof Activity;

export function GlobalEnterpriseSuite() {
  const [suite, setSuite] = useState<EnterpriseIntelligenceSuite | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [assistantAnswer, setAssistantAnswer] = useState<EnterpriseAssistantAnswer | null>(null);
  const [asking, setAsking] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<GlobalEnterpriseSearchResults | null>(null);
  const [searching, setSearching] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [documentResult, setDocumentResult] = useState<EnterpriseDocumentImportResult | null>(
    null
  );
  const [workflowResult, setWorkflowResult] = useState<EnterpriseWorkflowRunResult | null>(null);
  const [runningWorkflow, setRunningWorkflow] = useState(false);

  const copy = ENTERPRISE_COPY.intelligence;

  const loadSuite = async () => {
    setLoading(true);
    setError(null);
    try {
      setSuite(await fetchEnterpriseIntelligenceSuite());
    } catch (loadError) {
      setError(messageFromError(loadError, ENTERPRISE_COPY.errors.intelligence));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSuite();
  }, []);

  const derived = useMemo(() => deriveSuiteMetrics(suite), [suite]);

  const handleAsk = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }
    setAsking(true);
    try {
      setAssistantAnswer(await askEnterpriseAssistant(trimmed));
    } catch (askError) {
      setAssistantAnswer({
        question: trimmed,
        answer: messageFromError(askError, "Assistant request failed."),
        source_count: 0,
        sources: [],
        recommended_actions: [],
        limitations: [],
        generated_at: new Date().toISOString()
      });
    } finally {
      setAsking(false);
    }
  };

  const handleSearch = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      return;
    }
    setSearching(true);
    try {
      setSearchResults(await fetchGlobalEnterpriseSearch(trimmed));
    } finally {
      setSearching(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      return;
    }
    setUploading(true);
    try {
      const contentBase64 = await fileToBase64(selectedFile);
      setDocumentResult(
        await importEnterpriseDocument({
          filename: selectedFile.name,
          content_base64: contentBase64,
          mime_type: selectedFile.type || undefined,
          tags: ["frontend_import"]
        })
      );
      await loadSuite();
    } finally {
      setUploading(false);
    }
  };

  const handleWorkflow = async () => {
    setRunningWorkflow(true);
    try {
      setWorkflowResult(
        await runEnterpriseWorkflow({
          trigger: "manual",
          actions: ["assign_tasks", "notify_executives", "update_dashboard"]
        })
      );
      await loadSuite();
    } finally {
      setRunningWorkflow(false);
    }
  };

  if (loading && !suite) {
    return (
      <section className="glass-panel flex min-h-[420px] items-center justify-center rounded-lg p-6">
        <div className="flex items-center gap-3 text-board-muted">
          <Loader2 className="h-5 w-5 animate-spin text-board-teal" />
          {ENTERPRISE_COPY.loading.intelligence}
        </div>
      </section>
    );
  }

  if (error && !suite) {
    return (
      <section className="glass-panel rounded-lg p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">{ENTERPRISE_COPY.errors.workspace}</h2>
            <p className="mt-1 text-sm text-board-muted">{error}</p>
          </div>
          <Button type="button" variant="quiet" onClick={loadSuite}>
            Retry
          </Button>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="glass-panel rounded-lg p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">{copy.title}</h2>
            <p className="mt-1 text-sm text-board-muted">{copy.subtitle}</p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-board-muted">
            <Badge>{derived.providerMode}</Badge>
            <Badge>{derived.generatedAt}</Badge>
          </div>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Metric icon={BrainCircuit} label={copy.memory} value={derived.decisions} />
        <Metric icon={GitBranch} label={copy.graph} value={derived.graphNodes} />
        <Metric icon={Activity} label={copy.analytics} value={derived.averageConfidence} />
        <Metric icon={ShieldCheck} label={copy.observability} value={derived.providerHealth} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
        <Section icon={BrainCircuit} title={copy.assistant}>
          <form className="space-y-3" onSubmit={handleAsk}>
            <Textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={copy.questionPlaceholder}
            />
            <Button type="submit" disabled={asking || !question.trim()}>
              {asking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              {copy.ask}
            </Button>
          </form>
          {assistantAnswer ? (
            <div className="mt-4 rounded-md border border-white/10 bg-white/[0.035] p-3">
              <p className="text-sm leading-6 text-board-mist">{assistantAnswer.answer}</p>
              <MiniList
                className="mt-3"
                items={assistantAnswer.recommended_actions}
                empty={copy.empty}
              />
            </div>
          ) : null}
        </Section>

        <Section icon={Search} title={copy.search}>
          <form className="flex gap-2" onSubmit={handleSearch}>
            <Input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder={copy.searchPlaceholder}
            />
            <Button type="submit" variant="quiet" disabled={searching || !searchQuery.trim()}>
              {searching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </form>
          <div className="mt-4 space-y-2">
            {(searchResults?.items ?? []).slice(0, 7).map((item, index) => (
              <RecordRow key={`${item.collection ?? "item"}-${index}`} item={item} />
            ))}
            {searchResults && !searchResults.items.length ? (
              <EmptyLine label={copy.empty} />
            ) : null}
          </div>
        </Section>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Section icon={FileText} title={copy.documents}>
          <div className="space-y-3">
            <Input
              type="file"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
            <Button type="button" variant="quiet" disabled={!selectedFile || uploading} onClick={handleUpload}>
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              {copy.upload}
            </Button>
          </div>
          {documentResult ? (
            <div className="mt-4 rounded-md border border-white/10 bg-white/[0.035] p-3 text-sm">
              <div className="font-medium text-white">
                {textAt(documentResult.document, "filename", "Document imported")}
              </div>
              <p className="mt-1 leading-6 text-board-muted">
                {textAt(documentResult.document, "summary", copy.empty)}
              </p>
            </div>
          ) : null}
        </Section>

        <Section icon={Workflow} title={copy.workflows}>
          <Button type="button" variant="quiet" disabled={runningWorkflow} onClick={handleWorkflow}>
            {runningWorkflow ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Workflow className="h-4 w-4" />
            )}
            {copy.runWorkflow}
          </Button>
          <div className="mt-4 space-y-2">
            {asRecords(workflowResult?.workflow.executed).map((item, index) => (
              <RecordRow key={`workflow-${index}`} item={item} />
            ))}
            {workflowResult && !asRecords(workflowResult.workflow.executed).length ? (
              <EmptyLine label={copy.empty} />
            ) : null}
          </div>
        </Section>

        <Section icon={Users} title={copy.collaboration}>
          <MiniRecords
            items={asRecords(asRecord(suite?.collaboration).active_users).slice(0, 5)}
            empty={copy.empty}
          />
        </Section>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Section icon={BrainCircuit} title={copy.memory}>
          <MiniRecords items={derived.executiveMemory.slice(0, 6)} empty={copy.empty} />
        </Section>

        <Section icon={GitBranch} title={copy.graph}>
          <MiniRecords items={derived.graphPreview.slice(0, 8)} empty={copy.noGraph} />
        </Section>

        <Section icon={Database} title={copy.observability}>
          <MiniRecords items={derived.providerRows.slice(0, 7)} empty={copy.empty} />
        </Section>
      </div>
    </section>
  );
}

function Section({
  icon: Icon,
  title,
  children
}: {
  icon: IconComponent;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="glass-panel rounded-lg p-4">
      <div className="mb-4 flex items-center gap-2">
        <Icon className="h-4 w-4 text-board-teal" aria-hidden="true" />
        <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-board-muted">
          {title}
        </h3>
      </div>
      {children}
    </section>
  );
}

function Metric({ icon: Icon, label, value }: { icon: IconComponent; label: string; value: string }) {
  return (
    <div className="glass-panel rounded-lg p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs uppercase tracking-[0.18em] text-board-muted">{label}</span>
        <Icon className="h-4 w-4 text-board-teal" aria-hidden="true" />
      </div>
      <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}

function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-md border border-white/10 bg-white/[0.04] px-2.5 py-1 text-board-mist">
      {children}
    </span>
  );
}

function MiniList({
  items,
  empty,
  className
}: {
  items: string[];
  empty: string;
  className?: string;
}) {
  if (!items.length) {
    return <EmptyLine className={className} label={empty} />;
  }
  return (
    <ul className={`space-y-2 ${className ?? ""}`}>
      {items.slice(0, 5).map((item) => (
        <li key={item} className="rounded-md border border-white/10 bg-white/[0.025] px-3 py-2 text-sm text-board-muted">
          {item}
        </li>
      ))}
    </ul>
  );
}

function MiniRecords({ items, empty }: { items: Array<Record<string, unknown>>; empty: string }) {
  if (!items.length) {
    return <EmptyLine label={empty} />;
  }
  return (
    <div className="space-y-2">
      {items.map((item, index) => (
        <RecordRow key={`${textAt(item, "id", "record")}-${index}`} item={item} />
      ))}
    </div>
  );
}

function RecordRow({ item }: { item: Record<string, unknown> }) {
  const title =
    textAt(item, "title") ||
    textAt(item, "label") ||
    textAt(item, "display_name") ||
    textAt(item, "business_idea") ||
    textAt(item, "startup_idea") ||
    textAt(item, "name") ||
    textAt(item, "role") ||
    textAt(item, "collection", "Record");
  const detail =
    textAt(item, "status") ||
    textAt(item, "decision") ||
    textAt(item, "recommendation") ||
    textAt(item, "relationship") ||
    textAt(item, "confidence") ||
    textAt(item, "priority");
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.035] p-3">
      <div className="break-words text-sm font-medium text-white">{title}</div>
      {detail ? <div className="mt-1 break-words text-xs text-board-muted">{detail}</div> : null}
    </div>
  );
}

function EmptyLine({ label, className }: { label: string; className?: string }) {
  return <div className={`rounded-md border border-dashed border-white/10 p-3 text-sm text-board-muted ${className ?? ""}`}>{label}</div>;
}

function deriveSuiteMetrics(suite: EnterpriseIntelligenceSuite | null) {
  const memory = asRecord(suite?.memory);
  const decisionHistory = asRecord(memory.decision_history);
  const graph = asRecord(suite?.knowledge_graph);
  const graphCounts = asRecord(graph.counts);
  const analytics = asRecord(suite?.analytics);
  const meetingEffectiveness = asRecord(analytics.meeting_effectiveness);
  const observability = asRecord(suite?.observability);
  const providerRows = asRecords(observability.provider_health);
  const graphPreview = asRecords(graph.nodes);
  const executiveMemory = asRecords(memory.executive_memory);
  const providerMode = providerRows.length ? `${providerRows.length} providers` : ENTERPRISE_COPY.intelligence.fallback;
  const generatedAt =
    textAt(memory, "generated_at") ||
    textAt(graph, "generated_at") ||
    textAt(observability, "generated_at", "Ready");
  const confidence = numberAt(meetingEffectiveness, "average_confidence");

  return {
    decisions: String(numberAt(decisionHistory, "total")),
    graphNodes: `${numberAt(graphCounts, "nodes")} nodes`,
    averageConfidence: confidence ? `${Math.round(confidence * 100)}%` : "0%",
    providerHealth: providerMode,
    generatedAt,
    providerMode,
    providerRows,
    graphPreview,
    executiveMemory
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function asRecords(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function textAt(record: Record<string, unknown>, key: string, fallback = ""): string {
  const value = record[key];
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return fallback;
}

function numberAt(record: Record<string, unknown>, key: string) {
  const value = record[key];
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function messageFromError(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function fileToBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const value = String(reader.result ?? "");
      resolve(value.includes(",") ? value.split(",", 2)[1] : value);
    };
    reader.onerror = () => reject(new Error("File could not be read."));
    reader.readAsDataURL(file);
  });
}
