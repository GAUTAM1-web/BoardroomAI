from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

DataMode = Literal["demo", "manual", "live"]
WorkflowType = Literal[
    "existing_idea",
    "find_opportunity",
    "compare_ideas",
    "existing_business",
    "evaluate_location",
    "improve_business",
    "ask_board",
]


class LocationInput(BaseModel):
    country: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    locality: str | None = Field(default=None, max_length=160)
    market: str | None = Field(default=None, max_length=160)
    address: str | None = Field(default=None, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_km: float = Field(default=3.0, gt=0, le=100)
    map_zoom: int | None = Field(default=None, ge=1, le=22)
    source: Literal["manual", "browser_permission", "map_pin", "search"] = "manual"

    @model_validator(mode="after")
    def require_some_location(self) -> LocationInput:
        if not any(
            [
                self.country,
                self.state,
                self.city,
                self.locality,
                self.market,
                self.address,
                self.latitude is not None and self.longitude is not None,
            ]
        ):
            raise ValueError(
                "Enter a location manually, select a map pin, or use current location."
            )
        return self


class ManualCompetitorInput(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    category: str | None = Field(default=None, max_length=160)
    location_label: str | None = Field(default=None, max_length=220)
    distance_km: float | None = Field(default=None, ge=0, le=500)
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    website: str | None = Field(default=None, max_length=300)
    services: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=700)


class ManualSupplierInput(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    category: str | None = Field(default=None, max_length=160)
    location_label: str | None = Field(default=None, max_length=220)
    distance_km: float | None = Field(default=None, ge=0, le=1000)
    product_categories: list[str] = Field(default_factory=list, max_length=30)
    delivery_available: bool | None = None
    minimum_order_quantity: str | None = Field(default=None, max_length=160)
    public_pricing: str | None = Field(default=None, max_length=240)
    quotation_amount: float | None = Field(default=None, ge=0)
    contact_status: str | None = Field(default=None, max_length=120)
    is_preferred: bool = False
    notes: str | None = Field(default=None, max_length=700)


class CandidateLocationInput(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    country: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    locality: str | None = Field(default=None, max_length=160)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    expected_rent: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=700)


class PropertyInput(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    address: str | None = Field(default=None, max_length=300)
    rent: float | None = Field(default=None, ge=0)
    deposit: float | None = Field(default=None, ge=0)
    purchase_price: float | None = Field(default=None, ge=0)
    shop_size_sqft: float | None = Field(default=None, ge=0)
    frontage_ft: float | None = Field(default=None, ge=0)
    floor: str | None = Field(default=None, max_length=80)
    parking: str | None = Field(default=None, max_length=160)
    visibility: str | None = Field(default=None, max_length=160)
    lease_duration_months: int | None = Field(default=None, ge=1, le=360)
    rent_increase_percent: float | None = Field(default=None, ge=0, le=100)
    renovation_required: str | None = Field(default=None, max_length=240)
    observations: str | None = Field(default=None, max_length=1000)


class FinancialAssumptionsInput(BaseModel):
    expected_rent: float | None = Field(default=None, ge=0)
    security_deposit: float | None = Field(default=None, ge=0)
    renovation_cost: float | None = Field(default=None, ge=0)
    equipment_budget: float | None = Field(default=None, ge=0)
    opening_inventory_budget: float | None = Field(default=None, ge=0)
    license_budget: float | None = Field(default=None, ge=0)
    marketing_budget: float | None = Field(default=None, ge=0)
    monthly_staff_cost: float | None = Field(default=None, ge=0)
    utilities_monthly: float | None = Field(default=None, ge=0)
    logistics_monthly: float | None = Field(default=None, ge=0)
    desired_owner_income: float | None = Field(default=None, ge=0)
    working_capital_months: int = Field(default=3, ge=1, le=12)
    average_transaction_value: float | None = Field(default=None, gt=0)
    gross_margin_percent: float | None = Field(default=None, gt=0, le=100)
    working_days_per_month: int = Field(default=26, ge=1, le=31)


class CustomerInterviewInput(BaseModel):
    customer_segment: str = Field(min_length=1, max_length=180)
    need: str = Field(min_length=1, max_length=700)
    willingness_to_pay: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=1000)


class BusinessAnalysisRequest(BaseModel):
    workflow_type: WorkflowType = "existing_idea"
    business_idea: str | None = Field(default=None, max_length=500)
    business_category: str | None = Field(default=None, max_length=160)
    location: LocationInput
    budget: float | None = Field(default=None, gt=0)
    priorities: list[str] = Field(default_factory=lambda: ["full_analysis"], max_length=30)
    data_mode: DataMode = "demo"
    shop_size_sqft: float | None = Field(default=None, ge=0)
    business_experience: str | None = Field(default=None, max_length=500)
    skills: list[str] = Field(default_factory=list, max_length=30)
    target_customers: str | None = Field(default=None, max_length=500)
    risk_tolerance: Literal["low", "medium", "high"] = "medium"
    timeline: str | None = Field(default=None, max_length=160)
    manual_competitors: list[ManualCompetitorInput] = Field(default_factory=list, max_length=80)
    manual_suppliers: list[ManualSupplierInput] = Field(default_factory=list, max_length=80)
    candidate_locations: list[CandidateLocationInput] = Field(default_factory=list, max_length=12)
    properties: list[PropertyInput] = Field(default_factory=list, max_length=12)
    customer_observations: list[str] = Field(default_factory=list, max_length=50)
    customer_interviews: list[CustomerInterviewInput] = Field(default_factory=list, max_length=50)
    financial_assumptions: FinancialAssumptionsInput = Field(
        default_factory=FinancialAssumptionsInput
    )
    optional_inputs: dict[str, Any] = Field(default_factory=dict)

    @field_validator("priorities", "skills", "customer_observations")
    @classmethod
    def clean_string_lists(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            text = item.strip()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned

    @model_validator(mode="after")
    def require_idea_when_needed(self) -> BusinessAnalysisRequest:
        if self.workflow_type != "find_opportunity" and not (self.business_idea or "").strip():
            raise ValueError("Enter the business idea, such as 'mobile-repair shop'.")
        return self


class EvidenceRecordResponse(BaseModel):
    id: str
    claim: str
    source_name: str
    source_url: str | None = None
    source_type: str
    source_category: str | None = None
    provider: str | None = None
    retrieval_time: str
    location: dict[str, Any] | None = None
    value: Any = None
    confidence: str
    verification_status: str
    freshness: str
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)


class BusinessAnalysisSummaryResponse(BaseModel):
    analysis_id: str
    business_idea: str
    business_category: str
    location_label: str
    recommendation_label: str
    opportunity_score: int
    evidence_confidence: str
    data_mode: str
    created_at: str | None = None


class BusinessAnalysisListResponse(BaseModel):
    analyses: list[BusinessAnalysisSummaryResponse]


class BusinessAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    data_mode: str
    provider_label: str
    generated_at: str
    demo_notice: str | None = None
    disclaimer: str
    intake: dict[str, Any]
    recommendation: dict[str, Any]
    opportunity_score: dict[str, Any]
    evidence_confidence: str
    evidence_panel: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceRecordResponse]
    competitors: list[dict[str, Any]]
    suppliers: list[dict[str, Any]]
    candidate_areas: list[dict[str, Any]]
    properties: list[dict[str, Any]]
    customer_segments: list[dict[str, Any]]
    procurement_plan: dict[str, Any]
    financials: dict[str, Any]
    daily_sales: dict[str, Any]
    validation_plan: list[dict[str, Any]]
    performance_tracking: dict[str, Any]
    live_intelligence: dict[str, Any] = Field(default_factory=dict)
    missing_information: list[str]
    warnings: list[str]
    board_brief: dict[str, Any]
    report: dict[str, Any]


class BusinessProviderStatusResponse(BaseModel):
    default_mode: str
    maps_provider: str
    live_maps_configured: bool
    live_places_configured: bool
    providers: list[dict[str, Any]] = Field(default_factory=list)
    cache: dict[str, Any] = Field(default_factory=dict)
    last_updated: str | None = None
    modes: list[dict[str, Any]]


class BusinessPerformanceEntryRequest(BaseModel):
    period_label: str = Field(min_length=1, max_length=120)
    revenue: float | None = Field(default=None, ge=0)
    expenses: float | None = Field(default=None, ge=0)
    customers: int | None = Field(default=None, ge=0)
    transactions: int | None = Field(default=None, ge=0)
    average_transaction_value: float | None = Field(default=None, ge=0)
    inventory_purchases: float | None = Field(default=None, ge=0)
    stockouts: int | None = Field(default=None, ge=0)
    supplier_delays: int | None = Field(default=None, ge=0)
    marketing_spend: float | None = Field(default=None, ge=0)
    leads: int | None = Field(default=None, ge=0)
    repeat_customers: int | None = Field(default=None, ge=0)
    complaints: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1200)


class BusinessPerformanceEntryResponse(BusinessPerformanceEntryRequest):
    entry_id: str
    analysis_id: str
    created_at: str


class BusinessBoardReviewResponse(BaseModel):
    analysis_id: str
    performance_summary: dict[str, Any]
    top_issue: str
    top_opportunity: str
    financial_warning: str | None
    customer_insight: str | None
    inventory_insight: str | None
    recommended_experiments: list[str]
    next_week_priorities: list[str]
