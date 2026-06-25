from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class StartupBrief:
    startup_idea: str
    industry: str
    country: str
    budget: float
    timeline_months: int
    competitors: tuple[str, ...]
    target_audience: str
    funding_stage: str
    business_model: str

    def normalized_text(self) -> str:
        return " ".join(
            [
                self.startup_idea,
                self.industry,
                self.country,
                self.target_audience,
                self.funding_stage,
                self.business_model,
                " ".join(self.competitors),
            ]
        ).lower()


@dataclass(frozen=True)
class ExecutiveProfile:
    role: str
    charter: str
    personality: str
    goals: tuple[str, ...]
    risk_focus: tuple[str, ...]
    optimism_bias: float
    veto_threshold: float


@dataclass(frozen=True)
class StrategicAssessment:
    risk_scores: dict[str, float]
    signals: dict[str, str]

    @property
    def overall_risk(self) -> float:
        return sum(self.risk_scores.values()) / max(len(self.risk_scores), 1)

    @property
    def primary_risks(self) -> list[tuple[str, float]]:
        return sorted(self.risk_scores.items(), key=lambda item: item[1], reverse=True)[:4]


@dataclass(frozen=True)
class ExecutiveOpinion:
    role: str
    stance: str
    confidence: float
    message: str
    concerns: tuple[str, ...]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "stance": self.stance,
            "confidence": round(self.confidence, 3),
            "message": self.message,
            "concerns": list(self.concerns),
            "recommendations": list(self.recommendations),
        }


@dataclass(frozen=True)
class MeetingTurn:
    round_number: int
    speaker_role: str
    turn_type: str
    stance: str
    confidence: float
    message: str
    concerns: tuple[str, ...] = field(default_factory=tuple)
    recommendations: tuple[str, ...] = field(default_factory=tuple)
    topic: str = "Strategy"
    reasoning: tuple[str, ...] = field(default_factory=tuple)
    memory_references: tuple[str, ...] = field(default_factory=tuple)
    sequence: int | None = None
    occurred_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "round_number": self.round_number,
            "speaker_role": self.speaker_role,
            "turn_type": self.turn_type,
            "topic": self.topic,
            "stance": self.stance,
            "confidence": round(self.confidence, 3),
            "message": self.message,
            "concerns": list(self.concerns),
            "recommendations": list(self.recommendations),
            "reasoning": list(self.reasoning),
            "memory_references": list(self.memory_references),
            "occurred_at": self.occurred_at,
        }


@dataclass(frozen=True)
class BoardVote:
    role: str
    vote: str
    confidence: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "vote": self.vote,
            "confidence": round(self.confidence, 3),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class BoardReport:
    title: str
    decision: str
    sections: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "decision": self.decision,
            "sections": self.sections,
        }


@dataclass(frozen=True)
class BoardMeetingResult:
    meeting_id: UUID
    consensus_reached: bool
    aggregate_confidence: float
    decision: str
    assessment: StrategicAssessment
    turns: tuple[MeetingTurn, ...]
    votes: tuple[BoardVote, ...]
    report: BoardReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "meeting_id": str(self.meeting_id),
            "consensus_reached": self.consensus_reached,
            "aggregate_confidence": round(self.aggregate_confidence, 3),
            "decision": self.decision,
            "assessment": {
                "overall_risk": round(self.assessment.overall_risk, 3),
                "risk_scores": {
                    key: round(value, 3) for key, value in self.assessment.risk_scores.items()
                },
                "signals": self.assessment.signals,
            },
            "turns": [turn.to_dict() for turn in self.turns],
            "votes": [vote.to_dict() for vote in self.votes],
            "report": self.report.to_dict(),
        }
