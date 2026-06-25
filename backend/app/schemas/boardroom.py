from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

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
