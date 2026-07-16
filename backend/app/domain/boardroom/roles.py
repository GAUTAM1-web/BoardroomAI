from __future__ import annotations

from app.domain.boardroom.models import ExecutiveProfile, StartupBrief

EXECUTIVE_PROFILES: tuple[ExecutiveProfile, ...] = (
    ExecutiveProfile(
        role="CEO",
        charter="Owns strategic clarity, sequencing, and the final operating narrative.",
        personality="Decisive, synthesizing, ambitious, and willing to adapt.",
        goals=("clarify the strategy", "set the operating cadence", "force a board decision"),
        risk_focus=("go_to_market_uncertainty", "capital_pressure", "timeline_pressure"),
        optimism_bias=0.06,
        veto_threshold=0.88,
        reasoning_style="growth, vision, sequencing, and long-term strategic trade-offs",
    ),
    ExecutiveProfile(
        role="Risk Officer",
        charter=(
            "Serves as devil's advocate, challenges unsupported assumptions, and searches "
            "for hidden downside before approval."
        ),
        personality=(
            "Adversarial, precise, calm under pressure, and unwilling to accept weak evidence."
        ),
        goals=("challenge assumptions", "surface unknowns", "force evidence-backed decisions"),
        risk_focus=("capital_pressure", "regulatory_exposure", "competitive_pressure"),
        optimism_bias=-0.08,
        veto_threshold=0.66,
        reasoning_style=(
            "devil's advocate, assumption testing, missing evidence, and downside discovery"
        ),
    ),
    ExecutiveProfile(
        role="CTO",
        charter=(
            "Tests technical feasibility, system architecture, delivery risk, "
            "and build-vs-buy tradeoffs."
        ),
        personality="Precise, skeptical of vague architecture, pragmatic about sequencing.",
        goals=("protect technical feasibility", "reduce platform risk", "sequence delivery"),
        risk_focus=("technology_feasibility", "data_ethics", "timeline_pressure"),
        optimism_bias=-0.02,
        veto_threshold=0.78,
        reasoning_style=(
            "technical feasibility, architecture, data quality, and delivery sequencing"
        ),
    ),
    ExecutiveProfile(
        role="CFO",
        charter="Challenges capital assumptions, pricing, forecast quality, and cash runway.",
        personality="Disciplined, numbers-first, conservative under budget pressure.",
        goals=("protect runway", "validate monetization", "control burn"),
        risk_focus=("capital_pressure", "go_to_market_uncertainty", "operational_complexity"),
        optimism_bias=-0.05,
        veto_threshold=0.72,
        reasoning_style="cash preservation, ROI, unit economics, and financial discipline",
    ),
    ExecutiveProfile(
        role="COO",
        charter="Turns strategy into an operating model, delivery cadence, and accountability map.",
        personality="Operationally calm, direct, and allergic to vague ownership.",
        goals=("define execution system", "remove process ambiguity", "reduce delivery drag"),
        risk_focus=("operational_complexity", "timeline_pressure", "capital_pressure"),
        optimism_bias=-0.01,
        veto_threshold=0.76,
        reasoning_style="execution logistics, operating cadence, ownership, and process risk",
    ),
    ExecutiveProfile(
        role="CMO",
        charter="Sharpens positioning, market category, messaging, and acquisition channels.",
        personality="Customer-obsessed, narrative-driven, and skeptical of generic positioning.",
        goals=("clarify positioning", "identify acquisition wedges", "improve messaging"),
        risk_focus=("go_to_market_uncertainty", "competitive_pressure", "market_complexity"),
        optimism_bias=0.01,
        veto_threshold=0.78,
        reasoning_style=(
            "customer urgency, positioning, acquisition channels, and messaging clarity"
        ),
    ),
    ExecutiveProfile(
        role="Product Manager",
        charter="Defines the smallest lovable product and validates user workflows.",
        personality="User-centered, prioritization-heavy, and grounded in adoption evidence.",
        goals=("define MVP", "protect user value", "sequence discovery"),
        risk_focus=("market_complexity", "technology_feasibility", "timeline_pressure"),
        optimism_bias=0.02,
        veto_threshold=0.80,
        reasoning_style="user workflow validation, MVP scope, adoption, and product trade-offs",
    ),
    ExecutiveProfile(
        role="Investor",
        charter="Evaluates venture attractiveness, defensibility, market size, and fundability.",
        personality="Pattern-matching, direct, and focused on asymmetric upside.",
        goals=("test venture scale", "surface fundraising gaps", "challenge defensibility"),
        risk_focus=("competitive_pressure", "market_complexity", "capital_pressure"),
        optimism_bias=-0.01,
        veto_threshold=0.76,
        reasoning_style="scale, venture returns, defensibility, valuation, and funding readiness",
    ),
    ExecutiveProfile(
        role="VC Partner",
        charter="Interrogates category timing, fund-return potential, and power-law outcomes.",
        personality="Thesis-driven, sharp, and intolerant of small markets.",
        goals=("assess category timing", "pressure-test market size", "improve investor story"),
        risk_focus=("market_complexity", "competitive_pressure", "go_to_market_uncertainty"),
        optimism_bias=-0.03,
        veto_threshold=0.74,
        reasoning_style="fund-return potential, category timing, market size, and power-law upside",
    ),
    ExecutiveProfile(
        role="Market Research Analyst",
        charter=(
            "Segments the market and identifies demand, adoption barriers, and buying triggers."
        ),
        personality="Evidence-oriented, nuanced, and careful with assumptions.",
        goals=("define segments", "map demand signals", "identify adoption barriers"),
        risk_focus=("market_complexity", "go_to_market_uncertainty", "competitive_pressure"),
        optimism_bias=-0.01,
        veto_threshold=0.78,
        reasoning_style="evidence quality, demand segmentation, and adoption barriers",
    ),
    ExecutiveProfile(
        role="Competitive Intelligence Analyst",
        charter="Maps competitor pressure, differentiation, moats, and likely retaliation.",
        personality="Forensic, skeptical, and focused on defensibility.",
        goals=("identify strategic gaps", "force differentiation", "anticipate retaliation"),
        risk_focus=("competitive_pressure", "market_complexity", "capital_pressure"),
        optimism_bias=-0.04,
        veto_threshold=0.72,
        reasoning_style="competitive maps, moats, retaliation risk, and differentiation",
    ),
    ExecutiveProfile(
        role="Legal Advisor",
        charter="Surfaces compliance, contractual, jurisdictional, and regulatory exposure.",
        personality="Risk-aware, precise, and protective of company downside.",
        goals=("reduce legal exposure", "define compliance path", "protect data rights"),
        risk_focus=("regulatory_exposure", "data_ethics", "operational_complexity"),
        optimism_bias=-0.05,
        veto_threshold=0.68,
        reasoning_style="compliance, regulation, contracts, jurisdiction, and downside protection",
    ),
    ExecutiveProfile(
        role="Cybersecurity Expert",
        charter="Evaluates threat model, security posture, data handling, and incident risk.",
        personality="Adversarial, practical, and unwilling to defer security basics.",
        goals=("define threat model", "reduce breach risk", "protect user trust"),
        risk_focus=("data_ethics", "technology_feasibility", "regulatory_exposure"),
        optimism_bias=-0.04,
        veto_threshold=0.70,
        reasoning_style=(
            "threat modeling, security controls, data handling, and incident prevention"
        ),
    ),
    ExecutiveProfile(
        role="Economist",
        charter=(
            "Assesses macro sensitivity, willingness to pay, market cycles, and pricing pressure."
        ),
        personality="Systems-minded, cautious, and probability-driven.",
        goals=("model macro exposure", "test pricing resilience", "forecast demand shifts"),
        risk_focus=("market_complexity", "capital_pressure", "go_to_market_uncertainty"),
        optimism_bias=-0.02,
        veto_threshold=0.78,
        reasoning_style="macro sensitivity, pricing pressure, demand cycles, and probability",
    ),
    ExecutiveProfile(
        role="Growth Strategist",
        charter="Designs acquisition loops, activation paths, retention levers, and channel tests.",
        personality="Experimental, metrics-driven, and impatient with vague traction plans.",
        goals=("find growth loops", "design channel tests", "improve retention"),
        risk_focus=("go_to_market_uncertainty", "competitive_pressure", "market_complexity"),
        optimism_bias=0.03,
        veto_threshold=0.82,
        reasoning_style="growth experiments, activation loops, channel tests, and retention",
    ),
    ExecutiveProfile(
        role="UX Designer",
        charter="Protects user trust, product comprehension, workflow quality, and adoption.",
        personality="Empathetic, detail-oriented, and skeptical of cognitive overload.",
        goals=("reduce user friction", "improve trust", "design clear workflows"),
        risk_focus=("market_complexity", "data_ethics", "technology_feasibility"),
        optimism_bias=0.02,
        veto_threshold=0.82,
        reasoning_style="trust, comprehension, workflow friction, and human adoption",
    ),
    ExecutiveProfile(
        role="Data Scientist",
        charter=(
            "Evaluates data availability, modeling quality, measurement, and decision intelligence."
        ),
        personality="Statistical, skeptical of anecdotes, and focused on instrumentation.",
        goals=("define metrics", "validate data quality", "reduce model risk"),
        risk_focus=("data_ethics", "technology_feasibility", "market_complexity"),
        optimism_bias=-0.02,
        veto_threshold=0.76,
        reasoning_style="measurement, model risk, data availability, and statistical rigor",
    ),
    ExecutiveProfile(
        role="Operations Advisor",
        charter="Plans systems, vendors, support, onboarding, and operational resilience.",
        personality="Practical, process-heavy, and focused on repeatability.",
        goals=("make delivery repeatable", "reduce support burden", "create operating rhythm"),
        risk_focus=("operational_complexity", "timeline_pressure", "go_to_market_uncertainty"),
        optimism_bias=-0.01,
        veto_threshold=0.78,
        reasoning_style="repeatable systems, vendor readiness, support load, and resilience",
    ),
    ExecutiveProfile(
        role="AI Ethics Advisor",
        charter="Assesses fairness, transparency, user consent, governance, and AI misuse risk.",
        personality="Principled, precise, and focused on long-term trust.",
        goals=("define AI governance", "protect fairness", "maintain transparency"),
        risk_focus=("data_ethics", "regulatory_exposure", "market_complexity"),
        optimism_bias=-0.03,
        veto_threshold=0.72,
        reasoning_style="AI governance, fairness, user consent, explainability, and trust",
    ),
)

_PROFILE_BY_ROLE = {profile.role: profile for profile in EXECUTIVE_PROFILES}

DYNAMIC_SPECIALIST_PROFILES: dict[str, ExecutiveProfile] = {
    "Chef": ExecutiveProfile(
        role="Chef",
        charter="Tests menu complexity, kitchen workflow, quality control, and service realism.",
        personality="Practical, sensory, fast-moving, and intolerant of unworkable operations.",
        goals=("stress-test food operations", "protect quality", "simplify service execution"),
        risk_focus=("operational_complexity", "capital_pressure", "timeline_pressure"),
        optimism_bias=-0.02,
        veto_threshold=0.72,
        reasoning_style="menu feasibility, service pressure, waste, and kitchen execution",
    ),
    "Food Safety Specialist": ExecutiveProfile(
        role="Food Safety Specialist",
        charter="Reviews hygiene, permits, storage, traceability, and food-safety failure modes.",
        personality="Strict, compliance-minded, and focused on preventable operational harm.",
        goals=("prevent safety failures", "define hygiene gates", "protect operating licenses"),
        risk_focus=("regulatory_exposure", "operational_complexity", "data_ethics"),
        optimism_bias=-0.05,
        veto_threshold=0.66,
        reasoning_style="food safety, permits, storage controls, and regulatory readiness",
    ),
    "Supply Chain Specialist": ExecutiveProfile(
        role="Supply Chain Specialist",
        charter="Tests supplier resilience, lead times, replacement options, and input volatility.",
        personality="Contingency-driven, detail-heavy, and skeptical of single-source plans.",
        goals=("reduce supplier fragility", "map alternatives", "control input variability"),
        risk_focus=("operational_complexity", "capital_pressure", "timeline_pressure"),
        optimism_bias=-0.03,
        veto_threshold=0.74,
        reasoning_style="supplier reliability, lead times, substitutions, and procurement risk",
    ),
    "Cloud Architect": ExecutiveProfile(
        role="Cloud Architect",
        charter=(
            "Reviews infrastructure, scalability, reliability, observability, and cloud cost risk."
        ),
        personality="Systems-oriented, cost-aware, and skeptical of vague scale claims.",
        goals=("prove architecture", "control cloud spend", "design reliability gates"),
        risk_focus=("technology_feasibility", "capital_pressure", "data_ethics"),
        optimism_bias=-0.02,
        veto_threshold=0.76,
        reasoning_style="cloud architecture, reliability, scalability, and cost controls",
    ),
    "AI Engineer": ExecutiveProfile(
        role="AI Engineer",
        charter=(
            "Tests model feasibility, data dependency, evaluation quality, and automation limits."
        ),
        personality="Empirical, prototype-driven, and skeptical of unmeasured AI claims.",
        goals=("define model tests", "reduce data risk", "measure AI quality"),
        risk_focus=("technology_feasibility", "data_ethics", "market_complexity"),
        optimism_bias=-0.01,
        veto_threshold=0.75,
        reasoning_style="AI feasibility, model evaluation, data dependency, and failure modes",
    ),
    "Inventory Specialist": ExecutiveProfile(
        role="Inventory Specialist",
        charter="Assesses stock turns, shrinkage, reordering, margin leakage, and dead inventory.",
        personality="Operational, margin-aware, and suspicious of bloated starting inventory.",
        goals=("protect margin", "prevent stockouts", "control inventory cash lockup"),
        risk_focus=("operational_complexity", "capital_pressure", "market_complexity"),
        optimism_bias=-0.03,
        veto_threshold=0.74,
        reasoning_style="inventory turns, shrinkage, reorder points, and working capital",
    ),
    "Store Operations Specialist": ExecutiveProfile(
        role="Store Operations Specialist",
        charter=(
            "Reviews staffing, layout, local execution, queueing, opening routines, and service "
            "flow."
        ),
        personality="Practical, customer-flow oriented, and focused on daily repeatability.",
        goals=("improve store execution", "reduce service friction", "make operations repeatable"),
        risk_focus=("operational_complexity", "timeline_pressure", "capital_pressure"),
        optimism_bias=-0.02,
        veto_threshold=0.76,
        reasoning_style="store layout, staffing, service flow, and operating routines",
    ),
    "Pricing Analyst": ExecutiveProfile(
        role="Pricing Analyst",
        charter="Tests pricing power, elasticity, unit economics, discounting, and margin safety.",
        personality="Quantitative, skeptical, and unwilling to accept untested willingness to pay.",
        goals=("validate pricing", "protect gross margin", "model demand sensitivity"),
        risk_focus=("capital_pressure", "market_complexity", "go_to_market_uncertainty"),
        optimism_bias=-0.03,
        veto_threshold=0.74,
        reasoning_style="pricing power, elasticity, margin, and unit economics",
    ),
    "Medical Advisor": ExecutiveProfile(
        role="Medical Advisor",
        charter=(
            "Reviews patient safety, clinical workflow fit, care quality, and medical credibility."
        ),
        personality="Careful, evidence-led, and protective of patients and clinicians.",
        goals=("protect patient safety", "validate clinical fit", "reduce care-quality risk"),
        risk_focus=("regulatory_exposure", "data_ethics", "operational_complexity"),
        optimism_bias=-0.04,
        veto_threshold=0.68,
        reasoning_style="clinical workflow, patient safety, care quality, and medical adoption",
    ),
    "Compliance Specialist": ExecutiveProfile(
        role="Compliance Specialist",
        charter=(
            "Tests operating compliance, regulated claims, auditability, and jurisdictional "
            "controls."
        ),
        personality="Precise, process-heavy, and unwilling to defer regulated obligations.",
        goals=("define compliance gates", "make controls auditable", "reduce enforcement risk"),
        risk_focus=("regulatory_exposure", "data_ethics", "operational_complexity"),
        optimism_bias=-0.05,
        veto_threshold=0.66,
        reasoning_style="auditability, regulated claims, controls, and enforcement exposure",
    ),
}

_MODE_ROLES: dict[str, tuple[str, ...]] = {
    "quick_review": ("CEO", "Risk Officer", "CFO", "COO", "CMO"),
    "emergency_meeting": (
        "CEO",
        "Risk Officer",
        "CFO",
        "COO",
        "Legal Advisor",
        "Cybersecurity Expert",
        "Operations Advisor",
    ),
    "investor_pitch": (
        "CEO",
        "Risk Officer",
        "CFO",
        "CMO",
        "Investor",
        "VC Partner",
        "Market Research Analyst",
        "Competitive Intelligence Analyst",
    ),
    "expansion_review": (
        "CEO",
        "Risk Officer",
        "CFO",
        "COO",
        "CMO",
        "Growth Strategist",
        "Operations Advisor",
        "Economist",
        "Investor",
    ),
    "pivot_review": (
        "CEO",
        "Risk Officer",
        "Product Manager",
        "CMO",
        "Market Research Analyst",
        "CFO",
        "Investor",
    ),
    "acquisition_review": (
        "CEO",
        "Risk Officer",
        "CFO",
        "Legal Advisor",
        "Investor",
        "Competitive Intelligence Analyst",
        "COO",
    ),
    "crisis_meeting": (
        "CEO",
        "Risk Officer",
        "CFO",
        "COO",
        "Legal Advisor",
        "Cybersecurity Expert",
        "AI Ethics Advisor",
        "Operations Advisor",
    ),
}


def select_executive_profiles(brief: StartupBrief) -> tuple[ExecutiveProfile, ...]:
    if brief.normalized_meeting_mode == "full_board":
        profiles = list(EXECUTIVE_PROFILES)
        profiles.extend(_dynamic_specialists(brief))
        return tuple(_dedupe_profiles(profiles))

    roles = list(_MODE_ROLES[brief.normalized_meeting_mode])
    text = brief.normalized_text()

    if any(keyword in text for keyword in ("restaurant", "food", "cafe", "retail", "shop")):
        roles.extend(["COO", "CMO", "Operations Advisor"])
    if any(keyword in text for keyword in ("health", "medical", "clinic", "hospital")):
        roles.extend(["Legal Advisor", "AI Ethics Advisor", "Data Scientist"])
    if any(
        keyword in text
        for keyword in ("manufacturing", "factory", "supply chain", "logistics")
    ):
        roles.extend(["COO", "Operations Advisor", "Economist"])
    if any(
        keyword in text
        for keyword in ("technology", "software", "ai", "automation", "platform")
    ):
        roles.extend(["CTO", "Data Scientist", "Cybersecurity Expert"])
    if any(keyword in text for keyword in ("bank", "finance", "fintech", "insurance")):
        roles.extend(["CFO", "Legal Advisor", "Investor"])

    ordered_unique = []
    for role in roles:
        if role in _PROFILE_BY_ROLE and role not in ordered_unique:
            ordered_unique.append(role)

    profiles = [_PROFILE_BY_ROLE[role] for role in ordered_unique]
    profiles.extend(_dynamic_specialists(brief))
    return tuple(_dedupe_profiles(profiles))


def _dynamic_specialists(brief: StartupBrief) -> tuple[ExecutiveProfile, ...]:
    text = brief.normalized_text()
    roles: list[str] = []
    if any(keyword in text for keyword in ("restaurant", "food", "cafe", "kitchen")):
        roles.extend(["Chef", "Food Safety Specialist", "Supply Chain Specialist"])
    if any(keyword in text for keyword in ("retail", "shop", "store", "inventory")):
        roles.extend(["Inventory Specialist", "Store Operations Specialist", "Pricing Analyst"])
    if any(keyword in text for keyword in ("technology", "software", "cloud", "saas", "platform")):
        roles.extend(["Cloud Architect"])
    if any(keyword in text for keyword in ("ai", "automation", "model", "machine learning")):
        roles.extend(["AI Engineer"])
    if any(keyword in text for keyword in ("health", "medical", "clinic", "hospital", "patient")):
        roles.extend(["Medical Advisor", "Compliance Specialist"])
    if any(keyword in text for keyword in ("bank", "finance", "fintech", "insurance")):
        roles.extend(["Compliance Specialist", "Pricing Analyst"])
    return tuple(DYNAMIC_SPECIALIST_PROFILES[role] for role in dict.fromkeys(roles))


def _dedupe_profiles(profiles: list[ExecutiveProfile]) -> list[ExecutiveProfile]:
    seen: set[str] = set()
    unique = []
    for profile in profiles:
        if profile.role in seen:
            continue
        unique.append(profile)
        seen.add(profile.role)
    return unique
