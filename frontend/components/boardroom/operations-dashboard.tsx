"use client";

import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Database,
  Gauge,
  HardDrive,
  Loader2,
  Play,
  Plug,
  RefreshCcw,
  Server,
  ShieldCheck,
  TimerReset,
  Users
} from "lucide-react";
import { type ReactNode, useCallback, useEffect, useMemo, useState } from "react";

import {
  createOperationsJob,
  fetchOperationsJobs,
  fetchOperationsMonitoring,
  fetchOperationsPlugins,
  fetchOperationsSchedules
} from "@/lib/api";
import { ENTERPRISE_COPY } from "@/lib/enterprise-copy";
import { formatCompactNumber, formatDateTime, formatNumber } from "@/lib/i18n";
import type {
  OperationsJob,
  OperationsJobsResponse,
  OperationsMonitoringSnapshot,
  OperationsPluginManifest,
  OperationsSchedule,
  OperationsSchedulesResponse
} from "@/lib/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type LoadState = {
  monitoring: OperationsMonitoringSnapshot | null;
  jobs: OperationsJobsResponse | null;
  schedules: OperationsSchedulesResponse | null;
  plugins: OperationsPluginManifest | null;
};

const INITIAL_STATE: LoadState = {
  monitoring: null,
  jobs: null,
  schedules: null,
  plugins: null
};

export function OperationsDashboard() {
  const [state, setState] = useState<LoadState>(INITIAL_STATE);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [enqueueing, setEnqueueing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const copy = ENTERPRISE_COPY.operations;

  const load = useCallback(async (mode: "initial" | "refresh" = "refresh") => {
    if (mode === "initial") {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError(null);
    try {
      const [monitoring, jobs, schedules, plugins] = await Promise.all([
        fetchOperationsMonitoring(),
        fetchOperationsJobs(),
        fetchOperationsSchedules(),
        fetchOperationsPlugins()
      ]);
      setState({ monitoring, jobs, schedules, plugins });
      setNotice(`${copy.lastUpdated}: ${formatDateTime(monitoring.generated_at)}`);
    } catch (loadError) {
      setError(messageFromError(loadError, copy.loadError));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [copy.lastUpdated, copy.loadError]);

  useEffect(() => {
    void load("initial");
  }, [load]);

  const summary = useMemo(() => deriveSummary(state, copy), [state, copy]);

  const enqueueAnalyticsRefresh = async () => {
    setEnqueueing(true);
    setError(null);
    try {
      const job = await createOperationsJob("analytics_refresh", {
        source: "operations_dashboard"
      });
      setNotice(`${copy.jobQueued}: ${job.id}`);
      await load();
    } catch (jobError) {
      setError(messageFromError(jobError, copy.jobError));
    } finally {
      setEnqueueing(false);
    }
  };

  if (loading && !state.monitoring) {
    return (
      <section
        aria-labelledby="operations-heading"
        className="glass-panel flex min-h-[420px] items-center justify-center rounded-lg p-6"
      >
        <div className="flex items-center gap-3 text-board-muted" role="status" aria-live="polite">
          <Loader2 className="h-5 w-5 animate-spin text-board-teal" aria-hidden="true" />
          {copy.loading}
        </div>
      </section>
    );
  }

  if (error && !state.monitoring) {
    return (
      <section aria-labelledby="operations-heading" className="glass-panel rounded-lg p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 id="operations-heading" className="text-lg font-semibold text-white">
              {copy.title}
            </h2>
            <p className="mt-1 text-sm text-board-muted">{error}</p>
          </div>
          <Button type="button" variant="quiet" onClick={() => load("initial")}>
            <RefreshCcw className="h-4 w-4" aria-hidden="true" />
            {copy.refresh}
          </Button>
        </div>
      </section>
    );
  }

  return (
    <section aria-labelledby="operations-heading" className="space-y-4">
      <div className="glass-panel rounded-lg p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 id="operations-heading" className="text-xl font-semibold text-white">
              {copy.title}
            </h2>
            <p className="mt-1 text-sm text-board-muted">{copy.subtitle}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="quiet"
              aria-label={copy.refresh}
              onClick={() => load()}
              disabled={refreshing}
            >
              {refreshing ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <RefreshCcw className="h-4 w-4" aria-hidden="true" />
              )}
              {copy.refresh}
            </Button>
            <Button
              type="button"
              aria-label={copy.queueRefresh}
              onClick={enqueueAnalyticsRefresh}
              disabled={enqueueing}
            >
              {enqueueing ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Play className="h-4 w-4" aria-hidden="true" />
              )}
              {copy.queueRefresh}
            </Button>
          </div>
        </div>
        <div className="mt-3 min-h-5 text-sm text-board-muted" role="status" aria-live="polite">
          {error ?? notice}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric icon={Gauge} label={copy.apiLatency} value={summary.latency} detail={copy.p95Latency} />
        <Metric icon={Activity} label={copy.requests} value={summary.requests} detail={copy.activeRequests} />
        <Metric icon={Users} label={copy.activeUsers} value={summary.activeUsers} detail={copy.liveSessions} />
        <Metric icon={HardDrive} label={copy.memory} value={summary.memory} detail={copy.processMemory} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.85fr)]">
        <Panel icon={Server} title={copy.dependencies}>
          <StatusGrid items={summary.dependencies} />
        </Panel>

        <Panel icon={Database} title={copy.storage}>
          <div className="grid gap-3 sm:grid-cols-3">
            <SmallStat label={copy.cache} value={summary.cacheStatus} />
            <SmallStat label={copy.queueSize} value={summary.queueSize} />
            <SmallStat label={copy.deadLetter} value={summary.deadLetterSize} tone="rose" />
          </div>
        </Panel>

        <Panel icon={Clock3} title={copy.jobs}>
          <JobList jobs={state.jobs?.jobs ?? []} empty={copy.emptyJobs} />
        </Panel>

        <Panel icon={TimerReset} title={copy.schedules}>
          <ScheduleList schedules={state.schedules?.schedules ?? []} empty={copy.emptySchedules} />
        </Panel>

        <Panel icon={ShieldCheck} title={copy.providers}>
          <StatusGrid items={summary.providers} />
        </Panel>

        <Panel icon={Plug} title={copy.plugins}>
          <div className="grid gap-3 sm:grid-cols-3">
            <SmallStat label={copy.registeredPlugins} value={summary.plugins} />
            <SmallStat label={copy.pluginTypes} value={summary.pluginTypes} />
            <SmallStat label={copy.versioning} value={copy.apiVersions} tone="teal" />
          </div>
        </Panel>
      </div>
    </section>
  );
}

function deriveSummary(state: LoadState, copy: typeof ENTERPRISE_COPY.operations) {
  const monitoring = state.monitoring;
  const jobs = state.jobs?.stats ?? monitoring?.jobs;
  const providers = providerRows(monitoring?.providers);
  const dependencies = statusRows(monitoring?.dependencies ?? {});
  const memoryBytes =
    monitoring?.process.rss_bytes ?? monitoring?.process.memory_bytes?.tracemalloc_current ?? 0;
  return {
    latency: `${formatNumber(monitoring?.api.latency_ms.average ?? 0)} ms`,
    requests: formatCompactNumber(monitoring?.api.request_count ?? 0),
    activeUsers: formatNumber(monitoring?.active_users ?? 0),
    activeRequests: `${copy.activeRequests}: ${formatNumber(monitoring?.api.active_requests ?? 0)}`,
    liveSessions: copy.liveSessions,
    memory: formatBytes(memoryBytes),
    processMemory: copy.processMemory,
    p95Latency: `${copy.p95Latency}: ${formatNumber(monitoring?.api.latency_ms.p95 ?? 0)} ms`,
    queueSize: formatNumber(jobs?.queue_size ?? 0),
    deadLetterSize: formatNumber(jobs?.dead_letter_size ?? 0),
    cacheStatus: stringAt(monitoring?.cache ?? {}, "status", stringAt(monitoring?.cache ?? {}, "backend", "unknown")),
    dependencies,
    providers,
    plugins: formatNumber(state.plugins?.plugins.length ?? 0),
    pluginTypes: formatNumber(state.plugins?.plugin_types.length ?? 0)
  };
}

function Metric({
  icon: Icon,
  label,
  value,
  detail
}: {
  icon: typeof Activity;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="glass-panel rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words text-xs uppercase tracking-[0.16em] text-board-muted">{label}</p>
          <div className="mt-3 break-words text-2xl font-semibold text-white">{value}</div>
          <p className="mt-1 break-words text-xs text-board-muted">{detail}</p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-board-teal">
          <Icon className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}

function Panel({
  icon: Icon,
  title,
  children
}: {
  icon: typeof Activity;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="glass-panel rounded-lg p-4">
      <div className="mb-4 flex items-center gap-2">
        <Icon className="h-4 w-4 text-board-teal" aria-hidden="true" />
        <h3 className="break-words text-sm font-semibold uppercase tracking-[0.16em] text-board-muted">
          {title}
        </h3>
      </div>
      {children}
    </section>
  );
}

function StatusGrid({ items }: { items: Array<{ name: string; status: string; detail: string }> }) {
  if (!items.length) {
    return <EmptyState label={ENTERPRISE_COPY.operations.emptyStatus} />;
  }
  return (
    <div className="grid gap-2 md:grid-cols-2">
      {items.map((item) => (
        <div key={item.name} className="rounded-md border border-white/10 bg-white/[0.025] p-3">
          <div className="flex items-center justify-between gap-2">
            <span className="min-w-0 break-words text-sm font-medium text-white">{titleCase(item.name)}</span>
            <StatusBadge status={item.status} />
          </div>
          <p className="mt-2 break-words text-xs leading-5 text-board-muted">{item.detail}</p>
        </div>
      ))}
    </div>
  );
}

function JobList({ jobs, empty }: { jobs: OperationsJob[]; empty: string }) {
  if (!jobs.length) {
    return <EmptyState label={empty} />;
  }
  return (
    <div className="space-y-2">
      {jobs.slice(0, 8).map((job) => (
        <div key={job.id} className="rounded-md border border-white/10 bg-white/[0.025] p-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="break-words text-sm font-medium text-white">{titleCase(job.type)}</p>
              <p className="mt-1 break-all text-xs text-board-muted">{job.id}</p>
            </div>
            <StatusBadge status={job.status} />
          </div>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-board-teal"
              style={{ width: `${Math.max(0, Math.min(100, job.progress))}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-board-muted">
            {formatNumber(job.progress)}% | {formatDateTime(job.updated_at)}
          </p>
        </div>
      ))}
    </div>
  );
}

function ScheduleList({ schedules, empty }: { schedules: OperationsSchedule[]; empty: string }) {
  if (!schedules.length) {
    return <EmptyState label={empty} />;
  }
  return (
    <div className="space-y-2">
      {schedules.slice(0, 8).map((schedule) => (
        <div key={schedule.id} className="rounded-md border border-white/10 bg-white/[0.025] p-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="break-words text-sm font-medium text-white">{schedule.name}</p>
              <p className="mt-1 break-words text-xs text-board-muted">
                {schedule.cron} | {titleCase(schedule.job_type)}
              </p>
            </div>
            <StatusBadge status={schedule.enabled ? "enabled" : "disabled"} />
          </div>
          <p className="mt-2 text-xs text-board-muted">
            {ENTERPRISE_COPY.operations.nextRun}: {formatDateTime(schedule.next_run_at)}
          </p>
        </div>
      ))}
    </div>
  );
}

function SmallStat({
  label,
  value,
  tone = "muted"
}: {
  label: string;
  value: string;
  tone?: "muted" | "teal" | "rose";
}) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.025] p-3">
      <p className="break-words text-xs uppercase tracking-[0.14em] text-board-muted">{label}</p>
      <p
        className={cn(
          "mt-2 break-words text-lg font-semibold",
          tone === "teal" && "text-board-teal",
          tone === "rose" && "text-board-rose",
          tone === "muted" && "text-white"
        )}
      >
        {value}
      </p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const healthy = ["ok", "healthy", "up", "active", "enabled", "available", "configured"].includes(
    normalized
  );
  const warning = ["degraded", "unknown", "compatibility", "disabled", "queued", "running"].includes(
    normalized
  );
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1 rounded-sm border px-2 py-1 text-xs",
        healthy && "border-board-teal/30 bg-board-teal/10 text-board-teal",
        warning && "border-board-amber/30 bg-board-amber/10 text-board-amber",
        !healthy && !warning && "border-board-rose/30 bg-board-rose/10 text-board-rose"
      )}
    >
      {healthy ? (
        <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
      ) : (
        <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
      )}
      <span className="break-words">{titleCase(status)}</span>
    </span>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.025] p-3 text-sm text-board-muted">
      {label}
    </div>
  );
}

function statusRows(source: Record<string, unknown>) {
  return Object.entries(source).map(([name, value]) => {
    const record = asRecord(value);
    return {
      name,
      status: stringAt(record, "status", stringAt(record, "state", "unknown")),
      detail: statusDetail(record)
    };
  });
}

function providerRows(source: OperationsMonitoringSnapshot["providers"] | null | undefined) {
  const record = asRecord(source);
  const rawProviders = record.providers;
  if (!Array.isArray(rawProviders)) {
    return [];
  }
  return rawProviders.slice(0, 8).map((entry) => {
    const provider = asRecord(entry);
    const name = stringAt(provider, "name", stringAt(provider, "type", "provider"));
    const latency = provider.latency_ms == null ? "" : `${formatNumber(Number(provider.latency_ms))} ms`;
    return {
      name,
      status: stringAt(provider, "status", "unknown"),
      detail: [stringAt(provider, "type", ""), latency, stringAt(provider, "error", "")]
        .filter(Boolean)
        .join(" | ")
    };
  });
}

function statusDetail(record: Record<string, unknown>) {
  const latency = record.latency_ms == null ? "" : `${formatNumber(Number(record.latency_ms))} ms`;
  const backend = stringAt(record, "backend", "");
  const detail = stringAt(record, "detail", stringAt(record, "note", stringAt(record, "error", "")));
  return (
    [backend, latency, detail].filter(Boolean).join(" | ") ||
    ENTERPRISE_COPY.operations.noAdditionalDetail
  );
}

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function stringAt(record: Record<string, unknown>, key: string, fallback: string) {
  const value = record[key];
  return typeof value === "string" && value.trim() ? value : fallback;
}

function titleCase(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatBytes(value: number) {
  if (!Number.isFinite(value) || value <= 0) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB"];
  let size = value;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${formatNumber(Number(size.toFixed(size >= 10 ? 0 : 1)))} ${units[unitIndex]}`;
}

function messageFromError(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}
