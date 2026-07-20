from __future__ import annotations

from types import SimpleNamespace

from app.domain.business_intelligence.service import build_board_review, build_business_analysis
from app.schemas.business import (
    BusinessAnalysisRequest,
    BusinessPerformanceEntryRequest,
    FinancialAssumptionsInput,
    LocationInput,
    ManualCompetitorInput,
    ManualSupplierInput,
)


def _request(data_mode: str = "manual") -> BusinessAnalysisRequest:
    return BusinessAnalysisRequest(
        workflow_type="existing_idea",
        business_idea="Mobile-repair shop",
        business_category="Local repair service",
        location=LocationInput(
            country="United States",
            city="Austin",
            locality="Downtown",
            radius_km=3,
        ),
        budget=25_000,
        priorities=["Full analysis", "Competitor analysis", "Supplier discovery"],
        data_mode=data_mode,
        target_customers="office workers and residents needing quick repairs",
        manual_competitors=[
            ManualCompetitorInput(
                name="Downtown Phone Repair",
                category="mobile repair",
                distance_km=1.1,
                notes="User observed weekend queues.",
            )
        ],
        manual_suppliers=[
            ManualSupplierInput(
                name="Parts Wholesale Counter",
                category="screen and battery supplier",
                distance_km=8,
                product_categories=["screens", "batteries"],
                contact_status="called once",
            )
        ],
        customer_observations=["Customers mention unclear prices and long waits."],
        financial_assumptions=FinancialAssumptionsInput(
            expected_rent=1800,
            security_deposit=3600,
            average_transaction_value=45,
            gross_margin_percent=45,
        ),
    )


def test_business_analysis_uses_manual_evidence_and_labels_score() -> None:
    result = build_business_analysis(_request())

    assert result["recommendation"]["label"] in {
        "Proceed to validation",
        "Proceed carefully",
        "Do not commit yet",
    }
    assert result["opportunity_score"]["meaning"].endswith("guarantee.")
    assert "probability" in result["opportunity_score"]["meaning"]
    assert result["competitors"][0]["verification_status"] == "user_provided"
    assert result["suppliers"][0]["verification_status"] == "user_provided"
    assert result["evidence_confidence"] in {"Moderate", "High"}
    assert result["daily_sales"]["daily_targets"]["required_daily_transactions"] > 0
    assert result["procurement_plan"]["opening_inventory"]


def test_demo_mode_is_clearly_labeled_without_fake_suppliers() -> None:
    payload = _request(data_mode="demo").model_copy(
        update={"manual_competitors": [], "manual_suppliers": []}
    )

    result = build_business_analysis(payload)

    assert result["demo_notice"] == "Demo data - not live local evidence."
    assert result["suppliers"] == []
    assert result["competitors"] == []
    assert "Demo data - not live local evidence." in result["warnings"]
    assert result["evidence_confidence"] == "Low"


def test_evidence_panel_distinguishes_source_categories() -> None:
    result = build_business_analysis(_request())

    panel = result["evidence_panel"]

    assert panel["summary"]["user_provided_information"] >= 1
    assert panel["summary"]["ai_inference"] >= 1
    assert "live_evidence" in panel["categories"]
    assert result["evidence"][0]["source_category"] == "user_provided_information"


def test_live_mode_gracefully_degrades_when_providers_are_disabled() -> None:
    settings = SimpleNamespace(
        maps_provider="none",
        places_provider="none",
        weather_provider="none",
        news_provider="none",
        currency_provider="none",
        government_data_provider="none",
        demographics_provider="none",
        maps_api_key="",
        places_api_key="",
        business_data_mode="demo",
        live_data_cache_ttl_seconds=900,
    )

    result = build_business_analysis(_request(data_mode="live"), settings=settings)

    assert result["status"] == "completed"
    assert result["live_intelligence"]["provider_health"]["providers"]
    assert any(provider["status"] == "disabled" for provider in result["evidence_panel"]["provider_health"])
    assert result["warnings"]


def test_board_review_compares_actuals_without_blame() -> None:
    result = build_business_analysis(_request())
    entries = [
        BusinessPerformanceEntryRequest(
            period_label="Week 1",
            revenue=500,
            expenses=900,
            customers=18,
            transactions=20,
            complaints=1,
        )
    ]

    review = build_board_review(result, entries)

    assert review["performance_summary"]["entries_reviewed"] == 1
    assert review["financial_warning"]
    assert review["recommended_experiments"]
