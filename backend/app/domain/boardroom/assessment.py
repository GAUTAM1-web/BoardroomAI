from __future__ import annotations

from app.domain.boardroom.models import StartupBrief, StrategicAssessment

REGULATED_KEYWORDS = {
    "health",
    "healthcare",
    "medical",
    "clinic",
    "finance",
    "fintech",
    "bank",
    "insurance",
    "legal",
    "law",
    "education",
    "edtech",
    "crypto",
    "defense",
    "government",
}

AI_SENSITIVE_KEYWORDS = {
    "ai",
    "machine learning",
    "predict",
    "model",
    "credit",
    "diagnosis",
    "identity",
    "biometric",
    "personalization",
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _contains_any(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def assess_brief(brief: StartupBrief) -> StrategicAssessment:
    text = brief.normalized_text()
    competitor_count = len([competitor for competitor in brief.competitors if competitor.strip()])

    budget_risk = 0.24
    if brief.budget < 50_000:
        budget_risk = 0.92
    elif brief.budget < 125_000:
        budget_risk = 0.72
    elif brief.budget < 300_000:
        budget_risk = 0.52
    elif brief.budget > 1_500_000:
        budget_risk = 0.28

    timeline_risk = 0.25
    if brief.timeline_months <= 3:
        timeline_risk = 0.9
    elif brief.timeline_months <= 6:
        timeline_risk = 0.68
    elif brief.timeline_months <= 12:
        timeline_risk = 0.45

    competitive_pressure = clamp(0.22 + competitor_count * 0.14)
    if any(name.lower() in text for name in ("google", "microsoft", "amazon", "openai", "stripe")):
        competitive_pressure = clamp(competitive_pressure + 0.15)

    regulatory_exposure = 0.25
    if _contains_any(text, REGULATED_KEYWORDS):
        regulatory_exposure = 0.72
    if "united states" in text or "europe" in text or "eu" in text:
        regulatory_exposure = clamp(regulatory_exposure + 0.08)

    data_ethics = 0.28
    if _contains_any(text, AI_SENSITIVE_KEYWORDS):
        data_ethics = 0.66
    if _contains_any(text, REGULATED_KEYWORDS) and _contains_any(text, AI_SENSITIVE_KEYWORDS):
        data_ethics = 0.82

    technology_feasibility = 0.35
    if "ai" in text or "automation" in text or "real-time" in text:
        technology_feasibility = 0.58
    if "enterprise" in text or "platform" in text or "marketplace" in text:
        technology_feasibility = clamp(technology_feasibility + 0.1)

    market_complexity = 0.4
    if "b2b" in text or "enterprise" in text:
        market_complexity = 0.58
    if "consumer" in text or "marketplace" in text:
        market_complexity = clamp(market_complexity + 0.12)
    if "pre-seed" in text or "idea" in text:
        market_complexity = clamp(market_complexity + 0.08)

    go_to_market_uncertainty = 0.44
    if "b2b" in text:
        go_to_market_uncertainty = 0.6
    if "freemium" in text or "consumer" in text:
        go_to_market_uncertainty = clamp(go_to_market_uncertainty + 0.14)
    if brief.budget < 150_000 and competitor_count >= 3:
        go_to_market_uncertainty = clamp(go_to_market_uncertainty + 0.12)

    operational_complexity = 0.34
    if "marketplace" in text or "logistics" in text or "healthcare" in text:
        operational_complexity = 0.62
    if brief.timeline_months <= 6:
        operational_complexity = clamp(operational_complexity + 0.08)

    risk_scores = {
        "market_complexity": market_complexity,
        "technology_feasibility": technology_feasibility,
        "capital_pressure": budget_risk,
        "timeline_pressure": timeline_risk,
        "regulatory_exposure": regulatory_exposure,
        "competitive_pressure": competitive_pressure,
        "go_to_market_uncertainty": go_to_market_uncertainty,
        "operational_complexity": operational_complexity,
        "data_ethics": data_ethics,
    }

    signals = {
        "budget_signal": _budget_signal(brief.budget),
        "timeline_signal": _timeline_signal(brief.timeline_months),
        "competition_signal": _competition_signal(competitor_count),
        "regulatory_signal": "regulated" if regulatory_exposure >= 0.65 else "standard",
        "ai_governance_signal": "heightened" if data_ethics >= 0.65 else "standard",
    }

    return StrategicAssessment(risk_scores=risk_scores, signals=signals)


def _budget_signal(budget: float) -> str:
    if budget < 50_000:
        return "severely constrained"
    if budget < 125_000:
        return "constrained"
    if budget < 300_000:
        return "lean but workable"
    return "sufficient for a focused MVP"


def _timeline_signal(timeline_months: int) -> str:
    if timeline_months <= 3:
        return "extremely compressed"
    if timeline_months <= 6:
        return "compressed"
    if timeline_months <= 12:
        return "reasonable with strict scope"
    return "strategic runway available"


def _competition_signal(competitor_count: int) -> str:
    if competitor_count == 0:
        return "unknown competitive landscape"
    if competitor_count <= 2:
        return "moderate competitor visibility"
    if competitor_count <= 4:
        return "crowded market"
    return "highly contested market"
