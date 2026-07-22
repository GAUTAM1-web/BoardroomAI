from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from time import perf_counter
from typing import Any

import httpx

from app.schemas.business import BusinessAnalysisRequest

PROVIDER_TYPES = (
    "maps",
    "places",
    "weather",
    "news",
    "currency",
    "government_open_data",
    "demographics",
)

COUNTRY_CODES = {
    "australia": "AUS",
    "canada": "CAN",
    "france": "FRA",
    "germany": "DEU",
    "india": "IND",
    "singapore": "SGP",
    "united arab emirates": "ARE",
    "united kingdom": "GBR",
    "uk": "GBR",
    "united states": "USA",
    "usa": "USA",
}


@dataclass
class CacheEntry:
    value: Any
    expires_at: datetime
    provider_type: str


@dataclass
class ProviderHealthState:
    provider_type: str
    provider_name: str
    status: str
    configured: bool
    last_sync: str | None = None
    latency_ms: int | None = None
    error: str | None = None
    cache_hit: bool = False


_CACHE: dict[str, CacheEntry] = {}
_HEALTH: dict[str, ProviderHealthState] = {}


def clear_live_data_cache() -> None:
    _CACHE.clear()


def provider_health(settings: Any) -> dict[str, Any]:
    ttl = _cache_ttl(settings)
    providers = []
    for provider_type in PROVIDER_TYPES:
        provider_name = _provider_name(settings, provider_type)
        configured = _is_configured(settings, provider_type, provider_name)
        current = _HEALTH.get(provider_type)
        if current is None:
            current = ProviderHealthState(
                provider_type=provider_type,
                provider_name=provider_name,
                status="ready" if configured else "disabled",
                configured=configured,
            )
        providers.append(
            {
                "type": provider_type,
                "name": provider_name,
                "status": current.status if configured else "disabled",
                "configured": configured,
                "last_sync": current.last_sync,
                "latency_ms": current.latency_ms,
                "error": current.error,
                "cache_hit": current.cache_hit,
                "cache_ttl_seconds": ttl,
            }
        )
    return {
        "providers": providers,
        "cache": {
            "entries": len(_CACHE),
            "ttl_seconds": ttl,
        },
        "last_updated": datetime.now(UTC).isoformat(),
    }


def gather_live_business_intelligence(
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
    settings: Any | None,
    retrieved_at: datetime,
) -> dict[str, Any]:
    if payload.data_mode != "live" or settings is None:
        return _empty_bundle(settings)

    warnings: list[str] = []
    evidence: list[dict[str, Any]] = []
    competitors: list[dict[str, Any]] = []
    location = _resolve_coordinates(payload, settings, retrieved_at, warnings, evidence)

    places = _places_intelligence(payload, profile, settings, retrieved_at, location)
    warnings.extend(places["warnings"])
    evidence.extend(places["evidence"])
    competitors.extend(places["competitors"])

    weather = _weather_intelligence(payload, profile, settings, retrieved_at, location)
    warnings.extend(weather["warnings"])
    evidence.extend(weather["evidence"])

    news = _news_intelligence(payload, settings, retrieved_at)
    warnings.extend(news["warnings"])
    evidence.extend(news["evidence"])

    currency = _currency_intelligence(payload, settings, retrieved_at)
    warnings.extend(currency["warnings"])
    evidence.extend(currency["evidence"])

    open_data = _open_data_intelligence(payload, settings, retrieved_at)
    warnings.extend(open_data["warnings"])
    evidence.extend(open_data["evidence"])

    return {
        "warnings": warnings,
        "evidence": evidence,
        "competitors": competitors,
        "suppliers": [],
        "location_intelligence": places["location_intelligence"],
        "weather_impact": weather["weather_impact"],
        "news_intelligence": news["news_intelligence"],
        "currency_cost_indicators": currency["currency_cost_indicators"],
        "government_open_data": open_data["government_open_data"],
        "demographics": open_data["demographics"],
        "provider_health": provider_health(settings),
    }


def _empty_bundle(settings: Any | None) -> dict[str, Any]:
    return {
        "warnings": [],
        "evidence": [],
        "competitors": [],
        "suppliers": [],
        "location_intelligence": {},
        "weather_impact": {},
        "news_intelligence": {},
        "currency_cost_indicators": {},
        "government_open_data": {},
        "demographics": {},
        "provider_health": provider_health(settings) if settings is not None else {},
    }


def _resolve_coordinates(
    payload: BusinessAnalysisRequest,
    settings: Any,
    retrieved_at: datetime,
    warnings: list[str],
    evidence: list[dict[str, Any]],
) -> dict[str, float] | None:
    if payload.location.latitude is not None and payload.location.longitude is not None:
        return {"latitude": payload.location.latitude, "longitude": payload.location.longitude}
    if not _is_configured(settings, "maps", _provider_name(settings, "maps")):
        warnings.append("Maps provider is unavailable, so address geocoding was skipped.")
        return None
    query = _location_label(payload)
    data = _get_json(
        "maps",
        settings,
        "https://nominatim.openstreetmap.org/search",
        {
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
        },
    )
    if not isinstance(data, list) or not data:
        warnings.append("Maps provider did not return coordinates for the selected location.")
        return None
    result = data[0]
    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError):
        warnings.append("Maps provider response did not include usable coordinates.")
        return None
    evidence.append(
        _live_evidence(
            claim=f"Location geocoded to {latitude:.5f}, {longitude:.5f}.",
            source_name="OpenStreetMap Nominatim",
            source_type="geocoding",
            retrieved_at=retrieved_at,
            value=result,
            confidence="moderate",
            tags=["location", "maps"],
            source_url="https://nominatim.openstreetmap.org/",
        )
    )
    return {"latitude": latitude, "longitude": longitude}


def _places_intelligence(
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
    settings: Any,
    retrieved_at: datetime,
    location: dict[str, float] | None,
) -> dict[str, Any]:
    provider = _provider_name(settings, "places")
    if not _is_configured(settings, "places", provider):
        return _unavailable("Places provider is disabled; nearby businesses were not retrieved.")

    warnings: list[str] = []
    evidence: list[dict[str, Any]] = []
    competitors: list[dict[str, Any]] = []
    label = _location_label(payload)
    category_query = payload.business_category or _business_idea(payload)
    competitor_results = _nominatim_search(settings, f"{category_query} near {label}", limit=6)
    for result in competitor_results:
        record = _place_record(result, payload, location, "live_provider")
        competitors.append(record)
    if competitors:
        evidence.append(
            _live_evidence(
                claim=(
                    f"Retrieved {len(competitors)} possible nearby competitors "
                    "from live place data."
                ),
                source_name="OpenStreetMap Nominatim",
                source_type="places_search",
                retrieved_at=retrieved_at,
                value=competitors,
                confidence="moderate",
                tags=["competitor", "location"],
                source_url="https://nominatim.openstreetmap.org/",
            )
        )
    else:
        warnings.append("Places provider returned no competitor candidates for the search area.")

    signals: dict[str, list[dict[str, Any]]] = {}
    for signal, query in _location_signal_queries(profile, label).items():
        results = _nominatim_search(settings, query, limit=4)
        signals[signal] = [
            _place_record(result, payload, location, "live_provider") for result in results
        ]

    if any(signals.values()):
        evidence.append(
            _live_evidence(
                claim="Retrieved live location context for access and nearby demand indicators.",
                source_name="OpenStreetMap Nominatim",
                source_type="location_context",
                retrieved_at=retrieved_at,
                value=signals,
                confidence="moderate",
                tags=["location", "access", "complementary_businesses"],
                source_url="https://nominatim.openstreetmap.org/",
            )
        )

    return {
        "warnings": warnings,
        "evidence": evidence,
        "competitors": competitors,
        "location_intelligence": {
            "source": "OpenStreetMap Nominatim",
            "selected_area": label,
            "coordinates": location,
            "nearby_competitor_candidates": competitors,
            "complementary_businesses": signals.get("complementary_businesses", []),
            "parking": signals.get("parking", []),
            "public_transport": signals.get("public_transport", []),
            "schools_offices_hospitals": signals.get("schools_offices_hospitals", []),
            "commercial_activity_indicators": signals.get("commercial_activity_indicators", []),
            "limitations": [
                "Open place data may be incomplete, outdated, or uneven by geography.",
                "Absence of a returned place is not evidence that no place exists.",
            ],
        },
    }


def _weather_intelligence(
    payload: BusinessAnalysisRequest,
    profile: dict[str, Any],
    settings: Any,
    retrieved_at: datetime,
    location: dict[str, float] | None,
) -> dict[str, Any]:
    if not _is_configured(settings, "weather", _provider_name(settings, "weather")):
        return _unavailable("Weather provider is disabled; weather impact was not retrieved.")
    if location is None:
        return _unavailable("Weather provider requires coordinates; weather impact was skipped.")

    data = _get_json(
        "weather",
        settings,
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "daily": (
                "temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,precipitation_sum,weather_code"
            ),
            "forecast_days": 7,
            "timezone": "auto",
        },
    )
    if not isinstance(data, dict):
        return _unavailable("Weather provider did not return a usable forecast.")
    daily = data.get("daily") if isinstance(data.get("daily"), dict) else {}
    precipitation = [float(item or 0) for item in daily.get("precipitation_sum", [])]
    rain_probability = [
        float(item or 0) for item in daily.get("precipitation_probability_max", [])
    ]
    max_temps = [float(item or 0) for item in daily.get("temperature_2m_max", [])]
    weather_sensitive = _is_weather_sensitive(payload, profile)
    impact = {
        "source": "Open-Meteo",
        "weather_sensitive": weather_sensitive,
        "forecast_days": len(daily.get("time", [])),
        "average_max_temperature": round(sum(max_temps) / len(max_temps), 1) if max_temps else None,
        "total_precipitation": round(sum(precipitation), 2) if precipitation else None,
        "highest_rain_probability": max(rain_probability) if rain_probability else None,
        "operational_considerations": _weather_considerations(
            payload,
            weather_sensitive,
            precipitation,
            rain_probability,
            max_temps,
        ),
        "seasonal_note": (
            "Use historical weather before staffing, inventory, or launch timing decisions."
        ),
    }
    return {
        "warnings": [],
        "evidence": [
            _live_evidence(
                claim="Retrieved weather forecast for operational impact assessment.",
                source_name="Open-Meteo",
                source_type="weather_forecast",
                retrieved_at=retrieved_at,
                value=impact,
                confidence="moderate",
                tags=["weather", "operations"],
                source_url="https://open-meteo.com/",
            )
        ],
        "weather_impact": impact,
    }


def _news_intelligence(
    payload: BusinessAnalysisRequest,
    settings: Any,
    retrieved_at: datetime,
) -> dict[str, Any]:
    provider = _provider_name(settings, "news")
    if not _is_configured(settings, "news", provider):
        return _unavailable("News provider is disabled; recent market news was not retrieved.")
    query = " ".join(
        item
        for item in [
            payload.business_category,
            payload.location.city,
            payload.location.country,
            "business market regulation",
        ]
        if item
    )
    if not query.strip():
        return _unavailable("News query could not be built from the current intake.")
    data = _get_json(
        "news",
        settings,
        "https://api.gdeltproject.org/api/v2/doc/doc",
        {
            "query": query[:240],
            "mode": "ArtList",
            "format": "json",
            "timespan": "7d",
            "maxrecords": 8,
            "sort": "HybridRel",
        },
    )
    articles = []
    if isinstance(data, dict):
        raw_articles = data.get("articles") or data.get("items") or []
        if isinstance(raw_articles, list):
            articles = [
                {
                    "title": str(item.get("title") or item.get("name") or "Untitled"),
                    "url": item.get("url"),
                    "domain": item.get("domain"),
                    "seen_date": item.get("seendate") or item.get("date_published"),
                }
                for item in raw_articles[:8]
                if isinstance(item, dict)
            ]
    if not articles:
        return _unavailable("News provider returned no recent articles for the query.")
    impact = {
        "source": "GDELT DOC 2.0",
        "query": query,
        "articles": articles,
        "impact_summary": _news_impact_summary(articles, payload),
        "limitations": [
            "News relevance is based on keyword retrieval and should be reviewed manually.",
            "Absence of returned articles is not evidence that no relevant events occurred.",
        ],
    }
    return {
        "warnings": [],
        "evidence": [
            _live_evidence(
                claim=f"Retrieved {len(articles)} recent news items related to the proposal.",
                source_name="GDELT DOC 2.0",
                source_type="news_search",
                retrieved_at=retrieved_at,
                value=impact,
                confidence="moderate",
                tags=["news", "market_trends"],
                source_url="https://www.gdeltproject.org/",
            )
        ],
        "news_intelligence": impact,
    }


def _currency_intelligence(
    payload: BusinessAnalysisRequest,
    settings: Any,
    retrieved_at: datetime,
) -> dict[str, Any]:
    if not _is_configured(settings, "currency", _provider_name(settings, "currency")):
        return _unavailable("Currency provider is disabled; exchange rates were not retrieved.")
    base = str(getattr(settings, "currency_base", "USD") or "USD").upper()
    quotes = _currency_quotes(payload, settings)
    data = _get_json(
        "currency",
        settings,
        "https://api.frankfurter.dev/v2/rates",
        {
            "base": base,
            "quotes": ",".join(quotes),
        },
    )
    rates: list[dict[str, Any]] = []
    if isinstance(data, list):
        rates = [
            {
                "date": item.get("date"),
                "base": item.get("base"),
                "quote": item.get("quote"),
                "rate": item.get("rate"),
            }
            for item in data
            if isinstance(item, dict)
        ]
    if not rates:
        return _unavailable("Currency provider returned no exchange-rate records.")
    indicators = {
        "source": "Frankfurter",
        "base": base,
        "quotes": quotes,
        "rates": rates,
        "cost_note": (
            "Use exchange rates only as a live indicator; supplier quotes control actual costs."
        ),
    }
    return {
        "warnings": [],
        "evidence": [
            _live_evidence(
                claim=f"Retrieved live exchange rates for {base} against {', '.join(quotes)}.",
                source_name="Frankfurter",
                source_type="currency_rate",
                retrieved_at=retrieved_at,
                value=indicators,
                confidence="moderate",
                tags=["currency", "cost"],
                source_url="https://frankfurter.dev/",
            )
        ],
        "currency_cost_indicators": indicators,
    }


def _open_data_intelligence(
    payload: BusinessAnalysisRequest,
    settings: Any,
    retrieved_at: datetime,
) -> dict[str, Any]:
    code = COUNTRY_CODES.get((payload.location.country or "").strip().lower())
    if not code:
        return _unavailable("Country was not mappable to a World Bank country code.")
    if not _is_configured(
        settings,
        "government_open_data",
        _provider_name(settings, "government_open_data"),
    ):
        return _unavailable("Government/open-data provider is disabled.")
    indicators = "SP.POP.TOTL;NY.GDP.PCAP.CD;FP.CPI.TOTL.ZG"
    data = _get_json(
        "government_open_data",
        settings,
        f"https://api.worldbank.org/v2/country/{code}/indicator/{indicators}",
        {"format": "json", "mrnev": 1, "per_page": 20},
    )
    records = []
    if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
        records = [
            {
                "indicator": item.get("indicator", {}).get("value"),
                "indicator_id": item.get("indicator", {}).get("id"),
                "country": item.get("country", {}).get("value"),
                "date": item.get("date"),
                "value": item.get("value"),
            }
            for item in data[1]
            if isinstance(item, dict) and item.get("value") is not None
        ]
    if not records:
        return _unavailable("World Bank provider returned no recent non-empty indicators.")

    demographics = {
        "source": "World Bank",
        "country_code": code,
        "records": [item for item in records if item["indicator_id"] == "SP.POP.TOTL"],
    }
    government_open_data = {
        "source": "World Bank",
        "country_code": code,
        "records": records,
        "limitations": [
            "Country-level indicators may not reflect city or neighborhood conditions."
        ],
    }
    return {
        "warnings": [],
        "evidence": [
            _historical_evidence(
                claim=f"Retrieved recent World Bank country indicators for {code}.",
                source_name="World Bank",
                source_type="government_open_data",
                retrieved_at=retrieved_at,
                value=government_open_data,
                confidence="moderate",
                tags=["government_open_data", "demographics", "economics"],
                source_url="https://api.worldbank.org/",
            )
        ],
        "government_open_data": government_open_data,
        "demographics": demographics,
    }


def _unavailable(message: str) -> dict[str, Any]:
    return {
        "warnings": [message],
        "evidence": [],
        "competitors": [],
        "suppliers": [],
        "location_intelligence": {},
        "weather_impact": {},
        "news_intelligence": {},
        "currency_cost_indicators": {},
        "government_open_data": {},
        "demographics": {},
    }


def _nominatim_search(settings: Any, query: str, limit: int) -> list[dict[str, Any]]:
    data = _get_json(
        "places",
        settings,
        "https://nominatim.openstreetmap.org/search",
        {
            "q": query,
            "format": "jsonv2",
            "limit": min(10, max(1, limit)),
            "addressdetails": 1,
            "extratags": 1,
        },
    )
    return data if isinstance(data, list) else []


def _get_json(provider_type: str, settings: Any, url: str, params: dict[str, Any]) -> Any:
    provider_name = _provider_name(settings, provider_type)
    if not _is_configured(settings, provider_type, provider_name):
        _record_health(provider_type, provider_name, "disabled", False, None, None, False)
        return None

    cache_key = f"{provider_type}:{url}:{sorted(params.items())}"
    now = datetime.now(UTC)
    cached = _CACHE.get(cache_key)
    if cached is not None and cached.expires_at > now:
        _record_health(provider_type, provider_name, "ok", True, 0, None, True)
        return cached.value

    started = perf_counter()
    try:
        with httpx.Client(
            timeout=float(getattr(settings, "live_data_timeout_seconds", 2.5)),
            headers={
                "User-Agent": str(getattr(settings, "provider_user_agent", "BoardroomAI/1.0"))
            },
            follow_redirects=True,
        ) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            value = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        latency_ms = int((perf_counter() - started) * 1000)
        _record_health(provider_type, provider_name, "error", True, latency_ms, str(exc), False)
        return None

    latency_ms = int((perf_counter() - started) * 1000)
    _CACHE[cache_key] = CacheEntry(
        value=value,
        expires_at=now + timedelta(seconds=_cache_ttl(settings)),
        provider_type=provider_type,
    )
    _record_health(provider_type, provider_name, "ok", True, latency_ms, None, False)
    return value


def _record_health(
    provider_type: str,
    provider_name: str,
    status: str,
    configured: bool,
    latency_ms: int | None,
    error: str | None,
    cache_hit: bool,
) -> None:
    _HEALTH[provider_type] = ProviderHealthState(
        provider_type=provider_type,
        provider_name=provider_name,
        status=status,
        configured=configured,
        last_sync=datetime.now(UTC).isoformat() if status == "ok" else None,
        latency_ms=latency_ms,
        error=error,
        cache_hit=cache_hit,
    )


def _provider_name(settings: Any, provider_type: str) -> str:
    attr = {
        "maps": "maps_provider",
        "places": "places_provider",
        "weather": "weather_provider",
        "news": "news_provider",
        "currency": "currency_provider",
        "government_open_data": "government_data_provider",
        "demographics": "demographics_provider",
    }[provider_type]
    return str(getattr(settings, attr, "none") or "none")


def _is_configured(settings: Any, provider_type: str, provider_name: str) -> bool:
    normalized = provider_name.strip().lower()
    if normalized in {"", "none", "disabled", "off"}:
        return False
    if provider_type == "maps" and normalized not in {"osm", "openstreetmap", "osm_nominatim"}:
        return bool(getattr(settings, "maps_api_key", ""))
    if provider_type == "places" and normalized not in {"osm", "openstreetmap", "osm_nominatim"}:
        return bool(getattr(settings, "places_api_key", ""))
    if provider_type == "news" and normalized == "gdelt_cloud":
        return bool(getattr(settings, "gdelt_api_key", ""))
    return True


def _cache_ttl(settings: Any) -> int:
    try:
        return max(60, int(getattr(settings, "live_data_cache_ttl_seconds", 900)))
    except (TypeError, ValueError):
        return 900


def _place_record(
    result: dict[str, Any],
    payload: BusinessAnalysisRequest,
    location: dict[str, float] | None = None,
    origin: str = "live_provider",
) -> dict[str, Any]:
    lat = _float(result.get("lat"))
    lon = _float(result.get("lon"))
    distance = (
        _distance_km(location["latitude"], location["longitude"], lat, lon)
        if location is not None and lat is not None and lon is not None
        else None
    )
    name = str(result.get("name") or str(result.get("display_name") or "").split(",")[0])
    return {
        "name": name or "Unnamed place",
        "category": f"{result.get('class', 'place')}:{result.get('type', 'unknown')}",
        "classification": _live_competitor_classification(result, payload),
        "approximate_location": result.get("display_name"),
        "distance_km": round(distance, 2) if distance is not None else None,
        "rating": None,
        "review_count": None,
        "website": result.get("extratags", {}).get("website")
        if isinstance(result.get("extratags"), dict)
        else None,
        "public_services": [],
        "review_themes": [],
        "common_complaints": [],
        "common_praise": [],
        "source": "OpenStreetMap Nominatim",
        "source_category": "live_evidence",
        "retrieval_timestamp": datetime.now(UTC).isoformat(),
        "verification_status": origin,
        "notes": "Live place result; verify directly before committing spend.",
    }


def _location_signal_queries(profile: dict[str, Any], label: str) -> dict[str, str]:
    return {
        "complementary_businesses": f"{profile['label']} complementary business near {label}",
        "parking": f"parking near {label}",
        "public_transport": f"bus stop train station near {label}",
        "schools_offices_hospitals": f"school office hospital near {label}",
        "commercial_activity_indicators": f"shopping market commercial near {label}",
    }


def _weather_considerations(
    payload: BusinessAnalysisRequest,
    weather_sensitive: bool,
    precipitation: list[float],
    rain_probability: list[float],
    max_temps: list[float],
) -> list[str]:
    considerations = []
    if not weather_sensitive:
        considerations.append(
            "Weather is not a primary driver for this category, but access can still be affected."
        )
    if precipitation and sum(precipitation) > 20:
        considerations.append(
            "Rain may reduce walk-in traffic and increase delivery/logistics friction."
        )
    if rain_probability and max(rain_probability) >= 60:
        considerations.append(
            "Plan staffing, signage, parking, or delivery around likely rain windows."
        )
    if max_temps and max(max_temps) >= 35:
        considerations.append(
            "High heat can affect outdoor queues, cold-chain needs, and staff comfort."
        )
    if not considerations:
        considerations.append("No major weather stress signal was found in the short forecast.")
    if any(word in _business_idea(payload).lower() for word in ("restaurant", "cafe", "food")):
        considerations.append(
            "Food businesses should validate seasonality, footfall, and storage requirements."
        )
    return considerations


def _news_impact_summary(
    articles: list[dict[str, Any]],
    payload: BusinessAnalysisRequest,
) -> list[str]:
    summaries = [
        "Review recent news before launch timing, pricing, hiring, or compliance decisions."
    ]
    combined = " ".join(str(article.get("title", "")).lower() for article in articles)
    if any(word in combined for word in ("regulation", "permit", "license", "ban", "tax")):
        summaries.append(
            "Recent articles mention regulatory language; verify official requirements."
        )
    if any(word in combined for word in ("inflation", "rent", "cost", "shortage", "supply")):
        summaries.append(
            "Cost or supply-pressure language appeared in recent news; update assumptions."
        )
    if payload.location.city and payload.location.city.lower() in combined:
        summaries.append("City-specific articles appeared in the retrieved set.")
    return summaries


def _currency_quotes(payload: BusinessAnalysisRequest, settings: Any) -> list[str]:
    configured = [
        item.strip().upper()
        for item in str(getattr(settings, "currency_quotes", "EUR,GBP,INR")).split(",")
        if item.strip()
    ]
    country = (payload.location.country or "").strip().lower()
    preferred = {
        "india": "INR",
        "united kingdom": "GBP",
        "uk": "GBP",
        "united arab emirates": "AED",
        "canada": "CAD",
        "australia": "AUD",
        "singapore": "SGD",
    }.get(country)
    if preferred and preferred not in configured:
        configured.insert(0, preferred)
    return configured[:6] or ["EUR", "GBP", "INR"]


def _is_weather_sensitive(payload: BusinessAnalysisRequest, profile: dict[str, Any]) -> bool:
    text = f"{_business_idea(payload)} {payload.business_category or ''} {profile['label']}".lower()
    return any(
        word in text
        for word in (
            "restaurant",
            "cafe",
            "food",
            "agriculture",
            "farm",
            "tourism",
            "travel",
            "logistics",
            "retail",
            "outdoor",
        )
    )


def _live_competitor_classification(
    result: dict[str, Any],
    payload: BusinessAnalysisRequest,
) -> str:
    text = (
        f"{result.get('display_name', '')} {result.get('class', '')} "
        f"{result.get('type', '')}"
    ).lower()
    idea_words = set(_business_idea(payload).lower().replace("-", " ").split())
    if any(word in text for word in idea_words if len(word) >= 5):
        return "direct_competitor"
    if any(word in text for word in ("supplier", "wholesale", "distributor")):
        return "supplier"
    return "nearby_business"


def _live_evidence(
    claim: str,
    source_name: str,
    source_type: str,
    retrieved_at: datetime,
    confidence: str,
    value: Any = None,
    source_url: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    return _provider_evidence(
        claim,
        source_name,
        source_type,
        "live_evidence",
        retrieved_at,
        confidence,
        value,
        source_url,
        tags,
    )


def _historical_evidence(
    claim: str,
    source_name: str,
    source_type: str,
    retrieved_at: datetime,
    confidence: str,
    value: Any = None,
    source_url: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    return _provider_evidence(
        claim,
        source_name,
        source_type,
        "historical_evidence",
        retrieved_at,
        confidence,
        value,
        source_url,
        tags,
    )


def _provider_evidence(
    claim: str,
    source_name: str,
    source_type: str,
    source_category: str,
    retrieved_at: datetime,
    confidence: str,
    value: Any,
    source_url: str | None,
    tags: list[str] | None,
) -> dict[str, Any]:
    from app.domain.business_intelligence.service import _evidence

    record = _evidence(
        claim=claim,
        source_name=source_name,
        source_type=source_type,
        retrieved_at=retrieved_at,
        confidence=confidence,
        verification_status=(
            "live_provider"
            if source_category == "live_evidence"
            else "historical_open_data"
        ),
        value=value,
        source_url=source_url,
        freshness="live" if source_category == "live_evidence" else "historical",
        tags=tags or [],
    )
    record["source_category"] = source_category
    record["provider"] = source_name
    return record


def _business_idea(payload: BusinessAnalysisRequest) -> str:
    if payload.business_idea and payload.business_idea.strip():
        return payload.business_idea.strip()
    return "business opportunity"


def _location_label(payload: BusinessAnalysisRequest) -> str:
    parts = [
        payload.location.address,
        payload.location.market,
        payload.location.locality,
        payload.location.city,
        payload.location.state,
        payload.location.country,
    ]
    label = ", ".join(part.strip() for part in parts if part and part.strip())
    if label:
        return label
    if payload.location.latitude is not None and payload.location.longitude is not None:
        return f"{payload.location.latitude:.5f}, {payload.location.longitude:.5f}"
    return "selected location"


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
