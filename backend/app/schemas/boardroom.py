from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.domain.boardroom.ideas import StartupIdeaRequest
from app.domain.boardroom.models import StartupBrief


class StartupBriefRequest(BaseModel):
    startup_idea: str = Field(min_length=10, max_length=800)
    industry: str = Field(min_length=2, max_length=160)
    country: str = Field(min_length=2, max_length=120)
    budget: float = Field(gt=0)
    timeline_months: int = Field(ge=1, le=120)
    competitors: list[str] = Field(default_factory=list, max_length=20)
    target_audience: str = Field(min_length=3, max_length=500)
    funding_stage: str = Field(min_length=2, max_length=80)
    business_model: str = Field(min_length=2, max_length=120)

    @field_validator("competitors")
    @classmethod
    def normalize_competitors(cls, value: list[str]) -> list[str]:
        normalized = []
        for competitor in value:
            cleaned = competitor.strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    def to_domain(self) -> StartupBrief:
        return StartupBrief(
            startup_idea=self.startup_idea.strip(),
            industry=self.industry.strip(),
            country=self.country.strip(),
            budget=self.budget,
            timeline_months=self.timeline_months,
            competitors=tuple(self.competitors),
            target_audience=self.target_audience.strip(),
            funding_stage=self.funding_stage.strip(),
            business_model=self.business_model.strip(),
        )


class StartupBriefResponse(BaseModel):
    startup_idea: str
    industry: str
    country: str
    budget: float
    timeline_months: int
    competitors: list[str]
    target_audience: str
    funding_stage: str
    business_model: str


class StartupIdeaGenerationRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=500)
    interests: str | None = Field(default=None, max_length=240)
    industry: str | None = Field(default=None, max_length=160)
    country: str | None = Field(default=None, max_length=120)
    budget: float | None = Field(default=None, gt=0)
    business_model: str | None = Field(default=None, max_length=120)
    funding_stage: str | None = Field(default=None, max_length=80)
    number_of_ideas: int | None = Field(default=None, ge=1, le=30)

    def to_domain(self) -> StartupIdeaRequest:
        return StartupIdeaRequest(
            prompt=self.prompt,
            interests=self.interests,
            industry=self.industry,
            country=self.country,
            budget=self.budget,
            business_model=self.business_model,
            funding_stage=self.funding_stage,
            number_of_ideas=self.number_of_ideas,
        )


class StartupIdeaResponse(BaseModel):
    startup_name: str
    tagline: str
    problem: str
    solution: str
    target_audience: str
    revenue_model: str
    estimated_startup_cost: float
    estimated_tam: str
    innovation_score: int
    scalability_score: int
    difficulty: str
    competitive_advantage: str
    success_probability: int
    meeting_brief: StartupBriefResponse


class StartupIdeasResponse(BaseModel):
    ideas: list[StartupIdeaResponse]


class ExecutiveProfileResponse(BaseModel):
    role: str
    charter: str
    personality: str
    goals: list[str]
    risk_focus: list[str]


class ExecutiveCatalogResponse(BaseModel):
    executives: list[ExecutiveProfileResponse]


class MeetingTurnResponse(BaseModel):
    sequence: int | None = None
    round_number: int
    speaker_role: str
    turn_type: str
    topic: str | None = None
    stance: str
    confidence: float
    message: str
    concerns: list[str]
    recommendations: list[str]
    reasoning: list[str] = Field(default_factory=list)
    memory_references: list[str] = Field(default_factory=list)
    occurred_at: str | None = None


class BoardVoteResponse(BaseModel):
    role: str
    vote: str
    confidence: float
    rationale: str


class BoardReportResponse(BaseModel):
    title: str
    decision: str
    sections: dict[str, Any]


class BoardMeetingResponse(BaseModel):
    meeting_id: str
    consensus_reached: bool
    aggregate_confidence: float
    decision: str
    assessment: dict[str, Any]
    turns: list[MeetingTurnResponse]
    votes: list[BoardVoteResponse]
    report: BoardReportResponse


class MeetingSummaryResponse(BaseModel):
    meeting_id: str
    startup_idea: str
    industry: str
    country: str
    decision: str
    status: str
    aggregate_confidence: float
    consensus_reached: bool
    is_favorite: bool
    created_at: str | None = None
    completed_at: str | None = None
    report_title: str | None = None


class MeetingHistoryResponse(BaseModel):
    meetings: list[MeetingSummaryResponse]


class BoardMeetingDetailResponse(BoardMeetingResponse):
    startup_brief: StartupBriefResponse
    status: str
    is_favorite: bool
    created_at: str | None = None
    completed_at: str | None = None


class FavoriteMeetingRequest(BaseModel):
    is_favorite: bool


class FavoriteMeetingResponse(BaseModel):
    meeting_id: str
    is_favorite: bool


class DashboardResponse(BaseModel):
    total_meetings: int
    reports_generated: int
    approval_rate: float
    average_confidence: float
    top_industries: list[dict[str, Any]]
    recent_meetings: list[MeetingSummaryResponse]
    recent_reports: list[MeetingSummaryResponse]
    recent_board_decisions: list[MeetingSummaryResponse]


class GlobalSearchResponse(BaseModel):
    query: str
    meetings: list[MeetingSummaryResponse]
    reports: list[dict[str, Any]]
    executives: list[ExecutiveProfileResponse]


class ExportFormatResponse(BaseModel):
    format: Literal["json", "markdown", "pdf"]
