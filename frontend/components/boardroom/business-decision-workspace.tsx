"use client";

import {
  AlertTriangle,
  BriefcaseBusiness,
  Calculator,
  Download,
  FileJson,
  FileText,
  LocateFixed,
  MapPin,
  Play,
  RefreshCcw,
  Search,
  ShieldCheck,
  ShoppingCart,
  Store,
  Target,
  TrendingUp
} from "lucide-react";
import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";

import {
  analyzeBusiness,
  businessAnalysisExportUrl,
  fetchBusinessAnalyses,
  fetchBusinessAnalysisDetail,
  fetchBusinessProviderStatus
} from "@/lib/api";
import type {
  BusinessAnalysisPayload,
  BusinessAnalysisResult,
  BusinessAnalysisSummary,
  BusinessDataMode,
  BusinessProviderStatus,
  StartupBriefPayload
} from "@/lib/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type BusinessFormState = {
  workflow_type: BusinessAnalysisPayload["workflow_type"];
  business_idea: string;
  business_category: string;
  country: string;
  state: string;
  city: string;
  locality: string;
  market: string;
  address: string;
  latitude: string;
  longitude: string;
  radius_km: string;
  location_source: BusinessAnalysisPayload["location"]["source"];
  budget: string;
  priorities: string[];
  data_mode: BusinessDataMode;
  shop_size_sqft: string;
  business_experience: string;
  skillsText: string;
  target_customers: string;
  risk_tolerance: "low" | "medium" | "high";
  timeline: string;
  competitorsText: string;
  suppliersText: string;
  candidateLocationsText: string;
  propertiesText: string;
  customerObservationsText: string;
  expected_rent: string;
  security_deposit: string;
  renovation_cost: string;
  equipment_budget: string;
  opening_inventory_budget: string;
  license_budget: string;
  marketing_budget: string;
  monthly_staff_cost: string;
  utilities_monthly: string;
  logistics_monthly: string;
  desired_owner_income: string;
  working_capital_months: string;
  average_transaction_value: string;
  gross_margin_percent: string;
  working_days_per_month: string;
};

const workflowOptions: Array<{
  value: BusinessFormState["workflow_type"];
  label: string;
}> = [
  { value: "existing_idea", label: "I already have an idea" },
  { value: "find_opportunity", label: "Find an opportunity" },
  { value: "compare_ideas", label: "Compare ideas" },
  { value: "existing_business", label: "Analyze existing business" },
  { value: "evaluate_location", label: "Evaluate a shop or location" },
  { value: "improve_business", label: "Improve operating business" },
  { value: "ask_board", label: "Ask the advisory board" }
];

const priorityOptions = [
  "Best location",
  "Competitor analysis",
  "Nearby opportunity areas",
  "Supplier discovery",
  "Procurement planning",
  "Opening inventory",
  "Customer demand",
  "Customer problems",
  "Startup cost",
  "Monthly expenses",
  "Required daily sales",
  "Revenue potential",
  "Profitability",
  "Break-even",
  "Marketing",
  "Licenses and compliance",
  "Risks",
  "Validation plan",
  "Full analysis"
];

const initialBusinessForm: BusinessFormState = {
  workflow_type: "existing_idea",
  business_idea: "Mobile-repair shop",
  business_category: "Local repair service",
  country: "United States",
  state: "",
  city: "",
  locality: "",
  market: "",
  address: "",
  latitude: "",
  longitude: "",
  radius_km: "3",
  location_source: "manual",
  budget: "25000",
  priorities: ["Full analysis", "Competitor analysis", "Supplier discovery", "Required daily sales"],
  data_mode: "demo",
  shop_size_sqft: "",
  business_experience: "",
  skillsText: "repair, customer service",
  target_customers: "People nearby who need quick phone repairs and accessories",
  risk_tolerance: "medium",
  timeline: "6 months",
  competitorsText: "",
  suppliersText: "",
  candidateLocationsText: "",
  propertiesText: "",
  customerObservationsText: "",
  expected_rent: "",
  security_deposit: "",
  renovation_cost: "",
  equipment_budget: "",
  opening_inventory_budget: "",
  license_budget: "",
  marketing_budget: "",
  monthly_staff_cost: "",
  utilities_monthly: "",
  logistics_monthly: "",
  desired_owner_income: "",
  working_capital_months: "3",
  average_transaction_value: "",
  gross_margin_percent: "",
  working_days_per_month: "26"
};

export function BusinessDecisionWorkspace({
  onStartBoardMeeting
}: {
  onStartBoardMeeting: (payload: StartupBriefPayload) => void;
}) {
  const [form, setForm] = useState<BusinessFormState>(initialBusinessForm);
  const [result, setResult] = useState<BusinessAnalysisResult | null>(null);
  const [history, setHistory] = useState<BusinessAnalysisSummary[]>([]);
  const [providerStatus, setProviderStatus] = useState<BusinessProviderStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locationMessage, setLocationMessage] = useState<string | null>(null);

  const payload = useMemo(() => businessFormToPayload(form), [form]);

  async function refreshHistory() {
    setLoadingHistory(true);
    try {
      setHistory(await fetchBusinessAnalyses());
      setError(null);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Business analysis history failed to load"
      );
    } finally {
      setLoadingHistory(false);
    }
  }

  useEffect(() => {
    void refreshHistory();
    void fetchBusinessProviderStatus()
      .then(setProviderStatus)
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : "Provider status failed to load");
      });
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      const analysis = await analyzeBusiness(payload);
      setResult(analysis);
      await refreshHistory();
      setError(null);
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : "Business analysis failed");
    } finally {
      setBusy(false);
    }
  }

  async function openHistory(analysisId: string) {
    setBusy(true);
    try {
      setResult(await fetchBusinessAnalysisDetail(analysisId));
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Business decision brief failed");
    } finally {
      setBusy(false);
    }
  }

  function useCurrentLocation() {
    setLocationMessage(
      "BoardroomAI uses your approximate location to identify nearby competitors, suppliers, demand signals, and possible business areas. You can enter a location manually instead."
    );

    if (!("geolocation" in navigator)) {
      setLocationMessage("Location is unsupported in this browser. Search manually or select a map location.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setForm((current) => ({
          ...current,
          latitude: String(position.coords.latitude),
          longitude: String(position.coords.longitude),
          location_source: "browser_permission"
        }));
        setLocationMessage("Approximate location selected. It will be used only for this business analysis.");
      },
      (positionError) => {
        setLocationMessage(
          positionError.code === positionError.PERMISSION_DENIED
            ? "Location permission was denied. Search manually or select a map location."
            : "Location could not be read. Search manually or select a map location."
        );
      },
      {
        enableHighAccuracy: false,
        maximumAge: 60_000,
        timeout: 10_000
      }
    );
  }

  function update<K extends keyof BusinessFormState>(key: K, value: BusinessFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(420px,1.05fr)]">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <DecisionPanel
          icon={BriefcaseBusiness}
          title="What would you like help with?"
          subtitle="Simple Mode is the default. You can start with only an idea, location, and budget."
        >
          <div className="grid gap-2 sm:grid-cols-2">
            {workflowOptions.map((option) => (
              <ChoiceButton
                key={option.value}
                active={form.workflow_type === option.value}
                onClick={() => update("workflow_type", option.value)}
              >
                {option.label}
              </ChoiceButton>
            ))}
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <Field label="What business do you want to start?">
              <Input
                value={form.business_idea}
                onChange={(event) => update("business_idea", event.target.value)}
                placeholder="Mobile-repair shop"
              />
            </Field>
            <Field label="Business category">
              <Input
                value={form.business_category}
                onChange={(event) => update("business_category", event.target.value)}
                placeholder="Cafe, repair shop, B2B SaaS"
              />
            </Field>
          </div>
        </DecisionPanel>

        <DecisionPanel
          icon={MapPin}
          title="Where do you want to start it?"
          subtitle="Location permission is optional and only requested when you choose it."
        >
          <div className="grid gap-2 md:grid-cols-3">
            <Button type="button" variant="quiet" onClick={useCurrentLocation}>
              <LocateFixed className="h-4 w-4" />
              Use current location
            </Button>
            <Button
              type="button"
              variant={form.location_source === "search" ? "primary" : "quiet"}
              onClick={() => update("location_source", "search")}
            >
              <Search className="h-4 w-4" />
              Search manually
            </Button>
            <Button
              type="button"
              variant={form.location_source === "map_pin" ? "primary" : "quiet"}
              onClick={() => update("location_source", "map_pin")}
            >
              <MapPin className="h-4 w-4" />
              Select on map
            </Button>
          </div>

          {locationMessage ? (
            <div className="mt-3 rounded-md border border-board-teal/25 bg-board-teal/10 p-3 text-sm leading-6 text-board-mist">
              {locationMessage}
            </div>
          ) : null}

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <Field label="Country">
              <Input value={form.country} onChange={(event) => update("country", event.target.value)} />
            </Field>
            <Field label="State or province">
              <Input value={form.state} onChange={(event) => update("state", event.target.value)} />
            </Field>
            <Field label="City">
              <Input value={form.city} onChange={(event) => update("city", event.target.value)} />
            </Field>
            <Field label="Locality, neighbourhood, or market">
              <Input value={form.locality} onChange={(event) => update("locality", event.target.value)} />
            </Field>
            <Field label="Address">
              <Input value={form.address} onChange={(event) => update("address", event.target.value)} />
            </Field>
            <Field label="Search radius (km)">
              <Input
                value={form.radius_km}
                type="number"
                min="0.1"
                step="0.1"
                onChange={(event) => update("radius_km", event.target.value)}
              />
            </Field>
          </div>

          {form.location_source === "map_pin" || form.location_source === "browser_permission" ? (
            <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_220px]">
              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Latitude">
                  <Input
                    value={form.latitude}
                    type="number"
                    step="0.000001"
                    onChange={(event) => update("latitude", event.target.value)}
                  />
                </Field>
                <Field label="Longitude">
                  <Input
                    value={form.longitude}
                    type="number"
                    step="0.000001"
                    onChange={(event) => update("longitude", event.target.value)}
                  />
                </Field>
              </div>
              <MapSelectionPreview configured={providerStatus?.live_maps_configured === true} />
            </div>
          ) : null}
        </DecisionPanel>

        <DecisionPanel
          icon={Target}
          title="What help do you need?"
          subtitle="Choose priorities. Optional fields can stay blank."
        >
          <div className="flex flex-wrap gap-2">
            {priorityOptions.map((priority) => (
              <ChoiceButton
                key={priority}
                active={form.priorities.includes(priority)}
                onClick={() =>
                  update(
                    "priorities",
                    form.priorities.includes(priority)
                      ? form.priorities.filter((item) => item !== priority)
                      : [...form.priorities, priority]
                  )
                }
              >
                {priority}
              </ChoiceButton>
            ))}
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <Field label="Approximate budget">
              <Input
                value={form.budget}
                type="number"
                min="0"
                onChange={(event) => update("budget", event.target.value)}
              />
            </Field>
            <Field label="Timeline">
              <Input
                value={form.timeline}
                onChange={(event) => update("timeline", event.target.value)}
                placeholder="6 months"
              />
            </Field>
            <Field label="Shop size">
              <Input
                value={form.shop_size_sqft}
                type="number"
                min="0"
                onChange={(event) => update("shop_size_sqft", event.target.value)}
              />
            </Field>
            <Field label="Risk tolerance">
              <select
                value={form.risk_tolerance}
                onChange={(event) =>
                  update("risk_tolerance", event.target.value as BusinessFormState["risk_tolerance"])
                }
                className="h-10 w-full rounded-md border border-white/10 bg-white/[0.04] px-3 text-sm text-white outline-none"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </Field>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <Field label="Skills or interests">
              <Input
                value={form.skillsText}
                onChange={(event) => update("skillsText", event.target.value)}
                placeholder="repair, sales, cooking"
              />
            </Field>
            <Field label="Target customers">
              <Input
                value={form.target_customers}
                onChange={(event) => update("target_customers", event.target.value)}
                placeholder="Students, office workers, families"
              />
            </Field>
          </div>
        </DecisionPanel>

        <DecisionPanel
          icon={ShieldCheck}
          title="Evidence mode"
          subtitle="Demo mode is clearly labeled. Manual entries are treated as user-provided evidence."
        >
          <div className="grid gap-2 sm:grid-cols-3">
            {(["demo", "manual", "live"] as BusinessDataMode[]).map((mode) => (
              <ChoiceButton
                key={mode}
                active={form.data_mode === mode}
                onClick={() => update("data_mode", mode)}
              >
                {titleCase(mode)}
              </ChoiceButton>
            ))}
          </div>
          {providerStatus ? (
            <p className="mt-3 text-sm leading-6 text-board-muted">
              Provider: {providerStatus.maps_provider}. Live maps configured:{" "}
              {providerStatus.live_maps_configured ? "yes" : "no"}. Live places configured:{" "}
              {providerStatus.live_places_configured ? "yes" : "no"}.
            </p>
          ) : null}
          {form.data_mode === "demo" ? (
            <div className="mt-3 rounded-md border border-board-amber/30 bg-board-amber/10 p-3 text-sm text-board-amber">
              Demo data - not live local evidence.
            </div>
          ) : null}
        </DecisionPanel>

        <DecisionPanel
          icon={Store}
          title="Manual competitors, suppliers, areas, and properties"
          subtitle="One item per line. Use pipes to separate fields."
        >
          <div className="grid gap-3">
            <Field label="Competitors: name | category | distance km | notes">
              <Textarea
                value={form.competitorsText}
                onChange={(event) => update("competitorsText", event.target.value)}
                rows={4}
                placeholder="FastFix Phones | mobile repair | 1.2 | long waits on weekends"
              />
            </Field>
            <Field label="Suppliers: name | category | distance km | products | notes">
              <Textarea
                value={form.suppliersText}
                onChange={(event) => update("suppliersText", event.target.value)}
                rows={4}
                placeholder="Downtown Parts Wholesale | screens | 8 | screens, batteries | call for MOQ"
              />
            </Field>
            <Field label="Candidate areas: name | expected rent | notes">
              <Textarea
                value={form.candidateLocationsText}
                onChange={(event) => update("candidateLocationsText", event.target.value)}
                rows={3}
                placeholder="Market Street | 1800 | more offices nearby"
              />
            </Field>
            <Field label="Properties: name | rent | deposit | size sqft | notes">
              <Textarea
                value={form.propertiesText}
                onChange={(event) => update("propertiesText", event.target.value)}
                rows={3}
                placeholder="Shop A | 2000 | 4000 | 350 | good frontage, parking unknown"
              />
            </Field>
            <Field label="Customer observations">
              <Textarea
                value={form.customerObservationsText}
                onChange={(event) => update("customerObservationsText", event.target.value)}
                rows={3}
                placeholder="Customers complain about unclear prices; nearby stores have long wait times"
              />
            </Field>
          </div>
        </DecisionPanel>

        <DecisionPanel
          icon={Calculator}
          title="Editable financial assumptions"
          subtitle="Blank values become unknown or clearly labeled benchmarks."
        >
          <div className="grid gap-3 md:grid-cols-3">
            <NumberField label="Rent" value={form.expected_rent} onChange={(value) => update("expected_rent", value)} />
            <NumberField label="Deposit" value={form.security_deposit} onChange={(value) => update("security_deposit", value)} />
            <NumberField label="Renovation" value={form.renovation_cost} onChange={(value) => update("renovation_cost", value)} />
            <NumberField label="Equipment" value={form.equipment_budget} onChange={(value) => update("equipment_budget", value)} />
            <NumberField label="Opening inventory" value={form.opening_inventory_budget} onChange={(value) => update("opening_inventory_budget", value)} />
            <NumberField label="Licenses" value={form.license_budget} onChange={(value) => update("license_budget", value)} />
            <NumberField label="Marketing" value={form.marketing_budget} onChange={(value) => update("marketing_budget", value)} />
            <NumberField label="Monthly staff" value={form.monthly_staff_cost} onChange={(value) => update("monthly_staff_cost", value)} />
            <NumberField label="Utilities monthly" value={form.utilities_monthly} onChange={(value) => update("utilities_monthly", value)} />
            <NumberField label="Owner income" value={form.desired_owner_income} onChange={(value) => update("desired_owner_income", value)} />
            <NumberField label="Average transaction" value={form.average_transaction_value} onChange={(value) => update("average_transaction_value", value)} />
            <NumberField label="Gross margin %" value={form.gross_margin_percent} onChange={(value) => update("gross_margin_percent", value)} />
          </div>
        </DecisionPanel>

        {error ? (
          <div className="rounded-md border border-board-rose/30 bg-board-rose/10 p-3 text-sm text-board-rose">
            {error}
          </div>
        ) : null}

        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={busy}>
            <TrendingUp className="h-4 w-4" />
            {busy ? "Analyzing..." : "Prepare decision brief"}
          </Button>
          <Button type="button" variant="quiet" onClick={() => setForm(initialBusinessForm)}>
            <RefreshCcw className="h-4 w-4" />
            Reset intake
          </Button>
        </div>
      </form>

      <div className="space-y-4">
        {result ? (
          <DecisionBrief result={result} onStartBoardMeeting={onStartBoardMeeting} />
        ) : (
          <EmptyDecisionState />
        )}

        <DecisionPanel
          icon={BriefcaseBusiness}
          title="Recent business analyses"
          subtitle={loadingHistory ? "Loading..." : `${history.length} saved decision briefs`}
        >
          <div className="space-y-2">
            {history.length ? (
              history.slice(0, 8).map((analysis) => (
                <button
                  key={analysis.analysis_id}
                  type="button"
                  onClick={() => void openHistory(analysis.analysis_id)}
                  className="w-full rounded-md border border-white/10 bg-white/[0.035] p-3 text-left transition hover:border-board-teal/40"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="break-words text-sm font-semibold text-white">
                        {analysis.business_idea}
                      </div>
                      <div className="mt-1 break-words text-xs text-board-muted">
                        {analysis.location_label}
                      </div>
                    </div>
                    <ScoreBadge score={analysis.opportunity_score} />
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <SmallBadge tone="teal">{analysis.recommendation_label}</SmallBadge>
                    <SmallBadge>{analysis.evidence_confidence} evidence</SmallBadge>
                    {analysis.data_mode === "demo" ? <SmallBadge tone="amber">Demo</SmallBadge> : null}
                  </div>
                </button>
              ))
            ) : (
              <p className="text-sm text-board-muted">No business decision briefs yet.</p>
            )}
          </div>
        </DecisionPanel>
      </div>
    </div>
  );
}

function DecisionBrief({
  result,
  onStartBoardMeeting
}: {
  result: BusinessAnalysisResult;
  onStartBoardMeeting: (payload: StartupBriefPayload) => void;
}) {
  const setupCost = asRecord(asRecord(result.financials.setup_cost).estimated_total_range);
  const dailyTargets = asRecord(asRecord(result.daily_sales.daily_targets));
  const monthlyTargets = asRecord(asRecord(result.daily_sales.monthly_targets));
  const inventory = Array.isArray(result.procurement_plan.opening_inventory)
    ? result.procurement_plan.opening_inventory
    : [];

  return (
    <div className="space-y-4">
      <DecisionPanel
        icon={TrendingUp}
        title="Final decision brief"
        subtitle={result.demo_notice ?? result.provider_label}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="text-sm text-board-muted">Recommendation</div>
            <h2 className="mt-1 break-words text-2xl font-semibold text-white">
              {result.recommendation.label}
            </h2>
            <p className="mt-2 break-words text-sm leading-6 text-board-mist">
              {result.recommendation.plain_language}
            </p>
          </div>
          <ScoreDial score={result.opportunity_score.score} />
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Evidence" value={result.evidence_confidence} />
          <Metric label="Setup low" value={moneyish(setupCost.low)} />
          <Metric label="Setup high" value={moneyish(setupCost.high)} />
          <Metric label="Daily sales" value={moneyish(dailyTargets.required_daily_revenue)} />
        </div>

        <div className="mt-4 rounded-md border border-white/10 bg-white/[0.035] p-3 text-sm leading-6 text-board-muted">
          {result.disclaimer}
        </div>

        {result.warnings.length ? (
          <div className="mt-3 space-y-2">
            {result.warnings.map((warning) => (
              <div
                key={warning}
                className="flex gap-2 rounded-md border border-board-amber/30 bg-board-amber/10 p-3 text-sm text-board-amber"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{warning}</span>
              </div>
            ))}
          </div>
        ) : null}
      </DecisionPanel>

      <DecisionPanel icon={Target} title="Reasons, risks, and missing evidence" subtitle="What supports the recommendation">
        <ThreeColumnList
          firstTitle="Top reasons"
          firstItems={result.recommendation.top_reasons}
          secondTitle="Main risks"
          secondItems={result.recommendation.main_risks}
          thirdTitle="Missing information"
          thirdItems={result.missing_information}
        />
      </DecisionPanel>

      <DecisionPanel icon={Store} title="Competitors and suppliers" subtitle="Manual or configured-provider evidence only">
        <div className="grid gap-3 md:grid-cols-2">
          <ResultList
            title="Competitors"
            empty="No verified competitors were found in the current data."
            items={result.competitors}
            primaryKey="name"
            secondaryKey="classification"
          />
          <ResultList
            title="Suppliers"
            empty="No verified suppliers were found in the current data."
            items={result.suppliers}
            primaryKey="name"
            secondaryKey="category"
          />
        </div>
      </DecisionPanel>

      <DecisionPanel icon={Calculator} title="Daily sales and break-even" subtitle="Editable assumptions, transparent origin labels">
        <div className="grid gap-3 sm:grid-cols-3">
          <Metric label="Monthly revenue" value={moneyish(monthlyTargets.required_monthly_revenue)} />
          <Metric label="Daily revenue" value={moneyish(dailyTargets.required_daily_revenue)} />
          <Metric label="Daily transactions" value={String(dailyTargets.required_daily_transactions ?? "Unknown")} />
        </div>
        <p className="mt-4 text-sm leading-6 text-board-mist">
          {String(result.daily_sales.plain_language ?? "")}
        </p>
      </DecisionPanel>

      <DecisionPanel icon={ShoppingCart} title="Opening procurement" subtitle="Editable checklist with benchmark assumptions">
        <div className="grid gap-2">
          {inventory.slice(0, 6).map((item, index) => {
            const record = asRecord(item);
            const cost = asRecord(record.estimated_cost_range);
            return (
              <div
                key={`${String(record.item)}-${index}`}
                className="rounded-md border border-white/10 bg-white/[0.035] p-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="break-words text-sm font-semibold text-white">
                    {String(record.item)}
                  </div>
                  <SmallBadge>{String(record.category)}</SmallBadge>
                </div>
                <div className="mt-2 text-xs text-board-muted">
                  Estimated range: {moneyish(cost.low)} - {moneyish(cost.high)} ({String(cost.origin)})
                </div>
              </div>
            );
          })}
        </div>
      </DecisionPanel>

      <DecisionPanel icon={ShieldCheck} title="Validation plan" subtitle="Measurable checks before investing">
        <div className="space-y-2">
          {result.validation_plan.slice(0, 5).map((task, index) => (
            <div key={index} className="rounded-md border border-white/10 bg-white/[0.035] p-3">
              <div className="break-words text-sm font-semibold text-white">
                {String(task.task)}
              </div>
              <div className="mt-2 text-xs leading-5 text-board-muted">
                Expected evidence: {String(task.expected_evidence ?? "Record the result.")}
              </div>
            </div>
          ))}
        </div>
      </DecisionPanel>

      <div className="flex flex-wrap gap-2">
        <Button type="button" onClick={() => onStartBoardMeeting(result.board_brief)}>
          <Play className="h-4 w-4" />
          Start board meeting
        </Button>
        <Button type="button" variant="quiet" asChild>
          <a href={businessAnalysisExportUrl(result.analysis_id, "pdf")} target="_blank" rel="noreferrer">
            <Download className="h-4 w-4" />
            PDF
          </a>
        </Button>
        <Button type="button" variant="quiet" asChild>
          <a href={businessAnalysisExportUrl(result.analysis_id, "markdown")} target="_blank" rel="noreferrer">
            <FileText className="h-4 w-4" />
            Markdown
          </a>
        </Button>
        <Button type="button" variant="quiet" asChild>
          <a href={businessAnalysisExportUrl(result.analysis_id, "json")} target="_blank" rel="noreferrer">
            <FileJson className="h-4 w-4" />
            JSON
          </a>
        </Button>
      </div>
    </div>
  );
}

function businessFormToPayload(form: BusinessFormState): BusinessAnalysisPayload {
  return {
    workflow_type: form.workflow_type,
    business_idea: cleanOptional(form.business_idea),
    business_category: cleanOptional(form.business_category),
    location: {
      country: cleanOptional(form.country),
      state: cleanOptional(form.state),
      city: cleanOptional(form.city),
      locality: cleanOptional(form.locality),
      market: cleanOptional(form.market),
      address: cleanOptional(form.address),
      latitude: numberOrUndefined(form.latitude),
      longitude: numberOrUndefined(form.longitude),
      radius_km: numberOrUndefined(form.radius_km) ?? 3,
      source: form.location_source
    },
    budget: numberOrUndefined(form.budget),
    priorities: form.priorities,
    data_mode: form.data_mode,
    shop_size_sqft: numberOrUndefined(form.shop_size_sqft),
    business_experience: cleanOptional(form.business_experience),
    skills: splitLoose(form.skillsText),
    target_customers: cleanOptional(form.target_customers),
    risk_tolerance: form.risk_tolerance,
    timeline: cleanOptional(form.timeline),
    manual_competitors: parseCompetitors(form.competitorsText),
    manual_suppliers: parseSuppliers(form.suppliersText),
    candidate_locations: parseCandidateLocations(form.candidateLocationsText),
    properties: parseProperties(form.propertiesText),
    customer_observations: splitLines(form.customerObservationsText),
    customer_interviews: [],
    financial_assumptions: {
      expected_rent: numberOrUndefined(form.expected_rent),
      security_deposit: numberOrUndefined(form.security_deposit),
      renovation_cost: numberOrUndefined(form.renovation_cost),
      equipment_budget: numberOrUndefined(form.equipment_budget),
      opening_inventory_budget: numberOrUndefined(form.opening_inventory_budget),
      license_budget: numberOrUndefined(form.license_budget),
      marketing_budget: numberOrUndefined(form.marketing_budget),
      monthly_staff_cost: numberOrUndefined(form.monthly_staff_cost),
      utilities_monthly: numberOrUndefined(form.utilities_monthly),
      logistics_monthly: numberOrUndefined(form.logistics_monthly),
      desired_owner_income: numberOrUndefined(form.desired_owner_income),
      working_capital_months: numberOrUndefined(form.working_capital_months) ?? 3,
      average_transaction_value: numberOrUndefined(form.average_transaction_value),
      gross_margin_percent: numberOrUndefined(form.gross_margin_percent),
      working_days_per_month: numberOrUndefined(form.working_days_per_month) ?? 26
    },
    optional_inputs: {}
  };
}

function parseCompetitors(text: string): BusinessAnalysisPayload["manual_competitors"] {
  return splitLines(text).map((line) => {
    const [name, category, distance, notes] = splitPipe(line);
    return {
      name,
      category: cleanOptional(category),
      distance_km: numberOrUndefined(distance),
      notes: cleanOptional(notes)
    };
  });
}

function parseSuppliers(text: string): BusinessAnalysisPayload["manual_suppliers"] {
  return splitLines(text).map((line) => {
    const [name, category, distance, products, notes] = splitPipe(line);
    return {
      name,
      category: cleanOptional(category),
      distance_km: numberOrUndefined(distance),
      product_categories: splitLoose(products ?? ""),
      notes: cleanOptional(notes)
    };
  });
}

function parseCandidateLocations(text: string): BusinessAnalysisPayload["candidate_locations"] {
  return splitLines(text).map((line) => {
    const [name, expectedRent, notes] = splitPipe(line);
    return {
      name,
      expected_rent: numberOrUndefined(expectedRent),
      notes: cleanOptional(notes)
    };
  });
}

function parseProperties(text: string): BusinessAnalysisPayload["properties"] {
  return splitLines(text).map((line) => {
    const [name, rent, deposit, size, observations] = splitPipe(line);
    return {
      name,
      rent: numberOrUndefined(rent),
      deposit: numberOrUndefined(deposit),
      shop_size_sqft: numberOrUndefined(size),
      observations: cleanOptional(observations)
    };
  });
}

function splitPipe(line: string) {
  return line.split("|").map((part) => part.trim());
}

function splitLoose(text: string) {
  return text
    .split(/[,;\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitLines(text: string) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function cleanOptional(value?: string) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

function numberOrUndefined(value?: string) {
  if (!value?.trim()) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function DecisionPanel({
  icon: Icon,
  title,
  subtitle,
  children
}: {
  icon: typeof BriefcaseBusiness;
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <section className="glass-panel min-w-0 rounded-lg p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
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

function ChoiceButton({
  active,
  children,
  onClick
}: {
  active: boolean;
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-md border px-3 py-2 text-left text-sm transition",
        active
          ? "border-board-teal/50 bg-board-teal/15 text-board-teal"
          : "border-white/10 bg-white/[0.035] text-board-mist hover:border-board-teal/30"
      )}
    >
      {children}
    </button>
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

function NumberField({
  label,
  value,
  onChange
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <Field label={label}>
      <Input
        value={value}
        type="number"
        min="0"
        step="0.01"
        onChange={(event) => onChange(event.target.value)}
      />
    </Field>
  );
}

function MapSelectionPreview({ configured }: { configured: boolean }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.035] p-3">
      <div className="relative h-28 overflow-hidden rounded-md border border-white/10 bg-[linear-gradient(90deg,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(0deg,rgba(255,255,255,0.06)_1px,transparent_1px)] bg-[size:24px_24px]">
        <div className="absolute left-1/2 top-1/2 flex h-8 w-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-board-teal/50 bg-board-teal/20 text-board-teal">
          <MapPin className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-2 text-xs leading-5 text-board-muted">
        {configured
          ? "Map provider configured. Markers can represent selected location, competitors, suppliers, candidate areas, and properties."
          : "Map provider not configured. Enter coordinates manually; no provider secrets are exposed in frontend code."}
      </div>
    </div>
  );
}

function EmptyDecisionState() {
  return (
    <DecisionPanel
      icon={TrendingUp}
      title="Decision brief"
      subtitle="Your recommendation, evidence, costs, and next actions will appear here."
    >
      <div className="grid min-h-64 place-items-center rounded-md border border-dashed border-white/10 bg-white/[0.02] p-6 text-center">
        <div>
          <Store className="mx-auto h-6 w-6 text-board-muted" />
          <p className="mt-3 max-w-md text-sm leading-6 text-board-muted">
            Start with a simple local business, a technology startup, a candidate shop, or an operating business. The board can debate it after the evidence brief is prepared.
          </p>
        </div>
      </div>
    </DecisionPanel>
  );
}

function ScoreDial({ score }: { score: number }) {
  return (
    <div
      className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full"
      style={{
        background: `conic-gradient(#38d6c6 ${score * 3.6}deg, rgba(255,255,255,0.08) 0deg)`
      }}
    >
      <div className="flex h-16 w-16 flex-col items-center justify-center rounded-full bg-board-panel">
        <span className="text-xs text-board-muted">Score</span>
        <span className="text-lg font-semibold text-white">{score}</span>
      </div>
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  return (
    <span className="shrink-0 rounded-md border border-board-teal/30 bg-board-teal/10 px-2 py-1 text-sm font-semibold text-board-teal">
      {score}/100
    </span>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.035] p-3">
      <div className="text-xs uppercase text-board-muted">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

function ThreeColumnList({
  firstTitle,
  firstItems,
  secondTitle,
  secondItems,
  thirdTitle,
  thirdItems
}: {
  firstTitle: string;
  firstItems: string[];
  secondTitle: string;
  secondItems: string[];
  thirdTitle: string;
  thirdItems: string[];
}) {
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      <TextList title={firstTitle} items={firstItems} />
      <TextList title={secondTitle} items={secondItems} />
      <TextList title={thirdTitle} items={thirdItems} />
    </div>
  );
}

function TextList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.035] p-3">
      <div className="text-sm font-semibold text-white">{title}</div>
      <div className="mt-2 space-y-2">
        {items.length ? (
          items.map((item) => (
            <div key={item} className="text-sm leading-5 text-board-mist">
              {item}
            </div>
          ))
        ) : (
          <div className="text-sm text-board-muted">None recorded yet.</div>
        )}
      </div>
    </div>
  );
}

function ResultList({
  title,
  empty,
  items,
  primaryKey,
  secondaryKey
}: {
  title: string;
  empty: string;
  items: Array<Record<string, unknown>>;
  primaryKey: string;
  secondaryKey: string;
}) {
  return (
    <div>
      <div className="mb-2 text-sm font-semibold text-white">{title}</div>
      <div className="space-y-2">
        {items.length ? (
          items.slice(0, 6).map((item, index) => (
            <div key={`${String(item[primaryKey])}-${index}`} className="rounded-md border border-white/10 bg-white/[0.035] p-3">
              <div className="break-words text-sm font-semibold text-white">
                {String(item[primaryKey] ?? "Unnamed")}
              </div>
              <div className="mt-1 break-words text-xs text-board-muted">
                {String(item[secondaryKey] ?? "Not specified")}
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-md border border-dashed border-white/10 bg-white/[0.02] p-3 text-sm text-board-muted">
            {empty}
          </div>
        )}
      </div>
    </div>
  );
}

function SmallBadge({
  children,
  tone = "muted"
}: {
  children: ReactNode;
  tone?: "muted" | "teal" | "amber";
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-sm border px-2 py-1 text-xs",
        tone === "muted" && "border-white/10 bg-white/[0.04] text-board-muted",
        tone === "teal" && "border-board-teal/30 bg-board-teal/10 text-board-teal",
        tone === "amber" && "border-board-amber/30 bg-board-amber/10 text-board-amber"
      )}
    >
      {children}
    </span>
  );
}

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function moneyish(value: unknown) {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) {
    return "Unknown";
  }
  return new Intl.NumberFormat(undefined, {
    notation: "compact",
    maximumFractionDigits: 1
  }).format(numeric);
}

function titleCase(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
