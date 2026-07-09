from __future__ import annotations

from datetime import UTC, datetime
from math import ceil
from typing import Any
from uuid import uuid4

from app.schemas.business import (
    BusinessAnalysisRequest,
    BusinessPerformanceEntryRequest,
    ManualCompetitorInput,
    ManualSupplierInput,
)

DISCLAIMER = (
    "BoardroomAI provides decision support based on available evidence and assumptions. "
    "It does not guarantee business success. Verify location, demand, costs, suppliers, "
    "legal requirements, and financial assumptions before investing."
)

DEMO_NOTICE = "Demo data - not live local evidence."


BUSINESS_PROFILES: dict[str, dict[str, Any]] = {
    "mobile": {
        "label": "Mobile repair shop",
        "supplier_categories": [
            "spare-parts wholesalers",
            "screen suppliers",
            "battery suppliers",
            "accessories wholesalers",
            "repair-tool suppliers",
            "authorized distributors",
        ],
        "inventory_items": [
            ("Common charging cables", "essential", (20, 60), (80, 240)),
            ("Screen protectors and cases", "recommended", (20, 80), (150, 600)),
            ("Repair tools", "equipment", (1, 2), (400, 1200)),
            ("Common batteries and screens", "essential", (5, 20), (800, 4000)),
            ("Consumables and adhesives", "consumables", (1, 4), (120, 500)),
        ],
        "average_transaction_value": 45,
        "gross_margin_percent": 45,
        "setup_ranges": {
            "equipment": (1200, 5500),
            "inventory": (1500, 8500),
            "renovation": (800, 4000),
            "licenses": (100, 800),
            "marketing": (250, 1200),
            "utilities_monthly": (120, 450),
        },
    },
    "cycle": {
        "label": "Cycle repair shop",
        "supplier_categories": [
            "bicycle-parts wholesalers",
            "spare-parts distributors",
            "authorized bicycle dealers",
            "tool suppliers",
            "tyre and tube suppliers",
            "accessory wholesalers",
            "lubricant suppliers",
            "e-bike component suppliers",
        ],
        "inventory_items": [
            ("Common tyre sizes", "essential", (8, 30), (160, 900)),
            ("Tubes and puncture material", "essential", (20, 80), (120, 500)),
            ("Brake and gear cables", "recommended", (20, 60), (100, 350)),
            ("Chains, brake pads, bearings", "recommended", (10, 40), (250, 1200)),
            ("Repair tools and stand", "equipment", (1, 2), (350, 1500)),
            ("Lubricants and cleaning supplies", "consumables", (4, 12), (80, 350)),
        ],
        "average_transaction_value": 18,
        "gross_margin_percent": 42,
        "setup_ranges": {
            "equipment": (700, 3500),
            "inventory": (800, 4500),
            "renovation": (400, 2500),
            "licenses": (80, 600),
            "marketing": (150, 800),
            "utilities_monthly": (80, 300),
        },
    },
    "cafe": {
        "label": "Cafe or food service",
        "supplier_categories": [
            "coffee suppliers",
            "dairy suppliers",
            "bakery suppliers",
            "equipment suppliers",
            "packaging suppliers",
            "fresh ingredient distributors",
        ],
        "inventory_items": [
            ("Coffee, tea, milk, and core ingredients", "essential", (7, 21), (600, 3000)),
            ("Packaging and disposables", "essential", (1, 4), (250, 1200)),
            ("Brewing and kitchen equipment", "equipment", (1, 1), (3000, 20000)),
            ("Cleaning and safety supplies", "consumables", (1, 3), (150, 800)),
            ("Launch menu trial inventory", "recommended", (1, 2), (500, 2500)),
        ],
        "average_transaction_value": 7,
        "gross_margin_percent": 58,
        "setup_ranges": {
            "equipment": (6000, 35000),
            "inventory": (1200, 7000),
            "renovation": (4000, 30000),
            "licenses": (400, 3000),
            "marketing": (500, 3000),
            "utilities_monthly": (350, 1600),
        },
    },
    "service": {
        "label": "Service business",
        "supplier_categories": [
            "tools and equipment suppliers",
            "consumables suppliers",
            "software and communication providers",
            "local service partners",
        ],
        "inventory_items": [
            ("Core tools and starter equipment", "essential", (1, 2), (500, 5000)),
            ("Consumables and replacement supplies", "essential", (1, 4), (150, 1200)),
            ("Scheduling and communication setup", "recommended", (1, 1), (100, 800)),
            ("Marketing collateral", "recommended", (1, 2), (150, 1000)),
        ],
        "average_transaction_value": 60,
        "gross_margin_percent": 55,
        "setup_ranges": {
            "equipment": (500, 6000),
            "inventory": (200, 2500),
            "renovation": (0, 1500),
            "licenses": (100, 1200),
            "marketing": (250, 2000),
            "utilities_monthly": (50, 250),
        },
    },
    "technology": {
        "label": "Technology startup",
        "supplier_categories": [
            "cloud infrastructure",
            "software tooling",
            "security and compliance advisors",
            "design and engineering partners",
        ],
        "inventory_items": [
            ("Cloud and development tools", "essential", (1, 1), (300, 3000)),
            ("Security and compliance review", "recommended", (1, 1), (1000, 12000)),
            ("Prototype design and testing", "recommended", (1, 1), (1000, 15000)),
        ],
        "average_transaction_value": 500,
        "gross_margin_percent": 75,
        "setup_ranges": {
            "equipment": (1000, 6000),
            "inventory": (0, 500),
            "renovation": (0, 0),
            "licenses": (200, 2000),
            "marketing": (1000, 8000),
            "utilities_monthly": (100, 800),
        },
    },
    "retail": {
        "label": "Retail business",
        "supplier_categories": [
            "wholesalers",
            "distributors",
            "packaging suppliers",
            "fixture suppliers",
            "backup inventory suppliers",
        ],
        "inventory_items": [
            ("Core opening inventory", "essential", (1, 1), (2000, 18000)),
            ("Display fixtures and billing setup", "equipment", (1, 1), (800, 7000)),
            ("Packaging and consumables", "consumables", (1, 3), (200, 1500)),
            ("Promotional launch inventory", "optional", (1, 2), (500, 5000)),
        ],
        "average_transaction_value": 25,
        "gross_margin_percent": 35,
        "setup_ranges": {
            "equipment": (1000, 8000),
            "inventory": (2500, 20000),
            "renovation": (1000, 12000),
            "licenses": (150, 1500),
            "marketing": (300, 2500),
            "utilities_monthly": (150, 700),
        },
    },
}


def build_business_analysis(
    payload: BusinessAnalysisRequest,
    settings: Any | None = None,
) -> dict[str, Any]:
    generated_at = datetime.now(UTC)
    analysis_id = str(uuid4())
    profile_key = _profile_key(payload)
    profile = BUSINESS_PROFILES[profile_key]
    location_label = _location_label(payload)
    warnings = _provider_warnings(payload, settings)
    evidence = _base_evidence(payload, generated_at)

    competitors = _competitors(payload.manual_competitors, payload, generated_at, evidence)
    suppliers = _suppliers(payload.manual_suppliers, payload, profile, generated_at, evidence)
    score = _opportunity_score(payload, profile, competitors, suppliers, evidence)
    candidate_areas = _candidate_areas(payload, score, suppliers)
    properties = _properties(payload, suppliers)
    financials = _financials(payload, profile)
    daily_sales = _daily_sales(payload, profile, financials)
    procurement_plan = _procurement_plan(payload, profile, suppliers)
    customer_segments = _customer_segments(payload, generated_at, evidence)
    validation_plan = _validation_plan(payload, profile, score)
    missing_information = _missing_information(payload, competitors, suppliers, financials)
    recommendation = _recommendation(payload, score, financials, missing_information)
    performance_tracking = _performance_tracking()
    board_brief = _board_brief(payload, recommendation, competitors, score, financials)
    report = _report(
        payload=payload,
        profile=profile,
        recommendation=recommendation,
        score=score,
        competitors=competitors,
        suppliers=suppliers,
        candidate_areas=candidate_areas,
        properties=properties,
        customer_segments=customer_segments,
        procurement_plan=procurement_plan,
        financials=financials,
        daily_sales=daily_sales,
        validation_plan=validation_plan,
        evidence=evidence,
        missing_information=missing_information,
        performance_tracking=performance_tracking,
    )

    if payload.data_mode == "demo":
        warnings.append(DEMO_NOTICE)
    if (
        payload.data_mode == "manual"
        and not payload.manual_competitors
        and not payload.manual_suppliers
    ):
        warnings.append(
            "Manual mode has no competitor or supplier entries yet. Add observations or quotations "
            "to improve evidence quality."
        )

    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "data_mode": payload.data_mode,
        "provider_label": _provider_label(payload, settings),
        "generated_at": generated_at.isoformat(),
        "demo_notice": DEMO_NOTICE if payload.data_mode == "demo" else None,
        "disclaimer": DISCLAIMER,
        "intake": {
            "workflow_type": payload.workflow_type,
            "business_idea": _business_idea(payload),
            "business_category": payload.business_category or profile["label"],
            "location_label": location_label,
            "location_source": payload.location.source,
            "budget": payload.budget,
            "priorities": payload.priorities,
            "risk_tolerance": payload.risk_tolerance,
            "timeline": payload.timeline,
            "data_mode": payload.data_mode,
            "currency_note": (
                "Amounts use the currency implied by the user's inputs. Benchmark values are "
                "configurable planning assumptions, not verified local prices."
            ),
        },
        "recommendation": recommendation,
        "opportunity_score": score,
        "evidence_confidence": _evidence_confidence(evidence, payload),
        "evidence": evidence,
        "competitors": competitors,
        "suppliers": suppliers,
        "candidate_areas": candidate_areas,
        "properties": properties,
        "customer_segments": customer_segments,
        "procurement_plan": procurement_plan,
        "financials": financials,
        "daily_sales": daily_sales,
        "validation_plan": validation_plan,
        "performance_tracking": performance_tracking,
        "missing_information": missing_information,
        "warnings": warnings,
        "board_brief": board_brief,
        "report": report,
    }


def provider_status(settings: Any) -> dict[str, Any]:
    maps_key = bool(getattr(settings, "maps_api_key", ""))
    places_key = bool(getattr(settings, "places_api_key", ""))
    return {
        "default_mode": getattr(settings, "business_data_mode", "demo"),
        "maps_provider": getattr(settings, "maps_provider", "none"),
        "live_maps_configured": maps_key,
        "live_places_configured": places_key,
        "modes": [
            {
                "mode": "demo",
                "label": DEMO_NOTICE,
                "description": "Uses labeled benchmark scaffolding only; no live local listings.",
            },
            {
                "mode": "manual",
                "label": "Manual-data mode",
                "description": (
                    "Uses competitors, suppliers, quotations, observations, and costs entered "
                    "by the user."
                ),
            },
            {
                "mode": "live",
                "label": "Live-provider mode",
                "description": (
                    "Requires configured provider credentials. Falls back with warnings when "
                    "not configured."
                ),
            },
        ],
    }


def build_board_review(
    analysis: dict[str, Any],
    entries: list[BusinessPerformanceEntryRequest],
) -> dict[str, Any]:
    result = analysis.get("result", analysis)
    forecast = result.get("daily_sales", {}).get("monthly_targets", {})
    expected_revenue = _num(forecast.get("required_monthly_revenue"))
    revenue_values = [_num(entry.revenue) for entry in entries if entry.revenue is not None]
    expense_values = [_num(entry.expenses) for entry in entries if entry.expenses is not None]
    customer_values = [_num(entry.customers) for entry in entries if entry.customers is not None]
    total_revenue = sum(revenue_values)
    total_expenses = sum(expense_values)
    total_customers = sum(customer_values)
    latest = entries[-1] if entries else None
    variance = None
    if expected_revenue and revenue_values:
        variance = round((revenue_values[-1] - expected_revenue) / expected_revenue, 3)

    top_issue = "Not enough actual performance data yet."
    if (
        latest
        and latest.revenue is not None
        and expected_revenue
        and latest.revenue < expected_revenue
    ):
        top_issue = "Revenue is below the current break-even target."
    elif latest and latest.complaints and latest.complaints > 0:
        top_issue = "Customer complaints need review before scaling acquisition."
    elif latest and latest.stockouts and latest.stockouts > 0:
        top_issue = "Stockouts may be limiting sales or damaging customer trust."

    financial_warning = None
    if latest and latest.expenses is not None and latest.revenue is not None:
        if latest.expenses > latest.revenue:
            financial_warning = "Expenses exceeded revenue for the latest period."
    if variance is not None and variance < -0.2:
        financial_warning = "Revenue is more than 20 percent below the current target."

    return {
        "analysis_id": str(result.get("analysis_id") or analysis.get("analysis_id")),
        "performance_summary": {
            "entries_reviewed": len(entries),
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "total_customers": round(total_customers, 2),
            "latest_revenue_variance_vs_target": variance,
        },
        "top_issue": top_issue,
        "top_opportunity": _top_performance_opportunity(latest),
        "financial_warning": financial_warning,
        "customer_insight": _customer_insight(latest),
        "inventory_insight": _inventory_insight(latest),
        "recommended_experiments": [
            "Change one price, offer, or channel at a time and measure the result for one week.",
            "Ask five recent customers why they chose the business and what almost stopped them.",
            "Compare actual supplier delays and stockouts against the procurement plan.",
        ],
        "next_week_priorities": [
            "Update revenue, customers, expenses, and stockouts for the next period.",
            "Verify the assumption with the largest negative variance.",
            "Choose one measurable action with an owner and due date.",
        ],
    }


def _profile_key(payload: BusinessAnalysisRequest) -> str:
    text = " ".join(
        [
            payload.business_idea or "",
            payload.business_category or "",
            " ".join(payload.priorities),
        ]
    ).lower()
    if any(word in text for word in ("mobile", "phone", "screen", "battery")):
        return "mobile"
    if any(word in text for word in ("cycle", "bicycle", "bike repair", "e-bike")):
        return "cycle"
    if any(word in text for word in ("cafe", "restaurant", "bakery", "food", "coffee")):
        return "cafe"
    if any(word in text for word in ("saas", "software", "ai", "app", "platform", "fintech")):
        return "technology"
    if any(word in text for word in ("store", "shop", "grocery", "clothing", "electronics")):
        return "retail"
    return "service"


def _business_idea(payload: BusinessAnalysisRequest) -> str:
    if payload.business_idea and payload.business_idea.strip():
        return payload.business_idea.strip()
    return f"Find business opportunities near {_location_label(payload)}"


def _location_label(payload: BusinessAnalysisRequest) -> str:
    location = payload.location
    parts = [
        location.address,
        location.market,
        location.locality,
        location.city,
        location.state,
        location.country,
    ]
    label = ", ".join(part.strip() for part in parts if part and part.strip())
    if label:
        return label
    if location.latitude is not None and location.longitude is not None:
        return f"{location.latitude:.5f}, {location.longitude:.5f}"
    return "Selected location"


def _provider_label(payload: BusinessAnalysisRequest, settings: Any | None) -> str:
    provider = getattr(settings, "maps_provider", "none") if settings else "none"
    if payload.data_mode == "demo":
        return DEMO_NOTICE
    if payload.data_mode == "manual":
        return "Manual-data mode"
    return f"Live-provider mode ({provider})"


def _provider_warnings(payload: BusinessAnalysisRequest, settings: Any | None) -> list[str]:
    warnings: list[str] = []
    if payload.data_mode != "live":
        return warnings

    maps_configured = bool(getattr(settings, "maps_api_key", "")) if settings else False
    places_configured = bool(getattr(settings, "places_api_key", "")) if settings else False
    if not maps_configured and not places_configured:
        warnings.append(
            "No live location provider is configured. Continue with demo mode or add "
            "information manually."
        )
    elif not places_configured:
        warnings.append(
            "Live map credentials are present, but place-search credentials are missing. "
            "Competitor and supplier discovery may be unavailable."
        )
    return warnings


def _base_evidence(
    payload: BusinessAnalysisRequest,
    retrieved_at: datetime,
) -> list[dict[str, Any]]:
    evidence = [
        _evidence(
            claim=f"Business idea entered as '{_business_idea(payload)}'.",
            source_name="User provided",
            source_type="user_input",
            retrieved_at=retrieved_at,
            confidence="high",
            verification_status="user_provided",
            value=_business_idea(payload),
            tags=["business", "intake"],
        ),
        _evidence(
            claim=f"Selected business location is {_location_label(payload)}.",
            source_name="User provided",
            source_type=f"location_{payload.location.source}",
            retrieved_at=retrieved_at,
            confidence="moderate" if payload.location.source == "browser_permission" else "high",
            verification_status="user_provided",
            value={
                "country": payload.location.country,
                "state": payload.location.state,
                "city": payload.location.city,
                "locality": payload.location.locality,
                "market": payload.location.market,
                "address": payload.location.address,
                "latitude": payload.location.latitude,
                "longitude": payload.location.longitude,
                "radius_km": payload.location.radius_km,
            },
            tags=["location"],
        ),
    ]
    if payload.budget is not None:
        evidence.append(
            _evidence(
                claim=f"Approximate budget entered as {payload.budget:,.2f}.",
                source_name="User provided",
                source_type="user_input",
                retrieved_at=retrieved_at,
                confidence="high",
                verification_status="user_provided",
                value=payload.budget,
                tags=["finance", "budget"],
            )
        )
    if payload.data_mode == "demo":
        evidence.append(
            _evidence(
                claim="Benchmark scaffolding is active and is not live local evidence.",
                source_name="BoardroomAI demo benchmark",
                source_type="configurable_benchmark",
                retrieved_at=retrieved_at,
                confidence="low",
                verification_status="demo_not_live",
                value=DEMO_NOTICE,
                tags=["demo", "benchmark"],
            )
        )
    return evidence


def _competitors(
    manual_competitors: list[ManualCompetitorInput],
    payload: BusinessAnalysisRequest,
    retrieved_at: datetime,
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    competitors = []
    for competitor in manual_competitors:
        classification = _competitor_classification(competitor, payload)
        record = {
            "name": competitor.name,
            "category": competitor.category or "Not specified",
            "classification": classification,
            "approximate_location": competitor.location_label,
            "distance_km": competitor.distance_km,
            "rating": competitor.rating,
            "review_count": competitor.review_count,
            "website": competitor.website,
            "public_services": competitor.services,
            "review_themes": [],
            "common_complaints": [],
            "common_praise": [],
            "source": "User provided",
            "retrieval_timestamp": retrieved_at.isoformat(),
            "verification_status": "user_provided",
            "notes": competitor.notes,
        }
        competitors.append(record)
        evidence.append(
            _evidence(
                claim=f"Manual competitor entered: {competitor.name}.",
                source_name="User provided",
                source_type="manual_competitor",
                retrieved_at=retrieved_at,
                confidence="moderate",
                verification_status="user_provided",
                value=record,
                tags=["competitor", classification],
            )
        )
    return competitors


def _competitor_classification(
    competitor: ManualCompetitorInput,
    payload: BusinessAnalysisRequest,
) -> str:
    text = f"{competitor.name} {competitor.category or ''}".lower()
    idea = _business_idea(payload).lower()
    direct_words = set(idea.replace("-", " ").split())
    if any(word in text for word in direct_words if len(word) >= 5):
        return "direct_competitor"
    if any(word in text for word in ("wholesale", "supplier", "distributor", "dealer")):
        return "supplier"
    if competitor.category:
        return "indirect_competitor"
    return "unknown_relevance"


def _suppliers(
    manual_suppliers: list[ManualSupplierInput],
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
    retrieved_at: datetime,
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    suppliers = []
    for supplier in manual_suppliers:
        record = {
            "name": supplier.name,
            "category": supplier.category or "Not specified",
            "location": supplier.location_label,
            "distance_km": supplier.distance_km,
            "brands": "Not publicly available - contact the supplier for confirmation.",
            "product_categories": supplier.product_categories,
            "delivery_availability": (
                supplier.delivery_available
                if supplier.delivery_available is not None
                else "Not publicly available - contact the supplier for confirmation."
            ),
            "minimum_order_quantity": supplier.minimum_order_quantity
            or "Not publicly available - contact the supplier for confirmation.",
            "public_pricing": supplier.public_pricing
            or "Not publicly available - request quotations.",
            "quotation_amount": supplier.quotation_amount,
            "contact_status": supplier.contact_status,
            "is_preferred": supplier.is_preferred,
            "source": "User provided",
            "retrieval_timestamp": retrieved_at.isoformat(),
            "verification_status": "user_provided",
            "notes": supplier.notes,
        }
        suppliers.append(record)
        evidence.append(
            _evidence(
                claim=f"Manual supplier entered: {supplier.name}.",
                source_name="User provided",
                source_type="manual_supplier",
                retrieved_at=retrieved_at,
                confidence="moderate",
                verification_status="user_provided",
                value=record,
                tags=["supplier"],
            )
        )

    if not suppliers:
        evidence.append(
            _evidence(
                claim="Required supplier categories were inferred from the business category.",
                source_name="BoardroomAI category profile",
                source_type="configurable_benchmark",
                retrieved_at=retrieved_at,
                confidence="low",
                verification_status="assumption",
                value=profile["supplier_categories"],
                tags=["supplier", "procurement", "benchmark"],
            )
        )
    return suppliers


def _opportunity_score(
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
    competitors: list[dict[str, Any]],
    suppliers: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    direct_competitors = [
        item for item in competitors if item["classification"] == "direct_competitor"
    ]
    unknown_competition = not competitors
    if unknown_competition:
        competition_points = 10
        competition_reason = "No verified competitor data was provided or retrieved."
    elif len(direct_competitors) == 0:
        competition_points = 14
        competition_reason = (
            "No direct competitors were entered, but absence may mean missing data."
        )
    elif len(direct_competitors) <= 3:
        competition_points = 19
        competition_reason = "A manageable number of direct competitors was entered."
    elif len(direct_competitors) <= 8:
        competition_points = 14
        competition_reason = "The entered area appears competitive and needs differentiation."
    else:
        competition_points = 8
        competition_reason = "High manual competitor count creates pressure on location and offer."

    demand_points = 9
    demand_reasons = []
    if payload.target_customers:
        demand_points += 5
        demand_reasons.append("Target customers were described by the user.")
    if payload.customer_observations:
        demand_points += min(6, len(payload.customer_observations) * 2)
        demand_reasons.append("Customer observations were entered.")
    if payload.customer_interviews:
        demand_points += min(5, len(payload.customer_interviews) * 2)
        demand_reasons.append("Customer interviews were entered.")
    demand_points = min(25, demand_points)

    accessibility_points = 8
    if payload.location.address or payload.location.market or payload.location.locality:
        accessibility_points += 4
    if payload.location.latitude is not None and payload.location.longitude is not None:
        accessibility_points += 3
    if payload.shop_size_sqft:
        accessibility_points += 2
    accessibility_points = min(20, accessibility_points)

    supplier_points = 4
    if suppliers:
        nearby = [supplier for supplier in suppliers if _num(supplier.get("distance_km")) <= 15]
        supplier_points += min(8, len(suppliers) * 2)
        supplier_points += min(3, len(nearby))
    supplier_points = min(15, supplier_points)

    cost_points = _cost_feasibility_points(payload, profile)
    evidence_points = _evidence_points(evidence, payload)
    total = competition_points + demand_points + accessibility_points + supplier_points
    total += cost_points + evidence_points

    return {
        "label": f"Opportunity Score: {total}/100",
        "score": total,
        "meaning": (
            "This is an explainable planning score, not a probability of success or a guarantee."
        ),
        "breakdown": [
            {
                "factor": "Competition opportunity",
                "points": competition_points,
                "max_points": 25,
                "weight": 25,
                "reason": competition_reason,
                "evidence_used": [
                    "manual_competitors" if competitors else "missing_competitor_data"
                ],
            },
            {
                "factor": "Demand signals",
                "points": demand_points,
                "max_points": 25,
                "weight": 25,
                "reason": "; ".join(demand_reasons)
                if demand_reasons
                else "Demand remains mostly unverified.",
                "evidence_used": ["target_customers", "observations", "interviews"],
            },
            {
                "factor": "Accessibility",
                "points": accessibility_points,
                "max_points": 20,
                "weight": 20,
                "reason": (
                    "Based only on selected location detail and user-entered property context."
                ),
                "evidence_used": ["location"],
            },
            {
                "factor": "Supplier access",
                "points": supplier_points,
                "max_points": 15,
                "weight": 15,
                "reason": (
                    "Manual supplier entries improve confidence."
                    if suppliers
                    else "No verified suppliers were found within the current data."
                ),
                "evidence_used": ["manual_suppliers" if suppliers else "supplier_categories"],
            },
            {
                "factor": "Cost feasibility",
                "points": cost_points,
                "max_points": 10,
                "weight": 10,
                "reason": "Compares budget against editable setup-cost assumptions.",
                "evidence_used": ["budget", "financial_assumptions"],
            },
            {
                "factor": "Evidence quality",
                "points": evidence_points,
                "max_points": 5,
                "weight": 5,
                "reason": (
                    "Higher when the analysis has user-provided observations and less "
                    "demo-only data."
                ),
                "evidence_used": ["evidence_records"],
            },
        ],
        "advantages": _score_advantages(total, payload, suppliers),
        "disadvantages": _score_disadvantages(payload, competitors, suppliers),
        "unknowns": _score_unknowns(payload, competitors, suppliers),
        "evidence_confidence": _evidence_confidence(evidence, payload),
    }


def _cost_feasibility_points(payload: BusinessAnalysisRequest, profile: dict[str, Any]) -> int:
    if payload.budget is None:
        return 3
    setup_ranges = profile["setup_ranges"]
    benchmark_min = (
        setup_ranges["equipment"][0]
        + setup_ranges["inventory"][0]
        + setup_ranges["renovation"][0]
        + setup_ranges["licenses"][0]
        + setup_ranges["marketing"][0]
    )
    if payload.budget >= benchmark_min * 1.5:
        return 9
    if payload.budget >= benchmark_min:
        return 7
    if payload.budget >= benchmark_min * 0.65:
        return 5
    return 2


def _evidence_points(evidence: list[dict[str, Any]], payload: BusinessAnalysisRequest) -> int:
    user_evidence = [item for item in evidence if item["source_type"].startswith("manual")]
    user_evidence += [item for item in evidence if item["source_type"] == "user_input"]
    points = 1
    if len(user_evidence) >= 4:
        points += 2
    elif len(user_evidence) >= 2:
        points += 1
    if payload.customer_interviews or payload.customer_observations:
        points += 1
    if payload.data_mode != "demo":
        points += 1
    return min(5, points)


def _evidence_confidence(
    evidence: list[dict[str, Any]],
    payload: BusinessAnalysisRequest,
) -> str:
    if (
        payload.data_mode == "demo"
        and not payload.manual_competitors
        and not payload.manual_suppliers
    ):
        return "Low"
    high_or_moderate = [item for item in evidence if item["confidence"] in {"high", "moderate"}]
    if len(high_or_moderate) >= 8 and payload.customer_interviews:
        return "High"
    if len(high_or_moderate) >= 4:
        return "Moderate"
    return "Low"


def _score_advantages(
    total: int,
    payload: BusinessAnalysisRequest,
    suppliers: list[dict[str, Any]],
) -> list[str]:
    advantages = []
    if payload.budget is not None:
        advantages.append("Budget is available for setup-cost testing against assumptions.")
    if payload.target_customers:
        advantages.append("Target customer group is named, which makes validation easier.")
    if suppliers:
        advantages.append("At least one supplier was entered for procurement follow-up.")
    if total >= 70:
        advantages.append("The current inputs produce a comparatively strong provisional score.")
    return advantages or ["The concept can still be evaluated if the user adds local evidence."]


def _score_disadvantages(
    payload: BusinessAnalysisRequest,
    competitors: list[dict[str, Any]],
    suppliers: list[dict[str, Any]],
) -> list[str]:
    disadvantages = []
    if not competitors:
        disadvantages.append("Competitor landscape is unknown; do not infer low competition.")
    if not suppliers:
        disadvantages.append("Supplier availability and prices are not verified.")
    if payload.location.latitude is None or payload.location.longitude is None:
        disadvantages.append("No coordinates are available for distance-based checks.")
    if not payload.customer_observations and not payload.customer_interviews:
        disadvantages.append("Customer demand is not validated by observations or interviews.")
    return disadvantages


def _score_unknowns(
    payload: BusinessAnalysisRequest,
    competitors: list[dict[str, Any]],
    suppliers: list[dict[str, Any]],
) -> list[str]:
    unknowns = []
    if not competitors:
        unknowns.append("Number and strength of nearby competitors")
    if not suppliers:
        unknowns.append("Supplier names, delivery terms, MOQ, and verified pricing")
    if payload.financial_assumptions.expected_rent is None:
        unknowns.append("Rent and deposit at the exact property")
    if payload.location.source == "browser_permission":
        unknowns.append("Whether the approximate device location matches the business site")
    return unknowns


def _candidate_areas(
    payload: BusinessAnalysisRequest,
    selected_score: dict[str, Any],
    suppliers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    areas = [
        {
            "name": _location_label(payload),
            "type": "selected_area",
            "opportunity_score": selected_score["score"],
            "evidence_confidence": selected_score["evidence_confidence"],
            "advantages": selected_score["advantages"],
            "disadvantages": selected_score["disadvantages"],
            "unknowns": selected_score["unknowns"],
            "recommendation": "Use as the baseline area for comparison.",
        }
    ]
    for candidate in payload.candidate_locations:
        score = selected_score["score"]
        reasons = []
        if candidate.expected_rent is not None and payload.financial_assumptions.expected_rent:
            if candidate.expected_rent < payload.financial_assumptions.expected_rent:
                score += 4
                reasons.append("Entered rent is lower than the selected area's rent assumption.")
            elif candidate.expected_rent > payload.financial_assumptions.expected_rent:
                score -= 4
                reasons.append("Entered rent is higher than the selected area's rent assumption.")
        if suppliers:
            score += 1
            reasons.append("Supplier comparison requires route or distance verification.")
        score = max(0, min(100, score))
        areas.append(
            {
                "name": candidate.name,
                "type": "candidate_area",
                "opportunity_score": score,
                "evidence_confidence": "Low",
                "advantages": reasons or ["Candidate area added by the user for comparison."],
                "disadvantages": ["Competitor, demand, and accessibility data must be verified."],
                "unknowns": [
                    "Competitor density",
                    "Demand signals",
                    "Supplier distance",
                    "Real rent and property conditions",
                ],
                "recommendation": "Visit and collect comparable evidence before choosing.",
            }
        )
    return areas


def _properties(
    payload: BusinessAnalysisRequest,
    suppliers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    properties = []
    for property_input in payload.properties:
        score = 35
        strengths = []
        weaknesses = []
        if property_input.rent is not None:
            score += 10
            strengths.append("Rent is entered, so rent burden can be tested.")
        else:
            weaknesses.append("Rent is missing.")
        if property_input.shop_size_sqft:
            score += 8
            strengths.append("Shop size is entered.")
        else:
            weaknesses.append("Shop size is missing.")
        if property_input.visibility:
            score += 5
            strengths.append("Visibility observation is entered by the user.")
        if property_input.parking:
            score += 4
            strengths.append("Parking observation is entered by the user.")
        if suppliers:
            score += 3
            strengths.append("Supplier list exists for logistics follow-up.")
        score = max(0, min(100, score))
        properties.append(
            {
                "name": property_input.name,
                "address": property_input.address,
                "property_suitability_score": score,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "financial_impact": _property_financial_impact(property_input),
                "customer_impact": (
                    "Requires physical verification of visibility, frontage, parking, "
                    "and customer access."
                ),
                "operational_impact": (
                    "Supplier distance and storage suitability require verification before signing."
                ),
                "evidence_confidence": "Low" if weaknesses else "Moderate",
                "missing_information": weaknesses,
                "landlord_questions": [
                    "What expenses are included in rent?",
                    "What is the deposit refund condition?",
                    "Are signage, renovation, and business activity allowed?",
                    "What is the rent increase schedule?",
                ],
                "physical_verification_checklist": [
                    "Observe customer traffic at opening, lunch, evening, and weekend periods.",
                    "Check parking and loading access at busy times.",
                    "Measure usable frontage and interior layout.",
                    "Verify nearby competitors and complementary businesses.",
                ],
            }
        )
    return properties


def _property_financial_impact(property_input: Any) -> dict[str, Any]:
    rent = _num(property_input.rent)
    deposit = _num(property_input.deposit)
    return {
        "monthly_rent": _origin_value(
            rent if rent else None, "user_supplied" if rent else "unknown"
        ),
        "deposit": _origin_value(
            deposit if deposit else None, "user_supplied" if deposit else "unknown"
        ),
        "notes": "Rent burden should be compared with break-even revenue before signing.",
    }


def _financials(
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
) -> dict[str, Any]:
    assumptions = payload.financial_assumptions
    setup_ranges = profile["setup_ranges"]
    rent = assumptions.expected_rent
    deposit = assumptions.security_deposit
    if deposit is None and rent is not None:
        deposit = rent
        deposit_origin = "derived_calculation"
    else:
        deposit_origin = "user_supplied" if deposit is not None else "unknown"

    components = {
        "security_deposit": _single_component(deposit, deposit_origin),
        "renovation": _range_component(
            assumptions.renovation_cost,
            setup_ranges["renovation"],
            "configurable_benchmark",
        ),
        "equipment": _range_component(
            assumptions.equipment_budget,
            setup_ranges["equipment"],
            "configurable_benchmark",
        ),
        "opening_inventory": _range_component(
            assumptions.opening_inventory_budget,
            setup_ranges["inventory"],
            "configurable_benchmark",
        ),
        "licenses": _range_component(
            assumptions.license_budget,
            setup_ranges["licenses"],
            "configurable_benchmark",
        ),
        "launch_marketing": _range_component(
            assumptions.marketing_budget,
            setup_ranges["marketing"],
            "configurable_benchmark",
        ),
    }
    low, high = _sum_component_ranges(components)
    contingency_low = round(low * 0.1, 2)
    contingency_high = round(high * 0.15, 2)
    setup_low = round(low + contingency_low, 2)
    setup_high = round(high + contingency_high, 2)

    monthly_fixed = {
        "rent": _single_component(rent, "user_supplied" if rent is not None else "unknown"),
        "staff": _single_component(
            assumptions.monthly_staff_cost,
            "user_supplied" if assumptions.monthly_staff_cost is not None else "assumption",
            fallback=0,
        ),
        "utilities": _range_component(
            assumptions.utilities_monthly,
            setup_ranges["utilities_monthly"],
            "configurable_benchmark",
        ),
        "logistics": _single_component(
            assumptions.logistics_monthly,
            "user_supplied" if assumptions.logistics_monthly is not None else "assumption",
            fallback=0,
        ),
        "owner_income": _single_component(
            assumptions.desired_owner_income,
            "user_supplied" if assumptions.desired_owner_income is not None else "assumption",
            fallback=0,
        ),
    }
    fixed_low, fixed_high = _sum_component_ranges(monthly_fixed)
    working_capital = (
        round(fixed_low * assumptions.working_capital_months, 2),
        round(fixed_high * assumptions.working_capital_months, 2),
    )
    total_startup = (
        round(setup_low + working_capital[0], 2),
        round(setup_high + working_capital[1], 2),
    )

    scenario_base = _scenario(total_startup, fixed_low, fixed_high, 1.0)
    return {
        "currency_note": (
            "Amounts are in the same currency as the user's inputs. Benchmark ranges "
            "are configurable planning assumptions and should be replaced with quotations."
        ),
        "setup_cost": {
            "components": components,
            "contingency": {
                "low": contingency_low,
                "high": contingency_high,
                "origin": "derived_calculation",
            },
            "working_capital": {
                "low": working_capital[0],
                "high": working_capital[1],
                "months": assumptions.working_capital_months,
                "origin": "derived_calculation",
            },
            "estimated_total_range": {"low": total_startup[0], "high": total_startup[1]},
            "budget_gap": _budget_gap(payload.budget, total_startup),
        },
        "monthly_costs": {
            "components": monthly_fixed,
            "estimated_fixed_cost_range": {
                "low": round(fixed_low, 2),
                "high": round(fixed_high, 2),
            },
        },
        "unit_economics": {
            "average_transaction_value": _origin_value(
                assumptions.average_transaction_value or profile["average_transaction_value"],
                "user_supplied"
                if assumptions.average_transaction_value is not None
                else "configurable_benchmark",
            ),
            "gross_margin_percent": _origin_value(
                assumptions.gross_margin_percent or profile["gross_margin_percent"],
                "user_supplied"
                if assumptions.gross_margin_percent is not None
                else "configurable_benchmark",
            ),
        },
        "scenarios": {
            "conservative": _scenario(total_startup, fixed_low, fixed_high, 1.2),
            "base": scenario_base,
            "optimistic": _scenario(total_startup, fixed_low, fixed_high, 0.85),
        },
        "calculation_warnings": [
            "Rent is unknown, so break-even is incomplete."
            if rent is None
            else "Rent was included from user input.",
            "Replace benchmark costs with supplier quotations before committing spend.",
        ],
    }


def _single_component(
    value: float | None,
    origin: str,
    fallback: float | None = None,
) -> dict[str, Any]:
    amount = value if value is not None else fallback
    return {
        "amount": amount,
        "low": amount,
        "high": amount,
        "origin": origin,
        "confidence": "high" if origin == "user_supplied" else "low",
    }


def _range_component(
    user_value: float | None,
    benchmark_range: tuple[float, float],
    benchmark_origin: str,
) -> dict[str, Any]:
    if user_value is not None:
        return {
            "amount": user_value,
            "low": user_value,
            "high": user_value,
            "origin": "user_supplied",
            "confidence": "high",
        }
    return {
        "amount": None,
        "low": benchmark_range[0],
        "high": benchmark_range[1],
        "origin": benchmark_origin,
        "confidence": "low",
    }


def _sum_component_ranges(components: dict[str, dict[str, Any]]) -> tuple[float, float]:
    low = sum(_num(component.get("low")) for component in components.values())
    high = sum(_num(component.get("high")) for component in components.values())
    return round(low, 2), round(high, 2)


def _budget_gap(budget: float | None, total_startup: tuple[float, float]) -> dict[str, Any]:
    if budget is None:
        return {"status": "unknown", "message": "Budget was not provided."}
    if budget >= total_startup[1]:
        return {"status": "covered", "surplus_against_high": round(budget - total_startup[1], 2)}
    if budget >= total_startup[0]:
        return {
            "status": "tight",
            "message": "Budget covers the low estimate but not the high estimate.",
            "gap_against_high": round(total_startup[1] - budget, 2),
        }
    return {"status": "gap", "gap_against_low": round(total_startup[0] - budget, 2)}


def _scenario(
    total_startup: tuple[float, float],
    fixed_low: float,
    fixed_high: float,
    multiplier: float,
) -> dict[str, Any]:
    return {
        "setup_cost_low": round(total_startup[0] * multiplier, 2),
        "setup_cost_high": round(total_startup[1] * multiplier, 2),
        "monthly_fixed_low": round(fixed_low * multiplier, 2),
        "monthly_fixed_high": round(fixed_high * multiplier, 2),
        "changed_assumption": f"{round(multiplier * 100)} percent of base assumptions",
    }


def _daily_sales(
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
    financials: dict[str, Any],
) -> dict[str, Any]:
    assumptions = payload.financial_assumptions
    unit = financials["unit_economics"]
    average_transaction = _num(unit["average_transaction_value"]["value"])
    gross_margin = _num(unit["gross_margin_percent"]["value"]) / 100
    fixed_costs = financials["monthly_costs"]["estimated_fixed_cost_range"]
    required_gross_profit = fixed_costs["high"]
    required_monthly_revenue = required_gross_profit / gross_margin if gross_margin else 0
    working_days = assumptions.working_days_per_month
    daily_revenue = required_monthly_revenue / working_days
    daily_transactions = daily_revenue / average_transaction if average_transaction else 0
    return {
        "plain_language": (
            f"To cover the current assumptions, the business may require approximately "
            f"{ceil(daily_transactions)} customer transactions per working day."
        ),
        "monthly_targets": {
            "required_monthly_revenue": round(required_monthly_revenue, 2),
            "required_gross_profit": round(required_gross_profit, 2),
            "working_days_per_month": working_days,
            "average_transaction_value": average_transaction,
            "gross_margin_percent": round(gross_margin * 100, 2),
        },
        "weekly_targets": {
            "required_weekly_revenue": round(required_monthly_revenue / 4.33, 2),
            "required_weekly_transactions": ceil(daily_transactions * working_days / 4.33),
        },
        "daily_targets": {
            "required_daily_revenue": round(daily_revenue, 2),
            "required_daily_transactions": ceil(daily_transactions),
        },
        "calculation": (
            "Required monthly revenue = fixed monthly costs / gross margin. "
            "Required daily transactions = monthly revenue / working days / average "
            "transaction value."
        ),
        "assumption_labels": {
            "average_transaction_value": unit["average_transaction_value"]["origin"],
            "gross_margin_percent": unit["gross_margin_percent"]["origin"],
            "fixed_costs": "derived from user inputs and configurable benchmarks",
        },
        "stress_tests": [
            _stress_test(
                "Sales 20 percent below plan", required_monthly_revenue * 0.8, required_gross_profit
            ),
            _stress_test(
                "Sales 40 percent below plan", required_monthly_revenue * 0.6, required_gross_profit
            ),
            _stress_test(
                "Supplier prices increase", required_monthly_revenue, required_gross_profit * 1.1
            ),
            _stress_test(
                "Average transaction value falls",
                required_monthly_revenue * 0.9,
                required_gross_profit,
            ),
        ],
    }


def _stress_test(name: str, revenue: float, required_gross_profit: float) -> dict[str, Any]:
    margin = revenue - required_gross_profit
    return {
        "scenario": name,
        "estimated_revenue": round(revenue, 2),
        "gap_or_buffer": round(margin, 2),
        "interpretation": "Needs action" if margin < 0 else "Has buffer under this assumption",
    }


def _procurement_plan(
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
    suppliers: list[dict[str, Any]],
) -> dict[str, Any]:
    preferred_supplier = next((item for item in suppliers if item.get("is_preferred")), None)
    backup_supplier = next(
        (
            item
            for item in suppliers
            if preferred_supplier and item["name"] != preferred_supplier["name"]
        ),
        None,
    )
    items = []
    for name, bucket, quantity_range, cost_range in profile["inventory_items"]:
        items.append(
            {
                "item": name,
                "category": bucket,
                "suggested_quantity_range": {
                    "low": quantity_range[0],
                    "high": quantity_range[1],
                    "origin": "configurable_benchmark",
                },
                "editable_quantity": quantity_range[0],
                "estimated_cost_range": {
                    "low": cost_range[0],
                    "high": cost_range[1],
                    "origin": "configurable_benchmark",
                    "confidence": "low",
                },
                "reorder_level": "Set after first two weeks of actual demand.",
                "preferred_supplier": preferred_supplier["name"] if preferred_supplier else None,
                "backup_supplier": backup_supplier["name"] if backup_supplier else None,
                "confidence": "low",
            }
        )
    supplier_risk = (
        "High" if len(suppliers) <= 1 else "Moderate" if len(suppliers) <= 3 else "Lower"
    )
    return {
        "supplier_categories_needed": profile["supplier_categories"],
        "opening_inventory": items,
        "supplier_summary": {
            "verified_supplier_count": len(suppliers),
            "nearest_supplier": _nearest_supplier(suppliers),
            "backup_supplier": backup_supplier["name"] if backup_supplier else None,
            "supply_concentration_risk": supplier_risk,
            "procurement_distance": _procurement_distance(suppliers),
        },
        "exports_supported": ["procurement_checklist", "supplier_comparison", "opening_inventory"],
        "notes": [
            "Quantities and costs are editable planning assumptions.",
            "Request quotations before purchasing inventory.",
        ],
    }


def _nearest_supplier(suppliers: list[dict[str, Any]]) -> str | None:
    with_distance = [supplier for supplier in suppliers if supplier.get("distance_km") is not None]
    if not with_distance:
        return suppliers[0]["name"] if suppliers else None
    return min(with_distance, key=lambda item: _num(item.get("distance_km")))["name"]


def _procurement_distance(suppliers: list[dict[str, Any]]) -> dict[str, Any]:
    distances = [
        _num(supplier.get("distance_km"))
        for supplier in suppliers
        if supplier.get("distance_km") is not None
    ]
    if not distances:
        return {"status": "unknown", "message": "Supplier distances are not verified."}
    return {
        "nearest_km": round(min(distances), 2),
        "farthest_km": round(max(distances), 2),
        "average_km": round(sum(distances) / len(distances), 2),
    }


def _customer_segments(
    payload: BusinessAnalysisRequest,
    retrieved_at: datetime,
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    segments = []
    if payload.target_customers:
        segments.append(
            {
                "segment": payload.target_customers,
                "need": "User-defined target customers need direct validation.",
                "purchase_reason": "Convenience, trust, price, or availability must be verified.",
                "relevant_products": [_business_idea(payload)],
                "relevant_services": payload.priorities,
                "price_assumptions": "Unknown until interviews or test sales.",
                "convenience_expectations": "Ask during validation interviews.",
                "acquisition_channel": (
                    "Local search, signage, referrals, or direct outreach depending on "
                    "category."
                ),
                "evidence": "User provided target customer description.",
                "confidence": "Low",
                "validation_question": (
                    "What problem would make you choose this business this month?"
                ),
            }
        )
    else:
        segments.append(
            {
                "segment": "Local customers near the selected area",
                "need": "Unknown; identify through observation and interviews.",
                "purchase_reason": "Unknown",
                "relevant_products": [_business_idea(payload)],
                "relevant_services": payload.priorities,
                "price_assumptions": "Unknown",
                "convenience_expectations": "Unknown",
                "acquisition_channel": "To be validated",
                "evidence": "Assumption",
                "confidence": "Low",
                "validation_question": "Who has the most urgent need in this location?",
            }
        )
    for interview in payload.customer_interviews:
        evidence.append(
            _evidence(
                claim=f"Customer interview entered for {interview.customer_segment}.",
                source_name="User provided",
                source_type="customer_interview",
                retrieved_at=retrieved_at,
                confidence="moderate",
                verification_status="user_provided",
                value=interview.model_dump(mode="json"),
                tags=["customer", "interview"],
            )
        )
        segments.append(
            {
                "segment": interview.customer_segment,
                "need": interview.need,
                "purchase_reason": "User interview input",
                "relevant_products": [_business_idea(payload)],
                "relevant_services": payload.priorities,
                "price_assumptions": interview.willingness_to_pay or "Unknown",
                "convenience_expectations": interview.notes or "Unknown",
                "acquisition_channel": "Ask during follow-up interview",
                "evidence": "User-entered customer interview",
                "confidence": "Moderate",
                "validation_question": (
                    "Would this customer pay now, wait, or choose an alternative?"
                ),
            }
        )
    return segments


def _validation_plan(
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
    score: dict[str, Any],
) -> list[dict[str, Any]]:
    location_label = _location_label(payload)
    return [
        {
            "task": (
                f"Observe {location_label} for seven days at opening, lunch, evening, "
                "and weekend periods."
            ),
            "owner": "User",
            "due_date": "Before rent or major purchase",
            "cost": "Time only unless travel is required",
            "expected_evidence": (
                "Relevant customer traffic, competitor visits, parking, and customer types."
            ),
            "result": None,
            "outcome": None,
            "effect_on_confidence": (
                "Raises demand and accessibility confidence if recorded consistently."
            ),
        },
        {
            "task": (
                "Visit or call at least five relevant competitors and document services, "
                "prices, waits, and gaps."
            ),
            "owner": "User",
            "due_date": "Before final location decision",
            "cost": "Low",
            "expected_evidence": (
                "Competitor service list, pricing visibility, wait times, and customer "
                "pain points."
            ),
            "result": None,
            "outcome": None,
            "effect_on_confidence": "Improves competition and differentiation evidence.",
        },
        {
            "task": "Request three supplier quotations for essential opening inventory.",
            "owner": "User",
            "due_date": "Before procurement",
            "cost": "Low",
            "expected_evidence": (
                "Price, MOQ, delivery terms, payment terms, and backup supplier options."
            ),
            "result": None,
            "outcome": None,
            "effect_on_confidence": "Improves procurement and setup-cost confidence.",
        },
        {
            "task": "Interview ten target customers using the generated questions.",
            "owner": "User",
            "due_date": "Before launch",
            "cost": "Low",
            "expected_evidence": (
                "Need, purchase trigger, current alternative, price tolerance, and trust "
                "concerns."
            ),
            "result": None,
            "outcome": None,
            "effect_on_confidence": (
                "Updates demand, customer segments, and recommendation confidence."
            ),
        },
        {
            "task": "Run a small validation offer before committing full inventory.",
            "owner": "User",
            "due_date": "Before full launch",
            "cost": "Configurable",
            "expected_evidence": (
                "Leads, inquiries, trial orders, conversion rate, and customer objections."
            ),
            "result": None,
            "outcome": None,
            "effect_on_confidence": (
                "Validates willingness to buy without assuming online data is enough."
            ),
        },
    ]


def _missing_information(
    payload: BusinessAnalysisRequest,
    competitors: list[dict[str, Any]],
    suppliers: list[dict[str, Any]],
    financials: dict[str, Any],
) -> list[str]:
    missing = []
    if not competitors:
        missing.append("Verified nearby competitors and service gaps")
    if not suppliers:
        missing.append("Verified supplier names, quotations, delivery, MOQ, and backup supplier")
    if payload.financial_assumptions.expected_rent is None:
        missing.append("Exact rent and deposit")
    if not payload.customer_observations and not payload.customer_interviews:
        missing.append("Customer observations or interviews")
    if payload.location.latitude is None or payload.location.longitude is None:
        missing.append("Coordinates for distance calculations")
    if financials["setup_cost"]["budget_gap"]["status"] == "unknown":
        missing.append("Approximate budget")
    return missing


def _recommendation(
    payload: BusinessAnalysisRequest,
    score: dict[str, Any],
    financials: dict[str, Any],
    missing_information: list[str],
) -> dict[str, Any]:
    score_value = score["score"]
    if score_value >= 75 and len(missing_information) <= 3:
        label = "Proceed to validation"
        stance = "Promising, but verify before investing."
    elif score_value >= 55:
        label = "Proceed carefully"
        stance = "Worth exploring after key unknowns are resolved."
    else:
        label = "Do not commit yet"
        stance = "Collect stronger evidence before spending significant money."
    return {
        "label": label,
        "plain_language": stance,
        "business": _business_idea(payload),
        "selected_area": _location_label(payload),
        "top_reasons": score["advantages"][:4],
        "main_risks": score["disadvantages"][:5],
        "financial_view": {
            "estimated_setup_cost_range": financials["setup_cost"]["estimated_total_range"],
            "budget_gap": financials["setup_cost"]["budget_gap"],
        },
        "important_claims": [
            {
                "claim": "The current recommendation is provisional.",
                "evidence": "It is based on user inputs, manual evidence, and labeled assumptions.",
                "assumptions": missing_information[:5],
                "counterargument": (
                    "The result may change materially after competitor, supplier, rent, "
                    "and demand checks."
                ),
                "confidence": score["evidence_confidence"],
                "recommended_action": (
                    "Complete validation tasks before signing a lease or buying inventory."
                ),
            }
        ],
    }


def _performance_tracking() -> dict[str, Any]:
    return {
        "enabled": True,
        "tracked_metrics": [
            "daily_sales",
            "monthly_sales",
            "customers",
            "transactions",
            "expenses",
            "inventory_purchases",
            "stockouts",
            "supplier_delays",
            "marketing_spending",
            "leads",
            "repeat_customers",
            "reviews",
            "complaints",
            "owner_observations",
        ],
        "message": (
            "Enter actual results to compare forecast versus actual without blaming "
            "the operator."
        ),
    }


def _board_brief(
    payload: BusinessAnalysisRequest,
    recommendation: dict[str, Any],
    competitors: list[dict[str, Any]],
    score: dict[str, Any],
    financials: dict[str, Any],
) -> dict[str, Any]:
    idea = _business_idea(payload)
    location_country = payload.location.country or "Unknown"
    if len(location_country) < 2:
        location_country = "Unknown"
    business_category = payload.business_category or "local business"
    startup_idea = (
        f"{idea} in {_location_label(payload)} with {score['label']} and "
        f"{recommendation['label']} recommendation"
    )
    return {
        "startup_idea": startup_idea[:800],
        "industry": business_category[:160],
        "country": location_country[:120],
        "budget": payload.budget
        or max(financials["setup_cost"]["estimated_total_range"]["low"], 1),
        "timeline_months": _timeline_months(payload.timeline),
        "competitors": [str(item["name"]) for item in competitors[:20]],
        "target_audience": payload.target_customers
        or f"local customers near {_location_label(payload)}",
        "funding_stage": "self-funded planning",
        "business_model": "local business / services",
    }


def _timeline_months(timeline: str | None) -> int:
    if not timeline:
        return 6
    digits = "".join(ch for ch in timeline if ch.isdigit())
    if not digits:
        return 6
    value = int(digits)
    if "year" in timeline.lower():
        value *= 12
    return max(1, min(120, value))


def _report(
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
    recommendation: dict[str, Any],
    score: dict[str, Any],
    competitors: list[dict[str, Any]],
    suppliers: list[dict[str, Any]],
    candidate_areas: list[dict[str, Any]],
    properties: list[dict[str, Any]],
    customer_segments: list[dict[str, Any]],
    procurement_plan: dict[str, Any],
    financials: dict[str, Any],
    daily_sales: dict[str, Any],
    validation_plan: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    missing_information: list[str],
    performance_tracking: dict[str, Any],
) -> dict[str, Any]:
    sections = {
        "executive_summary": {
            "recommendation": recommendation,
            "opportunity_score": score,
            "evidence_confidence": score["evidence_confidence"],
            "disclaimer": DISCLAIMER,
        },
        "business_concept": {
            "business": _business_idea(payload),
            "category": payload.business_category or profile["label"],
            "target_customers": payload.target_customers or "Unknown",
            "workflow_type": payload.workflow_type,
        },
        "location": {
            "selected_area": _location_label(payload),
            "location_source": payload.location.source,
            "radius_km": payload.location.radius_km,
            "map_markers_supported": [
                "selected_location",
                "competitors",
                "suppliers",
                "candidate_areas",
                "properties",
            ],
        },
        "alternatives": candidate_areas,
        "property_analysis": properties,
        "competitors": competitors,
        "customer_problems": _customer_problem_themes(payload),
        "customer_segments": customer_segments,
        "suppliers": suppliers,
        "procurement": procurement_plan,
        "inventory": procurement_plan["opening_inventory"],
        "financial_assumptions": financials,
        "daily_sales_target": daily_sales,
        "risk_matrix": _risk_matrix(score, missing_information),
        "evidence_quality": {
            "confidence": score["evidence_confidence"],
            "records": evidence,
            "missing_information": missing_information,
        },
        "validation_plan": validation_plan,
        "licensing_compliance": _compliance_checklist(payload),
        "performance_tracking": performance_tracking,
        "thirty_day_plan": _thirty_day_plan(validation_plan),
        "ninety_day_roadmap": _ninety_day_roadmap(),
    }
    return {
        "title": f"Business Decision Brief: {_business_idea(payload)}",
        "decision": recommendation["label"],
        "sections": sections,
    }


def _customer_problem_themes(payload: BusinessAnalysisRequest) -> dict[str, Any]:
    observations = payload.customer_observations
    return {
        "observations": observations,
        "themes": _themes_from_observations(observations),
        "limitations": [
            "Do not treat one review or observation as a broad market problem.",
            (
                "Configured live review providers are required for legally available "
                "public feedback analysis."
            ),
        ],
        "differentiation_ideas": [
            {
                "idea": "Publish clear price ranges where possible.",
                "customer_value": "Reduces uncertainty and trust friction.",
                "cost": "Low to moderate",
                "difficulty": "Moderate",
                "validation_method": (
                    "Ask customers whether transparent ranges change purchase intent."
                ),
            },
            {
                "idea": "Offer written service status updates.",
                "customer_value": "Improves communication and perceived reliability.",
                "cost": "Low",
                "difficulty": "Low",
                "validation_method": "Measure repeat visits and complaints after testing.",
            },
        ],
    }


def _themes_from_observations(observations: list[str]) -> list[dict[str, Any]]:
    themes = []
    keywords = {
        "price": "Pricing concern",
        "wait": "Waiting time",
        "quality": "Quality concern",
        "warranty": "Warranty concern",
        "stock": "Product availability",
        "delivery": "Delivery concern",
    }
    combined = " ".join(observations).lower()
    for keyword, label in keywords.items():
        count = combined.count(keyword)
        if count:
            themes.append(
                {
                    "theme": label,
                    "observation_count": count,
                    "confidence": "Low" if count == 1 else "Moderate",
                    "source": "User-entered observations",
                }
            )
    return themes


def _risk_matrix(score: dict[str, Any], missing_information: list[str]) -> list[dict[str, Any]]:
    risks = [
        ("Evidence risk", len(missing_information), "Complete validation tasks."),
        ("Competition risk", len(score["unknowns"]), "Verify competitors and differentiation."),
        (
            "Financial risk",
            5 if "Exact rent and deposit" in missing_information else 2,
            "Replace assumptions with quotes.",
        ),
    ]
    return [
        {
            "risk": name,
            "severity": "high" if value >= 5 else "medium" if value >= 3 else "low",
            "evidence": "Derived from missing information and score unknowns.",
            "mitigation": mitigation,
        }
        for name, value, mitigation in risks
    ]


def _compliance_checklist(payload: BusinessAnalysisRequest) -> list[dict[str, Any]]:
    checklist = [
        {
            "category": "Business registration",
            "status": "requires_professional_verification",
            "note": "Check official national, state, and local registration requirements.",
        },
        {
            "category": "Tax registration",
            "status": "requires_professional_verification",
            "note": (
                "Verify applicable tax registrations with an official source or "
                "professional advisor."
            ),
        },
        {
            "category": "Shop or local permissions",
            "status": "possible_requirement",
            "note": (
                "Physical locations may require municipal, signage, zoning, or shop "
                "permissions."
            ),
        },
    ]
    text = _business_idea(payload).lower()
    if any(word in text for word in ("cafe", "food", "restaurant", "bakery")):
        checklist.append(
            {
                "category": "Food licensing",
                "status": "possible_requirement",
                "note": (
                    "Food businesses often require official food-safety licensing. "
                    "Verify locally."
                ),
            }
        )
    return checklist


def _thirty_day_plan(validation_plan: list[dict[str, Any]]) -> list[str]:
    return [task["task"] for task in validation_plan[:3]]


def _ninety_day_roadmap() -> list[dict[str, str]]:
    return [
        {"days": "1-30", "focus": "Collect local evidence and supplier quotations."},
        {"days": "31-60", "focus": "Run small validation offer and refine financial assumptions."},
        {"days": "61-90", "focus": "Decide whether to launch, change location, pivot, or stop."},
    ]


def _top_performance_opportunity(latest: BusinessPerformanceEntryRequest | None) -> str:
    if latest is None:
        return "Enter the first actual performance period."
    if latest.leads and latest.transactions and latest.leads > latest.transactions:
        return "Improve conversion from leads to paid transactions."
    if latest.repeat_customers and latest.repeat_customers > 0:
        return "Build a repeat-customer offer around the customers already returning."
    return "Identify the highest-performing product, service, or customer source."


def _customer_insight(latest: BusinessPerformanceEntryRequest | None) -> str | None:
    if latest is None:
        return None
    if latest.complaints and latest.complaints > 0:
        return (
            "Complaints were recorded; review complaint themes before increasing marketing spend."
        )
    if latest.customers and latest.transactions and latest.transactions > latest.customers:
        return "Transactions exceed customers, suggesting possible repeat or multi-item purchasing."
    return None


def _inventory_insight(latest: BusinessPerformanceEntryRequest | None) -> str | None:
    if latest is None:
        return None
    if latest.stockouts and latest.stockouts > 0:
        return "Stockouts were recorded; adjust reorder levels and backup supplier coverage."
    if latest.supplier_delays and latest.supplier_delays > 0:
        return "Supplier delays were recorded; consider a backup supplier or earlier ordering."
    return None


def _evidence(
    claim: str,
    source_name: str,
    source_type: str,
    retrieved_at: datetime,
    confidence: str,
    verification_status: str,
    value: Any = None,
    source_url: str | None = None,
    location: dict[str, Any] | None = None,
    freshness: str = "current_session",
    notes: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "claim": claim,
        "source_name": source_name,
        "source_url": source_url,
        "source_type": source_type,
        "retrieval_time": retrieved_at.isoformat(),
        "location": location,
        "value": value,
        "confidence": confidence,
        "verification_status": verification_status,
        "freshness": freshness,
        "notes": notes,
        "tags": tags or [],
    }


def _origin_value(value: Any, origin: str) -> dict[str, Any]:
    return {
        "value": value,
        "origin": origin,
        "confidence": "high" if origin == "user_supplied" else "low",
    }


def _num(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
