from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.boardroom.models import StartupBrief


@dataclass(frozen=True)
class StartupIdeaRequest:
    prompt: str | None = None
    interests: str | None = None
    industry: str | None = None
    country: str | None = None
    budget: float | None = None
    business_model: str | None = None
    funding_stage: str | None = None
    number_of_ideas: int | None = None


@dataclass(frozen=True)
class StartupIdea:
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
    meeting_brief: StartupBrief

    def to_dict(self) -> dict[str, object]:
        return {
            "startup_name": self.startup_name,
            "tagline": self.tagline,
            "problem": self.problem,
            "solution": self.solution,
            "target_audience": self.target_audience,
            "revenue_model": self.revenue_model,
            "estimated_startup_cost": self.estimated_startup_cost,
            "estimated_tam": self.estimated_tam,
            "innovation_score": self.innovation_score,
            "scalability_score": self.scalability_score,
            "difficulty": self.difficulty,
            "competitive_advantage": self.competitive_advantage,
            "success_probability": self.success_probability,
            "meeting_brief": {
                "startup_idea": self.meeting_brief.startup_idea,
                "industry": self.meeting_brief.industry,
                "country": self.meeting_brief.country,
                "budget": self.meeting_brief.budget,
                "timeline_months": self.meeting_brief.timeline_months,
                "competitors": list(self.meeting_brief.competitors),
                "target_audience": self.meeting_brief.target_audience,
                "funding_stage": self.meeting_brief.funding_stage,
                "business_model": self.meeting_brief.business_model,
            },
        }


INDUSTRY_ARCHETYPES: dict[str, tuple[str, ...]] = {
    "health": ("care navigation", "clinic operations", "patient finance", "remote monitoring"),
    "finance": ("cash-flow intelligence", "risk automation", "treasury workflows", "credit ops"),
    "education": ("skills verification", "teacher workflows", "career matching", "micro tutoring"),
    "climate": ("carbon accounting", "grid optimization", "circular supply", "weather resilience"),
    "retail": ("inventory signals", "loyalty automation", "checkout intelligence", "returns ops"),
    "legal": ("contract intelligence", "compliance evidence", "case workflow", "policy review"),
    "real estate": (
        "tenant operations",
        "property finance",
        "maintenance routing",
        "zoning insight",
    ),
    "logistics": (
        "dispatch intelligence",
        "warehouse planning",
        "shipment risk",
        "fleet utilization",
    ),
}

NAME_PREFIXES = (
    "Northstar",
    "Ledger",
    "Signal",
    "Aperture",
    "Foundry",
    "Pilot",
    "Vector",
    "Clearline",
    "Orbit",
    "Keystone",
)

NAME_SUFFIXES = (
    "OS",
    "Loop",
    "Stack",
    "IQ",
    "Works",
    "Grid",
    "Pilot",
    "Flow",
    "Lab",
    "Cloud",
)

CUSTOMER_SEGMENTS = (
    "independent operators",
    "regulated small businesses",
    "multi-site teams",
    "founder-led companies",
    "finance and operations leaders",
    "regional service providers",
)

BUSINESS_MODELS = ("B2B SaaS", "usage-based SaaS", "vertical SaaS", "AI services subscription")


def generate_startup_ideas(request: StartupIdeaRequest) -> list[StartupIdea]:
    count = _idea_count(request)
    industry = _clean(request.industry) or _infer_industry(request.prompt) or "AI productivity"
    country = _clean(request.country) or "United States"
    business_model = _clean(request.business_model) or _pick(BUSINESS_MODELS, industry)
    funding_stage = _clean(request.funding_stage) or "pre-seed"
    budget = float(request.budget or 150_000)
    interests = _clean(request.interests) or _clean(request.prompt) or industry
    archetypes = _archetypes_for(industry)

    ideas: list[StartupIdea] = []
    for index in range(count):
        archetype = _pick(archetypes, f"{industry}-{index}")
        segment = _pick(CUSTOMER_SEGMENTS, f"{interests}-{index}")
        prefix = _pick(NAME_PREFIXES, f"{industry}-{archetype}-{index}")
        suffix = _pick(NAME_SUFFIXES, f"{country}-{index}")
        startup_name = f"{prefix} {suffix}"
        wedge = _wedge(archetype, industry)
        cost = round(max(35_000, budget * (0.52 + (index % 5) * 0.08)), -3)
        innovation = 74 + ((index * 7 + len(industry)) % 22)
        scalability = 70 + ((index * 5 + len(country)) % 24)
        difficulty_score = 52 + ((index * 9 + len(archetype)) % 40)
        difficulty = _difficulty_label(difficulty_score)
        success_probability = min(
            91,
            max(42, int((innovation + scalability + (100 - difficulty_score)) / 3)),
        )
        target_audience = f"{segment} in {country}"
        startup_idea = (
            f"{startup_name}: an AI-enabled {archetype} platform for {target_audience} "
            f"that turns {wedge} into measurable operating leverage."
        )
        competitors = _competitors_for(industry, archetype)

        ideas.append(
            StartupIdea(
                startup_name=startup_name,
                tagline=f"{archetype.title()} for {segment}.",
                problem=(
                    f"{target_audience.capitalize()} still rely on fragmented tools, manual "
                    f"judgment, and delayed signals for {archetype}."
                ),
                solution=(
                    f"Unify intake, recommendations, workflow automation, and board-ready "
                    f"metrics around a focused {archetype} operating layer."
                ),
                target_audience=target_audience,
                revenue_model=business_model,
                estimated_startup_cost=cost,
                estimated_tam=_tam_for(industry, index),
                innovation_score=innovation,
                scalability_score=scalability,
                difficulty=difficulty,
                competitive_advantage=(
                    f"Own a narrow {industry} workflow with proprietary benchmarks, "
                    "workflow data, and expert-reviewed playbooks."
                ),
                success_probability=success_probability,
                meeting_brief=StartupBrief(
                    startup_idea=startup_idea,
                    industry=industry,
                    country=country,
                    budget=cost,
                    timeline_months=6 + (index % 4) * 3,
                    competitors=competitors,
                    target_audience=target_audience,
                    funding_stage=funding_stage,
                    business_model=business_model,
                ),
            )
        )
    return ideas


def _idea_count(request: StartupIdeaRequest) -> int:
    if request.number_of_ideas is not None:
        return max(1, min(30, request.number_of_ideas))
    if request.prompt:
        match = re.search(r"\b(\d{1,2})\b", request.prompt)
        if match:
            return max(1, min(30, int(match.group(1))))
    return 8


def _infer_industry(prompt: str | None) -> str | None:
    if not prompt:
        return None
    lowered = prompt.lower()
    for keyword in INDUSTRY_ARCHETYPES:
        if keyword in lowered:
            return keyword
    return None


def _archetypes_for(industry: str) -> tuple[str, ...]:
    lowered = industry.lower()
    for keyword, archetypes in INDUSTRY_ARCHETYPES.items():
        if keyword in lowered:
            return archetypes
    return (
        "decision intelligence",
        "workflow automation",
        "customer evidence",
        "risk monitoring",
    )


def _competitors_for(industry: str, archetype: str) -> tuple[str, ...]:
    lowered = industry.lower()
    if "health" in lowered:
        return ("Epic", "Athenahealth", "NexHealth")
    if "finance" in lowered or "fintech" in lowered:
        return ("Ramp", "Brex", "QuickBooks")
    if "education" in lowered:
        return ("Coursera", "Duolingo", "Khan Academy")
    if "legal" in lowered:
        return ("Clio", "Ironclad", "Harvey")
    return ("Notion", "Airtable", archetype.title())


def _tam_for(industry: str, index: int) -> str:
    base = 1.8 + (len(industry) % 7) * 0.6 + index * 0.35
    return f"${base:.1f}B serviceable global opportunity"


def _wedge(archetype: str, industry: str) -> str:
    return f"{industry} {archetype} signals"


def _difficulty_label(score: int) -> str:
    if score >= 82:
        return "Hard"
    if score >= 66:
        return "Moderate"
    return "Focused"


def _pick(options: tuple[str, ...], seed: str) -> str:
    index = sum(ord(character) for character in seed) % len(options)
    return options[index]


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
