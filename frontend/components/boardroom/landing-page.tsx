import {
  Activity,
  ArrowRight,
  BrainCircuit,
  Building2,
  CheckCircle2,
  Cloud,
  Database,
  Github,
  LineChart,
  LockKeyhole,
  MapPin,
  Server,
  ShieldCheck,
  Sparkles,
  Users,
  type LucideIcon
} from "lucide-react";
import Image from "next/image";
import type { Route } from "next";
import Link from "next/link";

import { APP_NAME, APP_VERSION, RELEASE_CHANNEL } from "@/lib/app-config";
import { Button } from "@/components/ui/button";

const featureGroups = [
  {
    icon: BrainCircuit,
    title: "AI Boardroom",
    body: "Nineteen executive roles debate, challenge assumptions, vote, and stream decision artifacts in real time."
  },
  {
    icon: MapPin,
    title: "Business Intelligence",
    body: "Local-business analysis combines user inputs, live provider evidence, financial assumptions, and validation tasks."
  },
  {
    icon: Building2,
    title: "Enterprise Workspace",
    body: "Organizations, teams, approvals, tasks, comments, audit events, templates, analytics, and executive dashboards."
  },
  {
    icon: ShieldCheck,
    title: "Evidence Provenance",
    body: "Recommendations separate live evidence, historical evidence, user-provided information, and AI inference."
  }
];

const deploymentTargets = ["Vercel", "Railway", "Render", "Fly.io", "Docker", "Desktop"];
const workspaceRoute = "/workspace" as Route;
const demoRoute = "/workspace?auth=demo" as Route;

export function LandingPage() {
  const githubUrl = process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/";

  return (
    <main className="min-h-screen bg-board-ink text-board-mist">
      <section className="relative isolate min-h-[92vh] overflow-hidden border-b border-white/10">
        <div className="absolute inset-0 opacity-80">
          <ProductPreview />
        </div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_30%,rgba(56,214,198,0.18),transparent_34%),linear-gradient(90deg,rgba(7,9,13,0.96),rgba(7,9,13,0.78)_48%,rgba(7,9,13,0.35))]" />
        <div className="relative z-10 mx-auto flex min-h-[92vh] max-w-7xl flex-col justify-between px-4 py-5">
          <nav className="flex flex-wrap items-center justify-between gap-3">
            <Link href="/" className="flex items-center gap-3">
              <Image src="/boardroom-mark.svg" alt="" width={36} height={36} />
              <div>
                <div className="text-sm font-semibold text-white">{APP_NAME}</div>
                <div className="text-xs text-board-muted">{RELEASE_CHANNEL} / {APP_VERSION}</div>
              </div>
            </Link>
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="quiet" size="sm">
                <Link href={workspaceRoute}>Workspace</Link>
              </Button>
              <Button asChild size="sm">
                <Link href={demoRoute}>
                  Demo
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </nav>

          <div className="max-w-4xl py-20 md:py-28">
            <div className="mb-4 inline-flex rounded-sm border border-board-teal/30 bg-board-teal/10 px-3 py-1 text-sm text-board-teal">
              Production-ready executive AI decision platform
            </div>
            <h1 className="max-w-4xl break-words text-5xl font-semibold text-white md:text-7xl">
              BoardroomAI
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-board-mist">
              A public, cloud-ready AI operating system for founder decisions, local-business
              intelligence, enterprise approvals, and evidence-backed board reports.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild>
                <Link href={demoRoute}>
                  Try the live demo
                  <Sparkles className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="quiet">
                <a href={githubUrl} target="_blank" rel="noreferrer">
                  <Github className="h-4 w-4" />
                  GitHub
                </a>
              </Button>
              <Button asChild variant="quiet">
                <Link href={workspaceRoute}>Sign in</Link>
              </Button>
            </div>
          </div>

          <div className="grid gap-3 pb-3 sm:grid-cols-3">
            <HeroMetric label="Deployment targets" value="6" />
            <HeroMetric label="Executive roles" value="19" />
            <HeroMetric label="Evidence modes" value="Live / Manual / Demo" />
          </div>
        </div>
      </section>

      <section className="border-b border-white/10 px-4 py-16">
        <div className="mx-auto max-w-7xl">
          <SectionHeader
            eyebrow="Product Overview"
            title="One platform for decisions, evidence, workflow, and replay."
            body="BoardroomAI is built for recruiters, investors, startups, and enterprise demos: it can run locally, in Docker, or across common cloud platforms without changing application code."
          />
          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {featureGroups.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-white/10 px-4 py-16">
        <div className="mx-auto grid max-w-7xl gap-8 xl:grid-cols-[minmax(0,1fr)_420px]">
          <div>
            <SectionHeader
              eyebrow="Screenshots"
              title="Portfolio-ready product surfaces."
              body="The demo opens with seeded workflows, live meeting progress, enterprise diagnostics, provider health, and export-ready reports."
            />
            <div className="mt-8 grid gap-4 md:grid-cols-2">
              <ScreenshotPanel title="Live Board Meeting" />
              <ScreenshotPanel title="Enterprise Dashboard" />
              <ScreenshotPanel title="Business Decision Brief" />
              <ScreenshotPanel title="Provider Health" />
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
            <div className="mb-4 flex items-center gap-2 text-board-teal">
              <Cloud className="h-4 w-4" />
              <span className="text-sm font-semibold">Deployment Targets</span>
            </div>
            <div className="grid gap-2">
              {deploymentTargets.map((target) => (
                <div key={target} className="flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.035] p-3 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-board-teal" />
                  {target}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-white/10 px-4 py-16">
        <div className="mx-auto max-w-7xl">
          <SectionHeader
            eyebrow="Architecture"
            title="Clean backend domains with a cloud-ready frontend shell."
            body="The system keeps orchestration, business intelligence, enterprise workflows, providers, persistence, and desktop packaging in clear layers."
          />
          <div className="mt-8 grid gap-3 md:grid-cols-5">
            {[
              ["Next.js", "Landing page, workspace, demo mode"],
              ["FastAPI", "Versioned APIs, auth, diagnostics"],
              ["Domain", "Boardroom, BI, enterprise logic"],
              ["Providers", "AI and real-world evidence"],
              ["Data", "Postgres, Redis, Qdrant"]
            ].map(([title, body], index) => (
              <ArchitectureStep key={title} index={index + 1} title={title} body={body} />
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-white/10 px-4 py-16">
        <div className="mx-auto grid max-w-7xl gap-4 md:grid-cols-3">
          <InfoPanel
            icon={Users}
            title="AI Board"
            body="Executives take role-specific stances, update confidence, vote, and produce replayable decision records."
          />
          <InfoPanel
            icon={Database}
            title="Business Intelligence"
            body="Live providers enrich decisions with maps, places, weather, news, currency, open data, and demographics."
          />
          <InfoPanel
            icon={LockKeyhole}
            title="Enterprise Intelligence"
            body="Role-aware collaboration, approval workflows, audit trails, secure exports, and admin diagnostics."
          />
        </div>
      </section>

      <section className="px-4 py-16">
        <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-[minmax(0,1fr)_360px]">
          <div>
            <SectionHeader
              eyebrow="Documentation"
              title="Ready for engineering review."
              body="Deployment, environment, architecture, API, enterprise, desktop, troubleshooting, and developer guides are included in the repository."
            />
            <div className="mt-6 flex flex-wrap gap-2">
              {["README", "Deployment", "Environment", "API", "Architecture", "Enterprise"].map((item) => (
                <span key={item} className="rounded-sm border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-board-muted">
                  {item}
                </span>
              ))}
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
            <h2 className="text-lg font-semibold text-white">Contact</h2>
            <p className="mt-2 text-sm leading-6 text-board-muted">
              Use the demo for a fast product walkthrough or connect the deployment to your own
              provider keys for production evaluation.
            </p>
            <div className="mt-4 grid gap-2">
              <Button asChild>
                <Link href={demoRoute}>Open recruiter demo</Link>
              </Button>
              <Button asChild variant="quiet">
                <a href="mailto:hello@boardroom.local">Contact</a>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

function ProductPreview() {
  return (
    <div className="absolute right-[-6rem] top-20 hidden w-[58rem] rotate-[-2deg] rounded-lg border border-white/10 bg-board-panel p-4 shadow-glow lg:block">
      <div className="grid gap-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex gap-2">
            <span className="h-3 w-3 rounded-full bg-board-rose" />
            <span className="h-3 w-3 rounded-full bg-board-amber" />
            <span className="h-3 w-3 rounded-full bg-board-teal" />
          </div>
          <div className="text-xs text-board-muted">BoardroomAI Workspace</div>
        </div>
        <div className="grid gap-4 md:grid-cols-[220px_minmax(0,1fr)]">
          <div className="space-y-2">
            {["Dashboard", "Enterprise", "Decide", "Boardroom", "History"].map((item) => (
              <div key={item} className="rounded-md border border-white/10 bg-white/[0.035] p-3 text-xs text-board-muted">
                {item}
              </div>
            ))}
          </div>
          <div className="grid gap-4">
            <div className="grid gap-3 md:grid-cols-3">
              <PreviewMetric icon={Activity} label="Confidence" value="84%" />
              <PreviewMetric icon={LineChart} label="Risk Trend" value="Low" />
              <PreviewMetric icon={Server} label="Providers" value="Healthy" />
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <PreviewPanel title="Executive Debate" />
              <PreviewPanel title="Evidence Panel" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function HeroMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-3">
      <div className="text-xs uppercase text-board-muted">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

function SectionHeader({
  eyebrow,
  title,
  body
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="max-w-3xl">
      <div className="text-sm font-medium text-board-teal">{eyebrow}</div>
      <h2 className="mt-2 break-words text-3xl font-semibold text-white md:text-4xl">{title}</h2>
      <p className="mt-3 text-base leading-7 text-board-muted">{body}</p>
    </div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  body
}: {
  icon: LucideIcon;
  title: string;
  body: string;
}) {
  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
      <Icon className="h-5 w-5 text-board-teal" />
      <h3 className="mt-4 text-base font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-board-muted">{body}</p>
    </article>
  );
}

function ScreenshotPanel({ title }: { title: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-board-panel p-3">
      <div className="mb-3 text-sm font-semibold text-white">{title}</div>
      <div className="grid gap-2">
        <div className="h-3 rounded bg-white/[0.10]" />
        <div className="h-3 w-3/4 rounded bg-board-teal/40" />
        <div className="mt-2 grid grid-cols-3 gap-2">
          <div className="h-14 rounded border border-white/10 bg-white/[0.04]" />
          <div className="h-14 rounded border border-white/10 bg-white/[0.04]" />
          <div className="h-14 rounded border border-white/10 bg-white/[0.04]" />
        </div>
      </div>
    </div>
  );
}

function ArchitectureStep({
  index,
  title,
  body
}: {
  index: number;
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-board-teal text-sm font-semibold text-board-ink">
        {index}
      </div>
      <h3 className="mt-4 text-sm font-semibold text-white">{title}</h3>
      <p className="mt-2 text-xs leading-5 text-board-muted">{body}</p>
    </div>
  );
}

function InfoPanel({
  icon: Icon,
  title,
  body
}: {
  icon: LucideIcon;
  title: string;
  body: string;
}) {
  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.035] p-5">
      <Icon className="h-5 w-5 text-board-teal" />
      <h2 className="mt-4 text-lg font-semibold text-white">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-board-muted">{body}</p>
    </article>
  );
}

function PreviewMetric({
  icon: Icon,
  label,
  value
}: {
  icon: LucideIcon;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.035] p-3">
      <Icon className="h-4 w-4 text-board-teal" />
      <div className="mt-3 text-xs text-board-muted">{label}</div>
      <div className="text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

function PreviewPanel({ title }: { title: string }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.035] p-3">
      <div className="text-xs font-semibold text-white">{title}</div>
      <div className="mt-3 space-y-2">
        <div className="h-2 rounded bg-white/[0.10]" />
        <div className="h-2 w-5/6 rounded bg-white/[0.07]" />
        <div className="h-2 w-2/3 rounded bg-board-amber/40" />
      </div>
    </div>
  );
}
