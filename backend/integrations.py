"""Read-only adapters for external SEO data providers.

Secrets are read only from the server environment. Provider calls are explicit,
bounded, and return the upstream source with the data so reports stay auditable.
"""
from __future__ import annotations

import base64
import asyncio
import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Literal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["integrations"])
TIMEOUT = 25


class PageSpeedRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)
    strategy: str = Field(default="mobile", pattern="^(mobile|desktop)$")


class SearchConsoleRequest(BaseModel):
    site_url: str = Field(min_length=3, max_length=2048)
    start_date: date
    end_date: date
    row_limit: int = Field(default=100, ge=1, le=1000)


class AnalyticsRequest(BaseModel):
    property_id: str = Field(min_length=1, max_length=40)
    start_date: date
    end_date: date


class SerpRequest(BaseModel):
    keyword: str = Field(min_length=2, max_length=200)
    location: str = Field(default="United States", min_length=2, max_length=100)
    language: str = Field(default="English", min_length=2, max_length=50)


class KeywordIdeasRequest(BaseModel):
    seeds: list[str] = Field(min_length=1, max_length=10)
    location: str = Field(default="United States", min_length=2, max_length=100)
    language: str = Field(default="English", min_length=2, max_length=50)
    limit: int = Field(default=50, ge=1, le=100)


class LocalMapsRequest(BaseModel):
    keyword: str = Field(min_length=2, max_length=200)
    location: str = Field(default="", max_length=100)
    language: str = Field(default="English", min_length=2, max_length=50)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class GeoGridRequest(BaseModel):
    keyword: str = Field(min_length=2, max_length=200)
    business_domain: str = Field(min_length=3, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_km: float = Field(default=5, ge=0.5, le=30)
    grid_size: Literal[3, 5] = 3
    language: str = Field(default="English", min_length=2, max_length=50)


class BacklinksRequest(BaseModel):
    target: str = Field(min_length=3, max_length=2048)
    limit: int = Field(default=50, ge=1, le=100)


def _request(url: str, *, method: str = "GET", data: Any = None,
             headers: dict[str, str] | None = None, timeout: int = TIMEOUT) -> dict[str, Any]:
    payload = json.dumps(data).encode() if data is not None else None
    request_headers = {"Accept": "application/json", "User-Agent": "SEON-Consultant/0.2"}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    request_headers.update(headers or {})
    req = urllib.request.Request(url, data=payload, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(5_000_001)
            if len(raw) > 5_000_000:
                raise HTTPException(502, "Provider response exceeded the 5 MB limit.")
            return json.loads(raw.decode("utf-8"))
    except HTTPException:
        raise
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read(1200).decode("utf-8", errors="replace")
        except OSError:
            pass
        raise HTTPException(502, f"Provider returned HTTP {exc.code}: {detail[:500] or 'request failed'}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise HTTPException(502, f"Could not retrieve provider data: {str(exc)[:300]}") from None


async def _request_async(url: str, *, method: str = "GET", data: Any = None,
                         headers: dict[str, str] | None = None, timeout: int = TIMEOUT) -> dict[str, Any]:
    return await asyncio.to_thread(_request, url, method=method, data=data, headers=headers, timeout=timeout)


def _google_token(scopes: list[str]) -> str:
    path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not path:
        raise HTTPException(503, "Set GOOGLE_APPLICATION_CREDENTIALS to a Google service-account JSON file, and grant it read access to the selected property.")
    try:
        import google.auth
        from google.auth.transport.requests import Request
        credentials, _ = google.auth.load_credentials_from_file(path, scopes=scopes)
        if not credentials.valid:
            credentials.refresh(Request())
        if not credentials.token:
            raise ValueError("No access token returned")
        return credentials.token
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, f"Google credentials could not be loaded or refreshed: {str(exc)[:300]}") from None


def _google_headers(scopes: list[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {_google_token(scopes)}"}


async def _google_headers_async(scopes: list[str]) -> dict[str, str]:
    return await asyncio.to_thread(_google_headers, scopes)


def _dataforseo_headers() -> dict[str, str]:
    login = os.getenv("DATAFORSEO_LOGIN", "").strip()
    password = os.getenv("DATAFORSEO_PASSWORD", "").strip()
    if not login or not password:
        raise HTTPException(503, "Configure DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD on the API server. Provider queries may be billable.")
    auth = base64.b64encode(f"{login}:{password}".encode()).decode()
    return {"Authorization": f"Basic {auth}"}


async def _dataforseo(path: str, payload: list[dict], timeout: int = 60) -> dict[str, Any]:
    result = await _request_async(f"https://api.dataforseo.com/v3/{path}", method="POST", data=payload, headers=_dataforseo_headers(), timeout=timeout)
    if result.get("status_code") not in (None, 0, 20000):
        raise HTTPException(502, f"DataForSEO request failed: {result.get('status_message', 'unknown provider error')}")
    tasks = result.get("tasks", [])
    for task in tasks:
        if task.get("status_code") not in (None, 0, 20000):
            raise HTTPException(502, f"DataForSEO task failed: {task.get('status_message', 'unknown provider error')}")
    return result


GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
GA_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"


@router.get("/integrations/status")
async def integrations_status() -> dict:
    google_configured = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip())
    return {
        "mode": "read-only provider adapters",
        "integrations": [
            {"id": "search_console", "name": "Google Search Console", "status": "credentials_set" if google_configured else "needs_setup", "capabilities": ["verified properties", "clicks", "impressions", "CTR", "average position", "query and page dimensions"], "setup": "Create a Google service account, set GOOGLE_APPLICATION_CREDENTIALS, then add its email as a read-only user to the Search Console property."},
            {"id": "ga4", "name": "Google Analytics 4", "status": "credentials_set" if google_configured else "needs_setup", "capabilities": ["sessions", "users", "conversions", "engagement", "page views"], "setup": "Use the same Google service account file and grant its email Viewer access to the GA4 property. Provide the numeric property ID when running a report."},
            {"id": "pagespeed", "name": "PageSpeed Insights + Lighthouse", "status": "configured" if os.getenv("PAGESPEED_API_KEY") else "optional_key", "capabilities": ["mobile/desktop Lighthouse", "SEO/accessibility/performance audits", "CrUX field data when available"], "setup": "Set PAGESPEED_API_KEY for more reliable quota. A key is optional for low-volume use."},
            {"id": "dataforseo", "name": "DataForSEO research", "status": "credentials_set" if os.getenv("DATAFORSEO_LOGIN") and os.getenv("DATAFORSEO_PASSWORD") else "needs_setup", "capabilities": ["localized live organic SERPs", "SERP competitor domains", "keyword ideas with approximate volume and difficulty", "Google Maps listing snapshots", "3×3 and 5×5 coordinate geo-grid scans", "backlink summaries and backlink samples"], "setup": "Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD. Keyword, organic, backlinks, Maps and each geo-grid point are provider queries that may incur charges."},
            {"id": "keyword_planner", "name": "Google Ads Keyword Planner", "status": "planned", "capabilities": ["keyword ideas", "historical volume ranges", "language and geographic targeting"], "setup": "Requires a Google Ads developer token, OAuth access/refresh tokens and customer ID; adapter is not implemented yet."},
            {"id": "bing_webmaster", "name": "Bing Webmaster Tools", "status": "planned", "capabilities": ["Bing search performance", "site scans", "backlinks for verified sites"], "setup": "API access is supported by Bing; OAuth/property workflow is not implemented yet."},
            {"id": "ahrefs", "name": "Ahrefs Webmaster Tools", "status": "planned", "capabilities": ["verified-site audit and backlink data"], "setup": "Provider integration is not implemented. Competitor backlink data requires an eligible paid provider account."},
            {"id": "local", "name": "Google Business Profile management", "status": "planned", "capabilities": ["read/manage owned locations, reviews and posts"], "setup": "Public Maps results and coordinate geo-grids are available through DataForSEO. Private Business Profile account access and changes need an approved OAuth integration and remain unimplemented."},
        ],
        "security": "Credentials remain on the API server and are never returned by this endpoint. This local app has no multi-tenant secret vault; do not expose its API publicly without authentication and encrypted per-client credentials.",
    }


@router.get("/integrations/search-console/sites")
async def search_console_sites() -> dict:
    headers = await _google_headers_async([GSC_SCOPE])
    result = await _request_async("https://www.googleapis.com/webmasters/v3/sites", headers=headers)
    sites = result.get("siteEntry", []) or []
    return {"source": "Google Search Console API", "sites": [{"site_url": s.get("siteUrl"), "permission": s.get("permissionLevel")} for s in sites]}


@router.post("/reports/search-console")
async def search_console_report(body: SearchConsoleRequest) -> dict:
    if body.end_date < body.start_date or (body.end_date - body.start_date).days > 500:
        raise HTTPException(400, "Choose an end date on or after the start date, within a 500-day window.")
    headers = await _google_headers_async([GSC_SCOPE])
    site = urllib.parse.quote(body.site_url, safe="")
    query = {"startDate": body.start_date.isoformat(), "endDate": body.end_date.isoformat(), "dimensions": ["query", "page", "country", "device"], "rowLimit": body.row_limit, "dataState": "final"}
    result = await _request_async(f"https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query", method="POST", data=query, headers=headers)
    rows = [{"keys": r.get("keys", []), "clicks": r.get("clicks", 0), "impressions": r.get("impressions", 0), "ctr": r.get("ctr", 0), "position": r.get("position", 0)} for r in result.get("rows", [])]
    return {"source": "Google Search Console Search Analytics API", "site_url": body.site_url, "period": {"start": body.start_date, "end": body.end_date}, "rows_returned": len(rows), "row_limit": body.row_limit, "rows": rows, "note": "Search Analytics returns top rows rather than a guaranteed complete export; recent data may be incomplete."}


@router.post("/reports/ga4")
async def ga4_report(body: AnalyticsRequest) -> dict:
    if body.end_date < body.start_date or (body.end_date - body.start_date).days > 500:
        raise HTTPException(400, "Choose an end date on or after the start date, within a 500-day window.")
    if not body.property_id.isdigit():
        raise HTTPException(400, "GA4 property ID must be numeric (not the G- measurement ID).")
    headers = await _google_headers_async([GA_SCOPE])
    payload = {"dateRanges": [{"startDate": body.start_date.isoformat(), "endDate": body.end_date.isoformat()}], "dimensions": [{"name": "pagePath"}, {"name": "sessionDefaultChannelGroup"}], "metrics": [{"name": "sessions"}, {"name": "totalUsers"}, {"name": "conversions"}, {"name": "engagementRate"}, {"name": "screenPageViews"}], "limit": 500}
    result = await _request_async(f"https://analyticsdata.googleapis.com/v1beta/properties/{body.property_id}:runReport", method="POST", data=payload, headers=headers)
    dimensions = [x["name"] for x in result.get("dimensionHeaders", [])]
    metrics = [x["name"] for x in result.get("metricHeaders", [])]
    rows = [{**dict(zip(dimensions, [v.get("value", "") for v in r.get("dimensionValues", [])])), **dict(zip(metrics, [v.get("value", "") for v in r.get("metricValues", [])]))} for r in result.get("rows", [])]
    return {"source": "Google Analytics Data API (GA4)", "property_id": body.property_id, "period": {"start": body.start_date, "end": body.end_date}, "rows_returned": len(rows), "rows": rows, "totals": result.get("totals", []), "note": "Conversions use the events configured as key events in this GA4 property."}


@router.post("/performance/pagespeed")
async def pagespeed(body: PageSpeedRequest) -> dict:
    from backend.main import normalize_url, resolve_public_host
    normalized = normalize_url(body.url)
    await resolve_public_host(normalized)
    params = [("url", normalized), ("strategy", body.strategy), ("category", "PERFORMANCE"), ("category", "ACCESSIBILITY"), ("category", "SEO")]
    key = os.getenv("PAGESPEED_API_KEY", "").strip()
    if key:
        params.append(("key", key))
    target = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(params)
    result = await _request_async(target, timeout=60)
    lighthouse = result.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})
    audits = lighthouse.get("audits", {})
    core_audit_ids = ["largest-contentful-paint", "cumulative-layout-shift", "interaction-to-next-paint", "total-blocking-time", "first-contentful-paint", "speed-index"]
    metrics = [{"id": key_id, "title": audits[key_id].get("title"), "display_value": audits[key_id].get("displayValue"), "score": audits[key_id].get("score")} for key_id in core_audit_ids if key_id in audits]
    opportunities = []
    for audit in audits.values():
        if audit.get("score") is not None and audit.get("score") < 0.9 and (audit.get("details", {}).get("type") in {"opportunity", "table", "list"}):
            opportunities.append({"id": audit.get("id"), "title": audit.get("title"), "display_value": audit.get("displayValue"), "description": audit.get("description", "")[:500], "score": audit.get("score")})
    field: dict[str, Any] = {}
    field_source = ""
    field_note = ""
    # PSI is primarily the lab audit; query CrUX directly for durable field data.
    if key:
        try:
            crux = await _request_async("https://chromeuxreport.googleapis.com/v1/records:queryRecord?" + urllib.parse.urlencode({"key": key}), method="POST", data={"url": normalized, "formFactor": "PHONE" if body.strategy == "mobile" else "DESKTOP"})
            field = crux.get("record", {}).get("metrics", {})
            field_source = "Chrome UX Report API" if field else ""
        except HTTPException as exc:
            # Lack of CrUX coverage must not discard a valid Lighthouse lab run.
            field_note = str(exc.detail)[:300]
    return {"source": "Google PageSpeed Insights API / Lighthouse", "url": normalized, "strategy": body.strategy, "fetch_time": lighthouse.get("fetchTime"), "categories": {name: {"score": data.get("score"), "title": data.get("title")} for name, data in categories.items()}, "lab_metrics": metrics, "field_metrics": field, "field_data_source": field_source, "field_data_note": field_note, "opportunities": opportunities[:20], "field_data_available": bool(field), "note": "Lighthouse scores are lab measurements. Direct CrUX field metrics require PAGESPEED_API_KEY and sufficient real-user data for this URL; aggregate origin fallback is not automatic."}


@router.post("/research/serp")
async def serp_research(body: SerpRequest) -> dict:
    result = await _dataforseo("serp/google/organic/live/advanced", [{"keyword": body.keyword, "location_name": body.location, "language_name": body.language, "depth": 20}], 60)
    tasks = result.get("tasks", [])
    task = tasks[0] if tasks else {}
    task_result = (task.get("result") or [{}])[0]
    items = task_result.get("items", [])
    organic = [{"rank": x.get("rank_group"), "absolute_rank": x.get("rank_absolute"), "domain": x.get("domain"), "title": x.get("title"), "url": x.get("url"), "snippet": x.get("description")} for x in items if x.get("type") == "organic"]
    questions = [{"question": x.get("title"), "source": x.get("type")} for x in items if x.get("type") in {"people_also_ask", "related_searches"}]
    return {"source": "DataForSEO Google organic SERP", "keyword": body.keyword, "location": body.location, "language": body.language, "checked_at": task_result.get("datetime"), "organic_results": organic, "questions_and_related": questions, "items_returned": len(items), "cost": task_result.get("cost"), "note": "Live provider query. Provider cost is included when returned; validate geographic coverage and terms for your account."}


@router.post("/research/keywords")
async def keyword_research(body: KeywordIdeasRequest) -> dict:
    seeds = [term.strip() for term in body.seeds if term.strip()]
    if not seeds or any(len(term) < 3 for term in seeds):
        raise HTTPException(400, "Provide one to ten seed keywords, each at least three characters.")
    result = await _dataforseo("dataforseo_labs/google/keyword_ideas/live", [{"keywords": seeds, "location_name": body.location, "language_name": body.language, "include_serp_info": True, "limit": body.limit}], 60)
    task = (result.get("tasks") or [{}])[0]
    task_result = (task.get("result") or [{}])[0]
    rows = []
    for item in task_result.get("items", []):
        data = item.get("keyword_data", item)
        info = data.get("keyword_info") or {}
        props = data.get("keyword_properties") or {}
        serp_info = data.get("serp_info") or {}
        rows.append({"keyword": data.get("keyword"), "search_volume": info.get("search_volume"), "volume_updated": info.get("last_updated_time"), "competition": info.get("competition"), "cpc": info.get("cpc"), "difficulty": props.get("keyword_difficulty"), "serp_features": serp_info.get("serp_item_types", []), "trend": info.get("monthly_searches", [])})
    return {"source": "DataForSEO Labs Google Keyword Ideas", "location": body.location, "language": body.language, "seeds": seeds, "checked_at": task_result.get("datetime"), "results": rows, "rows_returned": len(rows), "cost": task.get("cost", result.get("cost")), "note": "Provider estimates, not Search Console performance. Search-volume and difficulty values are approximate and depend on provider coverage; use date/source metadata when prioritizing."}


def _maps_rows(task_result: dict) -> list[dict]:
    items = task_result.get("items", []) or []
    return [{"rank": x.get("rank_group"), "name": x.get("title"), "domain": x.get("domain"), "url": x.get("url"), "address": x.get("address"), "phone": x.get("phone"), "category": x.get("category"), "rating": (x.get("rating") or {}).get("value"), "review_count": (x.get("rating") or {}).get("votes_count"), "latitude": x.get("latitude"), "longitude": x.get("longitude"), "place_id": x.get("place_id")} for x in items if x.get("type") == "maps_search"]


@router.post("/research/local-maps")
async def local_maps_research(body: LocalMapsRequest) -> dict:
    if (body.latitude is None) != (body.longitude is None):
        raise HTTPException(400, "Enter both latitude and longitude for a coordinate-based map search.")
    if body.latitude is None and not body.location.strip():
        raise HTTPException(400, "Enter a city/market location or both latitude and longitude.")
    task = {"keyword": body.keyword, "language_name": body.language, "depth": 20}
    if body.latitude is not None and body.longitude is not None:
        task["location_coordinate"] = f"{body.latitude},{body.longitude},17z"
    else:
        task["location_name"] = body.location
    result = await _dataforseo("serp/google/maps/live/advanced", [task], 60)
    response_task = (result.get("tasks") or [{}])[0]
    task_result = (response_task.get("result") or [{}])[0]
    return {"source": "DataForSEO Google Maps SERP", "keyword": body.keyword, "location": body.location or f"{body.latitude},{body.longitude}", "checked_at": task_result.get("datetime"), "results": _maps_rows(task_result), "cost": response_task.get("cost", result.get("cost")), "note": "Public Maps SERP observations, not access to or edits in a Google Business Profile account."}


@router.post("/research/geo-grid")
async def local_geo_grid(body: GeoGridRequest) -> dict:
    size = body.grid_size if body.grid_size in {3, 5} else 3
    half = size // 2
    lat_step = body.radius_km / 111.32 / max(half, 1)
    lon_step = body.radius_km / (111.32 * max(abs(math.cos(math.radians(body.latitude))), 0.15)) / max(half, 1)
    nodes = []
    for row in range(size):
        for column in range(size):
            lat = body.latitude + (row - half) * lat_step
            lon = body.longitude + (column - half) * lon_step
            nodes.append({"row": row, "column": column, "latitude": round(lat, 6), "longitude": round(lon, 6), "coordinate": f"{lat:.6f},{lon:.6f},17z"})
    headers = _dataforseo_headers()
    semaphore = asyncio.Semaphore(5)
    async def scan(node: dict) -> dict:
        async with semaphore:
            response = await _request_async("https://api.dataforseo.com/v3/serp/google/maps/live/advanced", method="POST", data=[{"keyword": body.keyword, "location_coordinate": node["coordinate"], "language_name": body.language, "depth": 20}], headers=headers, timeout=60)
            if response.get("status_code") not in (None, 0, 20000):
                raise HTTPException(502, f"DataForSEO geo-grid request failed: {response.get('status_message', 'provider error')}")
            task = (response.get("tasks") or [{}])[0]
            if task.get("status_code") not in (None, 0, 20000):
                raise HTTPException(502, f"DataForSEO geo-grid cell failed: {task.get('status_message', 'provider error')}")
            result = (task.get("result") or [{}])[0]
            listings = _maps_rows(result)
            domain = body.business_domain.lower().removeprefix("www.").strip("/ ")
            matching = next((listing for listing in listings if listing.get("domain") and listing["domain"].lower().removeprefix("www.").split("/")[0] == domain), None)
            return {"row": node["row"], "column": node["column"], "latitude": node["latitude"], "longitude": node["longitude"], "business_rank": matching.get("rank") if matching else None, "matched_listing": matching, "top_listings": listings[:5], "cost": task.get("cost", response.get("cost")), "checked_at": result.get("datetime")}
    cells = await asyncio.gather(*(scan(node) for node in nodes))
    return {"source": "DataForSEO Google Maps coordinate grid", "keyword": body.keyword, "business_domain": body.business_domain, "center": {"latitude": body.latitude, "longitude": body.longitude}, "radius_km": body.radius_km, "grid_size": size, "nodes_requested": len(nodes), "cells": cells, "ranked_cells": sum(1 for cell in cells if cell["business_rank"] is not None), "total_cost": sum(float(cell["cost"] or 0) for cell in cells), "note": "Each grid point is a separate live provider query and may incur a charge. A blank business rank means no listing matched the supplied domain in the returned top results; it is not proof the business has no profile."}


@router.post("/research/backlinks")
async def backlinks_research(body: BacklinksRequest) -> dict:
    raw_target = body.target.strip()
    parsed = urllib.parse.urlsplit(raw_target if "://" in raw_target else "https://" + raw_target)
    if not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(400, "Enter a valid domain or public page URL without credentials.")
    target = parsed.geturl() if parsed.path not in {"", "/"} else parsed.hostname.removeprefix("www.")
    summary_response = await _dataforseo("backlinks/summary/live", [{"target": target, "include_subdomains": True, "backlinks_status_type": "live", "internal_list_limit": 20}], 60)
    summary_task = (summary_response.get("tasks") or [{}])[0]
    summary_result = (summary_task.get("result") or [{}])[0]
    summary = summary_result.get("items", [{}])[0] if summary_result.get("items") else summary_result
    links_response = await _dataforseo("backlinks/backlinks/live", [{"target": target, "mode": "as_is", "limit": body.limit, "backlinks_status_type": "live"}], 60)
    links_task = (links_response.get("tasks") or [{}])[0]
    links_result = (links_task.get("result") or [{}])[0]
    links = [{"source_url": item.get("url_from"), "source_domain": item.get("domain_from"), "target_url": item.get("url_to"), "anchor": item.get("anchor"), "dofollow": item.get("dofollow"), "first_seen": item.get("first_seen"), "last_seen": item.get("last_seen"), "rank": item.get("rank")} for item in links_result.get("items", [])]
    return {"source": "DataForSEO Backlinks API", "target": target, "checked_at": summary_result.get("datetime") or links_result.get("datetime"), "metrics": {key: summary.get(key) for key in ["rank", "backlinks", "backlinks_spam_score", "referring_domains", "referring_main_domains", "referring_ips", "referring_subnets", "crawled_pages", "broken_backlinks", "broken_pages", "external_links_count", "internal_links_count"] if key in summary}, "backlinks": links, "rows_returned": len(links), "cost": (summary_task.get("cost") or 0) + (links_task.get("cost") or 0), "note": "Third-party link-index estimates, not a complete or Google-endorsed link graph. Review relevance and quality manually; do not treat provider toxicity scores as a Google penalty."}

