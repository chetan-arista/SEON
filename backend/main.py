from __future__ import annotations

import asyncio
import hashlib
import http.client
import ipaddress
import io
import json
import os
import re
import socket
import ssl
import uuid
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse, urlunparse

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from pydantic import BaseModel, Field
from backend.playbook import EXPERT_ROLES, SOURCES, build_blueprint, get_sources_for_area
from backend import storage
from backend.integrations import router as integrations_router
from backend.auth import router as auth_router, bootstrap_admin, user_from_cookie
from backend.admin import router as admin_router

app = FastAPI(title="SEON Consultant API", version="0.2.0")
app.include_router(integrations_router)
app.include_router(auth_router)
app.include_router(admin_router)
storage.init_app()
bootstrap_admin()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("SEON_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def authenticate_api(request: Request, call_next):
    path = request.url.path
    if not path.startswith("/api/") or request.method == "OPTIONS" or path == "/api/health":
        return await call_next(request)

    if request.method not in {"GET", "HEAD"}:
        origin = request.headers.get("origin")
        allowed_origins = {value.strip() for value in os.getenv("SEON_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if value.strip()}
        if origin and origin not in allowed_origins:
            return JSONResponse({"detail": "Request origin is not allowed."}, status_code=403)

    if path.startswith("/api/auth/"):
        return await call_next(request)

    user = user_from_cookie(request)
    if not user:
        return JSONResponse({"detail": "Sign in to continue."}, status_code=401)
    request.state.user = user
    role = user["role"]
    if path.startswith("/api/admin/") and role != "admin":
        return JSONResponse({"detail": "Administrator access is required."}, status_code=403)
    if path in {"/api/experts", "/api/sources"} and role != "admin":
        return JSONResponse({"detail": "Development tools are available to administrators only."}, status_code=403)
    if role == "client":
        allowed = (
            request.method == "POST" and path in {"/api/crawl", "/api/analyze"}
            or request.method == "GET" and (path == "/api/runs" or path.startswith("/api/runs/"))
            or request.method == "PATCH" and path.startswith("/api/findings/")
        )
        if not allowed:
            return JSONResponse({"detail": "Client accounts can only review their live-site audits."}, status_code=403)
    return await call_next(request)

MAX_REDIRECTS = 5
MAX_BODY_BYTES = 2_000_000
TIMEOUT_SECONDS = 12


class AnalyzeRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)


class CrawlRequest(AnalyzeRequest):
    max_pages: int = Field(default=25, ge=1, le=50)
    business_context: dict | None = None
    competitor_urls: list[str] = Field(default_factory=list, max_length=5)


class BlueprintRequest(BaseModel):
    client_name: str = Field(default="", max_length=140)
    operator_name: str = Field(default="", max_length=140)
    business_name: str = Field(min_length=1, max_length=140)
    business_type: str = Field(pattern="^(local_service|saas|ecommerce|publisher|other)$")
    business_model: str = Field(default="", max_length=200)
    audience: str = Field(min_length=2, max_length=500)
    market: str = Field(min_length=2, max_length=300)
    services: list[str] = Field(default_factory=list, max_length=20)
    service_areas: list[str] = Field(default_factory=list, max_length=30)
    goal: str = Field(min_length=2, max_length=300)
    conversion: str = Field(min_length=2, max_length=200)
    stack: str = Field(min_length=2, max_length=200)
    competitors: list[str] = Field(default_factory=list, max_length=10)
    industry: str = Field(default="", max_length=200)
    domain: str = Field(default="", max_length=300)
    location: str = Field(default="", max_length=300)
    languages: list[str] = Field(default_factory=list, max_length=10)
    search_themes: list[str] = Field(default_factory=list, max_length=30)
    differentiators: str = Field(default="", max_length=1500)
    constraints: str = Field(default="", max_length=1500)
    baseline: str = Field(default="", max_length=1500)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.h1: list[str] = []
        self.h2_count = 0
        self.description = ""
        self.canonical = ""
        self.robots = ""
        self.lang = ""
        self.viewport = False
        self.images: list[dict[str, str]] = []
        self.internal_links = 0
        self.external_links = 0
        self.structured_data = 0
        self.has_main = False
        self.base_host = ""
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1.append("")
        elif tag == "h2":
            self.h2_count += 1
        elif tag == "meta":
            if a.get("name", "").lower() == "description":
                self.description = a.get("content", "").strip()
            if a.get("name", "").lower() == "robots":
                self.robots = a.get("content", "").strip().lower()
            if a.get("name", "").lower() == "viewport":
                self.viewport = True
        elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonical = a.get("href", "")
        elif tag == "img":
            self.images.append({"alt": a.get("alt", ""), "src": a.get("src", "")})
        elif tag == "a" and a.get("href", "").strip():
            self.links.append(a["href"].strip())
            self._classify_link(a["href"])
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self.structured_data += 1
        elif tag == "main":
            self.has_main = True

    def _classify_link(self, href: str) -> None:
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return
        destination = urlparse(urljoin("https://" + self.base_host + "/", href))
        if destination.hostname == self.base_host:
            self.internal_links += 1
        else:
            self.external_links += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if self.in_title and text:
            self.title += (" " if self.title else "") + text
        if self.h1 and text:
            self.h1[-1] += (" " if self.h1[-1] else "") + text


def normalize_url(raw: str) -> str:
    candidate = raw.strip()
    if "://" not in candidate:
        candidate = "https://" + candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(400, "Enter a valid public http or https website URL.")
    if parsed.username or parsed.password:
        raise HTTPException(400, "URLs containing usernames or passwords are not allowed.")
    if parsed.port and parsed.port not in {80, 443}:
        raise HTTPException(400, "Only standard web ports 80 and 443 can be audited.")
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", parsed.query, ""))


async def resolve_public_host(url: str) -> list[str]:
    host = urlparse(url).hostname
    if not host:
        raise HTTPException(400, "The URL does not contain a valid hostname.")
    if host.lower() == "localhost" or host.lower().endswith((".localhost", ".local", ".internal")):
        raise HTTPException(400, "Private and local network addresses cannot be audited.")
    try:
        records = await asyncio.to_thread(socket.getaddrinfo, host, None, type=socket.SOCK_STREAM)
    except OSError:
        raise HTTPException(400, "The website hostname could not be resolved.") from None
    addresses = sorted({record[4][0] for record in records})
    if not addresses:
        raise HTTPException(400, "The website hostname has no address records.")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise HTTPException(400, "Private or reserved network addresses cannot be audited.")
    return addresses


class PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, pin_ip: str) -> None:
        super().__init__(host, port, timeout=TIMEOUT_SECONDS)
        self.pin_ip = pin_ip

    def connect(self) -> None:
        self.sock = socket.create_connection((self.pin_ip, self.port), self.timeout)


class PinnedHTTPSConnection(PinnedHTTPConnection):
    def connect(self) -> None:
        sock = socket.create_connection((self.pin_ip, self.port), self.timeout)
        self.sock = ssl.create_default_context().wrap_socket(sock, server_hostname=self.host)


def fetch_once_pinned(url: str, pin_ip: str) -> tuple[int, str, str | None, bytes]:
    parsed = urlparse(url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    connection_type = PinnedHTTPSConnection if parsed.scheme == "https" else PinnedHTTPConnection
    connection = connection_type(parsed.hostname or "", port, pin_ip)
    path = urlunparse(("", "", parsed.path or "/", "", parsed.query, ""))
    try:
        connection.request("GET", path, headers={
            "User-Agent": "SEON-Consultant-Audit/0.1 (+read-only site audit)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity", "Connection": "close",
        })
        response = connection.getresponse()
        content_type = response.getheader("content-type", "")
        location = response.getheader("location")
        body = response.read(MAX_BODY_BYTES + 1)
        if len(body) > MAX_BODY_BYTES:
            raise HTTPException(413, "The page is too large to audit safely (2 MB limit).")
        return response.status, content_type, location, body
    finally:
        connection.close()


async def fetch_public(url: str) -> tuple[str, int, str, bytes]:
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        addresses = await resolve_public_host(current)
        try:
            status, content_type, location, body = await asyncio.to_thread(fetch_once_pinned, current, addresses[0])
        except socket.timeout:
            raise HTTPException(504, "The website took too long to respond.") from None
        except (OSError, ssl.SSLError, http.client.HTTPException):
            raise HTTPException(502, "The website could not be reached from the audit service.") from None
        if status in {301, 302, 303, 307, 308}:
            if not location:
                raise HTTPException(502, "The website returned a redirect without a destination.")
            current = urljoin(current, location)
            current = normalize_url(current)
            continue
        return current, status, content_type, body
    raise HTTPException(400, "The website redirected too many times.")


def finding(title: str, detail: str, severity: str, area: str, page: str, fix: str,
            evidence: str, grade: str = "A", confidence: float = 0.99) -> dict:
    digest = hashlib.sha256(f"{title}|{page}".encode("utf-8")).hexdigest()[:8].upper()
    return {
        "id": f"F-{uuid.uuid4().hex[:12].upper()}", "evidence_id": f"E-{digest}", "title": title,
        "detail": detail, "severity": severity, "area": area, "grade": grade,
        "confidence": confidence, "page": page, "fix": fix, "evidence": evidence,
        "status": "Needs approval", "expected_impact": "unknown",
        "impact_note": "Ranking impact cannot be estimated from this crawl alone.",
        "sources": get_sources_for_area(area),
    }


def keyword_hypotheses(context: dict | None) -> list[str]:
    if not context:
        return []
    location = str(context.get("location", "")).strip()
    services = context.get("offerings") or context.get("services") or []
    if isinstance(services, str):
        services = [services]
    suggestions = [str(theme).strip() for theme in (context.get("search_themes") or []) if str(theme).strip()]
    for service in services[:8]:
        service = str(service).strip()
        if not service:
            continue
        suggestions.extend([f"{service} {location}".strip() if location else service,
                            f"{service} cost {location}".strip() if location else f"{service} cost",
                            f"how to choose {service}"])
    return list(dict.fromkeys(suggestions))[:20]


async def observe_competitors(urls: list[str]) -> list[dict]:
    observations = []
    for raw in urls[:5]:
        try:
            url = normalize_url(raw)
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rules: list[tuple[str, str]] = []
            try:
                _, robots_status, _, robots_body = await fetch_public(robots_url)
                if robots_status == 200:
                    rules, _ = robots_policy(robots_body.decode("utf-8", errors="replace"))
            except HTTPException:
                pass
            if not robots_allows(parsed.path or "/", rules):
                observations.append({"url": url, "domain": parsed.hostname, "status_code": None, "note": "Not fetched because this path is disallowed by robots.txt."})
                continue
            final, status, content_type, body = await fetch_public(url)
            page = PageParser(); page.feed(body.decode("utf-8", errors="replace"))
            observations.append({"url": final, "domain": urlparse(final).hostname, "status_code": status,
                                 "title": page.title[:180], "h1": "; ".join(page.h1[:3])[:300],
                                 "description": page.description[:300], "note": "Observed from the initial public HTML only; not a SERP or competitor-rank comparison."})
        except (HTTPException, ValueError) as exc:
            observations.append({"url": raw[:300], "status_code": None, "note": str(exc.detail) if isinstance(exc, HTTPException) else "URL could not be parsed."})
    return observations


async def add_context_to_crawl(result: dict, context: dict | None, competitor_urls: list[str]) -> None:
    if context:
        result["business_context"] = context
        result["keyword_hypotheses"] = keyword_hypotheses(context)
        result["context_note"] = "Topic suggestions are derived from the supplied business, service, and location. They are not validated search queries and have no search-volume or ranking data."
    if competitor_urls:
        result["competitor_observations"] = await observe_competitors(competitor_urls)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "service": "seon-consultant-api"}


@app.get("/api/experts")
async def experts() -> dict:
    return {"workflow": ["intake", "crawl_and_measure", "diagnose", "prioritize", "propose", "approve", "implement", "verify", "measure"], "specialists": EXPERT_ROLES}


@app.get("/api/sources")
async def sources() -> dict:
    return {"sources": SOURCES}


@app.post("/api/blueprints")
async def create_blueprint(request: BlueprintRequest, auth_request: Request) -> dict:
    brief = request.model_dump()
    result = build_blueprint(brief)
    result["business"]["name"] = brief["business_name"]
    result["business"].update({"client_name": brief["client_name"], "operator_name": brief["operator_name"], "business_model": brief["business_model"], "industry": brief["industry"], "domain": brief["domain"], "location": brief["location"], "languages": brief["languages"], "differentiators": brief["differentiators"], "constraints": brief["constraints"], "baseline": brief["baseline"]})
    result["keyword_hypotheses"] = keyword_hypotheses({"offerings": brief["services"], "search_themes": brief["search_themes"], "location": brief["location"]})
    result["competitor_observations"] = await observe_competitors([item for item in brief["competitors"] if item.startswith(("https://", "http://"))])
    storage.save_blueprint(auth_request.state.user["id"], brief, result)
    return result


@app.get("/api/blueprints/{blueprint_id}")
async def read_blueprint(blueprint_id: str, request: Request) -> dict:
    user = request.state.user
    result = storage.get_blueprint(blueprint_id, user["id"], user["role"])
    if not result:
        raise HTTPException(404, "Blueprint not found.")
    return result


@app.get("/api/runs")
async def read_runs(request: Request) -> dict:
    user = request.state.user
    return {"runs": storage.list_runs(user["id"], user["role"])}


@app.get("/api/runs/{run_id}")
async def read_run(run_id: str, request: Request) -> dict:
    user = request.state.user
    result = storage.get_run(run_id, user["id"], user["role"])
    if not result:
        raise HTTPException(404, "Audit run not found.")
    return result


class FindingUpdate(BaseModel):
    status: str = Field(pattern="^(Needs approval|Approved|Dismissed)$")


@app.patch("/api/findings/{finding_id}")
async def update_finding(finding_id: str, request: FindingUpdate, auth_request: Request) -> dict:
    user = auth_request.state.user
    result = storage.update_finding(finding_id, request.status, user["id"], user["role"])
    if not result:
        raise HTTPException(404, "Finding not found. Re-run the audit to refresh the action list.")
    return result


def robots_policy(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    groups: list[tuple[list[str], list[tuple[str, str]]]] = []
    sitemaps: list[str] = []
    agents: list[str] = []
    rules: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()
        if key == "sitemap":
            sitemaps.append(value)
        elif key == "user-agent":
            if rules:
                groups.append((agents, rules))
                agents, rules = [], []
            agents.append(value.lower())
        elif key in {"allow", "disallow"} and agents and value:
            rules.append((key, value))
    if agents:
        groups.append((agents, rules))
    matching = [group_rules for group_agents, group_rules in groups if "*" in group_agents or "seon-consultant-audit" in group_agents]
    return [rule for group in matching for rule in group], sitemaps


def robots_allows(path: str, rules: list[tuple[str, str]]) -> bool:
    matches = [(len(pattern), directive == "allow") for directive, pattern in rules if path.startswith(pattern)]
    if not matches:
        return True
    return max(matches, key=lambda item: item[0])[1]


def same_site(candidate: str, origin: str) -> bool:
    target, base = urlparse(candidate), urlparse(origin)
    return (target.scheme, target.hostname, target.port) == (base.scheme, base.hostname, base.port)


async def sitemap_page_urls(sitemap_url: str, origin: str, seen: set[str], budget: int) -> list[str]:
    if not same_site(sitemap_url, origin) or sitemap_url in seen or len(seen) >= 5:
        return []
    seen.add(sitemap_url)
    try:
        final, status, content_type, body = await fetch_public(sitemap_url)
        if status >= 400 or len(body) > MAX_BODY_BYTES:
            return []
        if b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper():
            return []
        root = ET.fromstring(body)
    except (HTTPException, ET.ParseError, ValueError):
        return []
    children = [node.text.strip() for node in root.iter() if node.tag.lower().endswith("loc") and node.text and node.text.strip()]
    if "sitemapindex" in root.tag.lower():
        output: list[str] = []
        for child in children:
            if same_site(child, origin):
                output.extend(await sitemap_page_urls(child, origin, seen, budget - len(output)))
            if len(output) >= budget:
                break
        return output[:budget]
    return [urljoin(final, child) for child in children if same_site(urljoin(final, child), origin)][:budget]


@app.post("/api/crawl")
async def crawl_site(request: CrawlRequest, auth_request: Request) -> dict:
    user = auth_request.state.user
    if user["role"] == "client":
        request.max_pages = min(request.max_pages, 10)
        request.business_context = None
        request.competitor_urls = []
    start_url = normalize_url(request.url)
    parsed_start = urlparse(start_url)
    origin = f"{parsed_start.scheme}://{parsed_start.netloc}"
    robots_url = origin + "/robots.txt"
    rules: list[tuple[str, str]] = []
    sitemap_urls: list[str] = []
    try:
        _, robots_status, _, robots_body = await fetch_public(robots_url)
        if robots_status == 200:
            rules, sitemap_urls = robots_policy(robots_body.decode("utf-8", errors="replace"))
    except HTTPException:
        pass

    if not robots_allows(urlparse(start_url).path or "/", rules):
        root_finding = finding("Requested page is disallowed by robots.txt", "The website's crawler policy disallows the URL you submitted, so SEON stopped before fetching it.", "High", "Crawlability", urlparse(start_url).path or "/", "If this is your site and the page should be audited, review the matching robots.txt rule and confirm your crawler access is permitted before scanning again.", f"robots.txt at {robots_url} disallows {urlparse(start_url).path or '/'}.", "A")
        result = {"url": start_url, "requested_url": start_url, "status_code": None, "page_count": 0, "health_score": 0, "pages": [], "findings": [root_finding], "limitations": ["The submitted URL was blocked by robots.txt and was not fetched."]}
        await add_context_to_crawl(result, request.business_context, request.competitor_urls)
        storage.save_run(user["id"], "existing", start_url, result)
        return result

    sitemap_seen: set[str] = set()
    sitemap_candidates: list[str] = []
    for sitemap in (sitemap_urls or [origin + "/sitemap.xml"]):
        sitemap_candidates.extend(await sitemap_page_urls(sitemap, origin, sitemap_seen, request.max_pages))
        if len(sitemap_candidates) >= request.max_pages:
            break

    queue = [start_url] + sitemap_candidates
    queued = set(queue)
    visited: set[str] = set()
    pages: list[dict] = []
    findings: list[dict] = []
    titles: dict[str, list[str]] = {}
    while queue and len(visited) < request.max_pages:
        url = queue.pop(0)
        if url in visited or not same_site(url, origin) or not robots_allows(urlparse(url).path or "/", rules):
            continue
        visited.add(url)
        try:
            final_url, status, content_type, body = await fetch_public(url)
        except HTTPException as exc:
            pages.append({"url": url, "status_code": exc.status_code, "title": "", "issue": str(exc.detail)})
            continue
        if final_url in {p["url"] for p in pages}:
            continue
        path = urlparse(final_url).path or "/"
        if status >= 400:
            findings.append(finding("Page returned an error response", f"The internal URL returned HTTP {status}.", "High", "Crawlability", path,
                                    "Check whether the route should exist. Repair the internal link or return the correct status/redirect after review.", f"HTTP {status} at {final_url}.", "A"))
            pages.append({"url": final_url, "status_code": status, "title": "", "issue": "HTTP error"})
            continue
        if "html" not in content_type.lower():
            continue
        parser = PageParser()
        parser.base_host = (urlparse(final_url).hostname or "").lower()
        parser.feed(body.decode("utf-8", errors="replace"))
        pages.append({"url": final_url, "status_code": status, "title": parser.title, "h1": parser.h1[:2], "description": parser.description, "canonical": parser.canonical, "internal_links": parser.internal_links})
        if parser.title:
            titles.setdefault(parser.title.strip().lower(), []).append(path)
        if not parser.title:
            findings.append(finding("Page has no title element", "Search engines and browsers receive no HTML title for this page.", "High", "On-page SEO", path, "Add a unique, descriptive title in the CMS SEO fields or route template.", f"No title element on {final_url}.", "A"))
        if not parser.description:
            findings.append(finding("Meta description is missing", "No meta description was found in the initial HTML; search engines may choose a snippet from page content.", "Opportunity", "On-page SEO", path, "Add a page-specific meta description that summarizes the visible content.", f"No description meta tag on {final_url}.", "A"))
        if not parser.h1:
            findings.append(finding("No H1 heading found in initial HTML", "A clear page heading helps visitors understand the page. JavaScript-rendered headings may not be included in this check.", "Opportunity", "Content structure", path, "Add a visible main heading that describes the page in natural language.", f"No H1 element on {final_url}.", "B", 0.85))
        if "noindex" in parser.robots:
            findings.append(finding("Page instructs search engines not to index it", "The page's robots meta directive includes noindex.", "Critical", "Indexation", path, "Confirm the page is intentionally excluded. If it should appear in search, remove the directive after approval and verify the rendered response.", f"robots meta content: {parser.robots}.", "A"))
        missing_alt = sum(1 for image in parser.images if "alt" not in image)
        if missing_alt:
            findings.append(finding("Images are missing alt attributes", "Some images have no alt attribute; informative images need a concise description and decorative images need an empty alt value.", "Opportunity", "Accessibility", path, "Review images in context, then add appropriate alt text or an empty alt attribute.", f"{missing_alt} of {len(parser.images)} images missing alt attributes.", "A"))
        for href in parser.links:
            candidate = urljoin(final_url, href)
            parsed_candidate = urlparse(candidate)
            candidate = urlunparse((parsed_candidate.scheme, parsed_candidate.netloc, parsed_candidate.path or "/", "", "", ""))
            if candidate not in queued and candidate not in visited and same_site(candidate, origin) and not parsed_candidate.query and len(visited) + len(queue) < request.max_pages * 2:
                queued.add(candidate)
                queue.append(candidate)

    for normalized_title, paths in titles.items():
        if normalized_title and len(paths) > 1:
            findings.append(finding("Duplicate page titles detected", f"{len(paths)} crawled pages use the same title. Distinct page purposes can be clearer to visitors with unique titles.", "High", "On-page SEO", paths[0], "Review the pages and write accurate, distinct titles that describe their individual content.", f"Title appears on: {', '.join(paths[:10])}.", "A"))
    if not findings:
        findings.append(finding("No audited page-level issues detected", "The checks performed did not find the issues in the current registry. This is not a ranking assessment or a guarantee that every site URL was discovered.", "Opportunity", "Audit summary", urlparse(start_url).path or "/", "Connect Search Console and review content against real query demand and business goals.", f"{len(pages)} HTML pages fetched and checked.", "B", 0.7))
    score = max(0, 100 - sum(12 for item in findings if item["severity"] in {"Critical", "High"}) - sum(3 for item in findings if item["severity"] == "Opportunity"))
    result = {"url": start_url, "requested_url": start_url, "status_code": pages[0]["status_code"] if pages else None, "page_count": len(pages), "health_score": score, "pages": pages, "findings": findings, "limitations": [f"The crawler checked at most {request.max_pages} same-site URLs. It honors basic User-agent: * and SEON robots.txt rules; complex wildcards are not interpreted.", "This is an initial-HTML audit without JavaScript rendering, GSC/GA4 evidence, SERP competitor data, backlink data, or field Core Web Vitals.", "A crawl cannot establish why a page ranks poorly. Connect Search Console for owned-site search and indexation evidence.", "No website changes are applied. Approval only records an action decision; implementation still needs the CMS or source connector."]}
    await add_context_to_crawl(result, request.business_context, request.competitor_urls)
    storage.save_run(user["id"], "existing", start_url, result)
    return result


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest, auth_request: Request) -> dict:
    requested_url = normalize_url(request.url)
    final_url, status_code, content_type, body = await fetch_public(requested_url)
    if "html" not in content_type.lower():
        raise HTTPException(415, "This URL did not return an HTML page. Enter a public webpage URL.")
    html = body.decode("utf-8", errors="replace")
    parser = PageParser()
    parser.base_host = (urlparse(final_url).hostname or "").lower()
    parser.feed(html)
    findings: list[dict] = []
    page = urlparse(final_url).path or "/"

    if status_code >= 400:
        findings.append(finding("Page returned an error response", f"The requested page returned HTTP {status_code}.", "Critical", "Crawlability", page,
                                "Check the route and hosting configuration. Confirm the page should be public, then return the correct status or redirect it intentionally.",
                                f"HTTP status: {status_code}.", "A"))
    if urlparse(requested_url).scheme == "http" and urlparse(final_url).scheme == "https":
        findings.append(finding("HTTP URL redirects to HTTPS", "The site redirects to a secure URL, which is expected. Make sure internal links and sitemap entries use the final HTTPS URL.", "Opportunity", "Crawlability", page,
                                "Update internal links and canonical/sitemap URLs to use the HTTPS destination.", f"Requested {requested_url}; final URL {final_url}.", "A"))
    if not parser.title:
        findings.append(finding("Page has no title element", "Search engines and browsers receive no HTML title for this page.", "High", "On-page SEO", page,
                                "Add a unique, descriptive <title> in this page's SEO settings or route template.", "No <title> text was found in the returned HTML."))
    elif len(parser.title) > 60:
        findings.append(finding("Page title is unusually long", "Long titles may be truncated in some search results; the displayed title can vary.", "Opportunity", "On-page SEO", page,
                                "Review the title and keep its main topic clear near the beginning. Do not remove useful context only to meet a character target.",
                                f"Title length: {len(parser.title)} characters; title: {parser.title[:180]}.", "B", 0.9))
    if not parser.description:
        findings.append(finding("Meta description is missing", "The page has no meta description in its initial HTML. Search engines may create a snippet from page content instead.", "Opportunity", "On-page SEO", page,
                                "Add a page-specific meta description in your CMS SEO fields or route metadata. Treat it as a snippet suggestion, not a ranking guarantee.", "No meta description meta tag was found.", "A"))
    if len(parser.h1) == 0:
        findings.append(finding("No H1 heading found in initial HTML", "A clear main heading can help people understand the page. This check may miss headings rendered only by JavaScript.", "Opportunity", "Content structure", page,
                                "Add one visible, descriptive page heading near the main content. Verify the rendered page and avoid forcing keywords.", "No H1 element was found in the HTML response.", "B", 0.85))
    elif len(parser.h1) > 1:
        findings.append(finding("Multiple H1 headings found", "Multiple H1 elements are present. This is not automatically a ranking problem; review whether the page has one clear main heading.", "Opportunity", "Content structure", page,
                                "Review the page hierarchy and ensure the main topic is clear to readers. Keep additional sections as H2 when that fits the design.",
                                f"H1 count: {len(parser.h1)}. Headings: {'; '.join(parser.h1[:5])}.", "B", 0.78))
    if not parser.viewport:
        findings.append(finding("Mobile viewport declaration is missing", "The initial HTML has no viewport meta tag, which can cause mobile pages to render at desktop width.", "High", "Mobile experience", page,
                                "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> to the document head or shared layout.", "No viewport meta tag was found."))
    if not parser.lang:
        findings.append(finding("Document language is not declared", "Assistive technology and browser tools may not know the page's primary language.", "Opportunity", "Accessibility", page,
                                "Set the correct lang attribute on the root <html> element, such as lang=\"en\".", "The html element has no lang attribute.", "A"))
    if not parser.canonical:
        findings.append(finding("Canonical URL is not declared", "No canonical link was found. This is a review prompt; a canonical is not required on every page and should reflect your URL strategy.", "Opportunity", "Indexation", page,
                                "Confirm whether this page needs a canonical. If so, add a self-referencing canonical to the preferred public URL and check it against redirects and indexation settings.", "No rel=canonical link was found.", "B", 0.72))
    if "noindex" in parser.robots:
        findings.append(finding("Page instructs search engines not to index it", "The page's robots meta directive includes noindex.", "Critical", "Indexation", page,
                                "Confirm the page is intentionally excluded. If it should appear in search, remove noindex from the CMS/template after approval and verify the rendered response.",
                                f"robots meta content: {parser.robots}.", "A"))
    missing_alt = [image for image in parser.images if "alt" not in image]
    if missing_alt:
        findings.append(finding("Images are missing alt attributes", "Some images do not specify alt text. Decorative images should have alt=\"\"; informative images need a concise description.", "Opportunity", "Accessibility", page,
                                "Review each image in context. Add descriptive alt text to informative images and an empty alt attribute to decorative images.",
                                f"{len(missing_alt)} of {len(parser.images)} image elements have no alt attribute.", "A"))
    if not parser.structured_data:
        findings.append(finding("No JSON-LD structured data detected", "This page returned no JSON-LD. Structured data is optional and does not guarantee a rich result.", "Opportunity", "Structured data", page,
                                "Check whether a relevant structured-data type accurately matches visible page content and current eligibility rules. Add only valid, truthful markup.", "No application/ld+json script was found.", "B", 0.7))
    if not findings:
        findings.append(finding("No critical template issues detected", "The initial HTML passed the available deterministic checks. This does not show that the site ranks well or that all rendered pages are healthy.", "Opportunity", "Audit summary", page,
                                "Connect Search Console and audit representative page templates to investigate search visibility and business outcomes.",
                                "Initial HTML checks: title, description, H1, viewport, language, canonical and JSON-LD are present; no noindex directive detected.", "B", 0.72))

    points = sum(1 for f in findings if f["severity"] in {"High", "Critical"})
    health_score = max(0, 100 - points * 12 - sum(1 for f in findings if f["area"] in {"Accessibility", "Content structure"}) * 3)
    result = {
        "url": final_url, "requested_url": requested_url, "status_code": status_code,
        "page_title": parser.title, "page_description": parser.description,
        "h1_count": len(parser.h1), "image_count": len(parser.images),
        "internal_link_count": parser.internal_links, "structured_data_count": parser.structured_data,
        "health_score": health_score, "findings": findings,
        "limitations": [
            "This is a one-page, initial-HTML audit; JavaScript-rendered content and sitewide templates are not inspected yet.",
            "A crawl cannot establish why a page ranks poorly. Connect Google Search Console and Analytics for owned-site performance evidence.",
            "The audit does not measure Core Web Vitals, competitor SERPs, backlinks, or conversions.",
            "No website changes are applied. Each recommendation must be reviewed and implemented in the site's CMS or codebase.",
        ],
    }
    user = auth_request.state.user
    storage.save_run(user["id"], "existing", final_url, result)
    return result


MAX_REPOSITORY_ARCHIVE = 20 * 1024 * 1024
MAX_REPOSITORY_EXPANDED = 80 * 1024 * 1024
MAX_REPOSITORY_FILES = 1200
SOURCE_SUFFIXES = {".html", ".htm", ".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".astro", ".php", ".liquid", ".json", ".xml", ".toml", ".yaml", ".yml", ".md", ".txt"}
SKIP_PARTS = {"node_modules", "vendor", "dist", "build", ".git", ".next", ".venv", "venv", "coverage", "target"}


def repo_findings(files: dict[str, str], context: dict) -> list[dict]:
    findings: list[dict] = []
    source_text = "\n".join(files.values())
    html_paths = [path for path in files if path.lower().endswith((".html", ".htm", ".php", ".liquid", ".astro", ".tsx", ".jsx", ".vue", ".svelte"))]
    candidates = html_paths or list(files)[:1] or ["<repository-root>"]
    title_files = [path for path, text in files.items() if re.search(r"<title\b|<Title\b|title\s*[:=]", text)]
    description_files = [path for path, text in files.items() if re.search(r"name\s*=\s*['\"]description['\"]|name:\s*['\"]description['\"]|description\s*[:=]", text, re.I)]
    canonical_files = [path for path, text in files.items() if re.search(r"rel\s*=\s*['\"]canonical['\"]|rel:\s*['\"]canonical['\"]", text, re.I)]
    h1_files = [path for path, text in files.items() if re.search(r"<h1\b|<H1\b", text)]
    robots_files = [path for path in files if path.lower().endswith("robots.txt")]
    sitemap_files = [path for path in files if "sitemap" in PurePosixPath(path).name.lower() and path.lower().endswith(".xml")]
    package = next((text for path, text in files.items() if PurePosixPath(path).name == "package.json"), "")
    metadata_target = next((path for path in files if path.lower().endswith(("app/layout.tsx", "app/layout.jsx", "pages/_document.tsx", "pages/_document.js"))), None)
    metadata_target = metadata_target or next((path for path in files if PurePosixPath(path).name.lower() in {"index.html", "_document.tsx", "_document.js"}), None) or candidates[0]
    framework = ""
    if "next" in package.lower(): framework = "Next.js"
    elif "vite" in package.lower(): framework = "Vite"
    elif "react" in package.lower(): framework = "React"
    elif any(path.lower().endswith(".php") for path in files): framework = "PHP / possible WordPress or Shopify theme"
    elif any(path.lower().endswith(".liquid") for path in files): framework = "Liquid theme (Shopify-compatible)"
    elif any(path.lower().endswith(".astro") for path in files): framework = "Astro"
    def add_if_missing(present: bool, title: str, detail: str, area: str, recommendation: str, paths: list[str] | None = None) -> None:
        if present:
            return
        path = (paths or candidates)[0]
        findings.append(finding(title, detail, "Opportunity", area, path, recommendation,
                                 f"Static scan of {len(files)} source/config files did not find a recognizable implementation. Check dynamic metadata, CMS-generated output, and runtime HTML before changing code.", "B", 0.72))
    add_if_missing(bool(title_files), "Page title configuration was not found", "No recognizable page title pattern was found in the scanned source. This static check may miss generated or CMS-managed titles.", "On-page SEO", "Inspect the metadata/head configuration at this path. Add unique, business-accurate metadata for important routes, then verify the rendered page source.", [metadata_target])
    add_if_missing(bool(description_files), "Meta description configuration was not found", "No recognizable meta-description pattern was found in scanned source files.", "On-page SEO", "Inspect shared head/metadata configuration at this path. Add useful route-specific descriptions where appropriate, then verify rendered HTML.", [metadata_target])
    add_if_missing(bool(canonical_files), "Canonical configuration was not found", "No recognizable canonical-link pattern was found in scanned source files. A canonical is not required on every page.", "Indexation", "Review the URL and duplicate-content strategy in this metadata layer. If canonicalization is appropriate, implement it and test against redirects.", [metadata_target])
    add_if_missing(bool(h1_files), "Main heading pattern was not found", "No static H1 pattern was found. Dynamic components may add the heading at runtime.", "Content structure", "Check the page component at this path for a clear visible main heading and verify the rendered page. Avoid forcing exact-match keywords.", [candidates[0]])
    add_if_missing(bool(robots_files), "robots.txt was not found in this source archive", "The archive contains no root robots.txt file. A deployed CMS or hosting layer may provide it separately.", "Crawlability", "Check the deployed host first. If no policy exists, create an intentional robots.txt at this target path; do not block assets or important pages by default.", ["public/robots.txt"])
    add_if_missing(bool(sitemap_files), "XML sitemap was not found in this source archive", "No sitemap XML file was included. A framework or CMS may generate it at runtime.", "Crawlability", "Check the deployed sitemap URL and framework/CMS sitemap generator before adding a static file. If the platform needs a static sitemap, create it at this target path and list only canonical, indexable URLs.", ["public/sitemap.xml"])
    missing_alt = []
    for path, content in files.items():
        if not path.lower().endswith((".html", ".tsx", ".jsx", ".vue", ".svelte", ".astro", ".php", ".liquid")):
            continue
        for match in re.finditer(r"<img\b[^>]{0,600}>", content, re.I):
            if not re.search(r"\balt\s*=", match.group(0), re.I):
                missing_alt.append(path); break
    if missing_alt:
        findings.append(finding("Image elements without alt attributes appear in source", "At least one static image element lacks an alt attribute. Decorative images may intentionally use empty alt text.", "Opportunity", "Accessibility", missing_alt[0], "Inspect each reported image in context. Add concise alt text to informative images; set alt=\"\" for decorative images, then verify the rendered output.", f"Static <img> tag scan found an img without an alt attribute in: {', '.join(missing_alt[:8])}.", "B", 0.8))
    if re.search(r"noindex", source_text, re.I):
        findings.append(finding("A noindex directive string exists in the repository", "The source archive contains a noindex directive string; this can be intentional for previews or admin routes.", "High", "Indexation", next(path for path, text in files.items() if re.search(r"noindex", text, re.I)), "Trace whether the directive reaches production pages. Keep staging private; only remove noindex from public pages that should be indexed after approval.", "Matched the literal noindex in scanned source; this does not prove it is active in production.", "B", 0.75))
    if not findings:
        findings.append(finding("No configured SEO pattern was missing in scanned files", "The checked source patterns were present or no static issue was detected. This is not a rendered-site or search-performance pass.", "Opportunity", "Audit summary", candidates[0], "Compare key routes against rendered HTML, Search Console, mobile performance, and the client brief. Static source checks alone cannot confirm what users or search crawlers receive.", "Source-pattern scan only; see repository limitations.", "B", 0.7))
    return findings


@app.post("/api/repository/analyze")
async def analyze_repository(auth_request: Request, archive: UploadFile = File(...), business_context: str = Form(...)) -> dict:
    if not archive.filename or not archive.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Upload a .zip archive of website source files.")
    raw = await archive.read(MAX_REPOSITORY_ARCHIVE + 1)
    if len(raw) > MAX_REPOSITORY_ARCHIVE:
        raise HTTPException(413, "Repository ZIP exceeds the 20 MB upload limit.")
    try:
        context = json.loads(business_context)
        if not isinstance(context, dict):
            raise ValueError()
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(400, "Business context must be valid JSON.") from None
    try:
        bundle = zipfile.ZipFile(io.BytesIO(raw))
        entries = bundle.infolist()
        if len(entries) > MAX_REPOSITORY_FILES:
            raise HTTPException(413, f"Repository archive has more than {MAX_REPOSITORY_FILES} entries.")
        if sum(item.file_size for item in entries) > MAX_REPOSITORY_EXPANDED:
            raise HTTPException(413, "Expanded repository content exceeds the 80 MB analysis limit.")
        files: dict[str, str] = {}
        for item in entries:
            if item.is_dir() or item.file_size > 1_000_000:
                continue
            path = PurePosixPath(item.filename.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts or any(part.lower() in SKIP_PARTS or part.startswith(".") and part not in {".well-known"} for part in path.parts):
                continue
            if path.suffix.lower() not in SOURCE_SUFFIXES or path.name.lower() in {".env", ".env.local", "secrets.json"}:
                continue
            try:
                files[str(path)] = bundle.read(item).decode("utf-8", errors="replace")
            except (OSError, RuntimeError, zipfile.BadZipFile):
                continue
    except zipfile.BadZipFile:
        raise HTTPException(400, "The upload is not a readable ZIP archive.") from None
    if not files:
        raise HTTPException(400, "No supported web source or configuration files were found in the ZIP.")
    findings = repo_findings(files, context)
    package_text = next((text for path, text in files.items() if PurePosixPath(path).name == "package.json"), "")
    framework = "Next.js" if '"next"' in package_text else "Vite" if '"vite"' in package_text else "React" if '"react"' in package_text else "Liquid / PHP theme" if any(p.endswith((".liquid", ".php")) for p in files) else "Static or unrecognized"
    result = {
        "repository_name": archive.filename, "business_context": context, "framework": framework,
        "file_count": len(files), "findings": findings, "keyword_hypotheses": keyword_hypotheses(context),
        "framework_findings": [f"Detected framework family: {framework}.", f"Scanned {len(files)} text source/config files without extracting files to disk.", "Paths in findings are ZIP-relative source paths; confirm the archive root maps to the actual repository root."],
        "competitor_observations": await observe_competitors([item for item in context.get("competitors", []) if str(item).startswith(("https://", "http://"))]),
        "limitations": ["This is a bounded static scan of files included in the ZIP. It does not install or execute repository code.", "It cannot verify server-rendered or CMS-generated output, runtime routes, JavaScript rendering, Search Console coverage, SERPs, links, traffic, or conversion data.", "Findings are review proposals with file paths; no repository files are changed. Approve a separate patch/draft workflow before writing changes."],
        "sources": SOURCES,
    }
    storage.save_run(auth_request.state.user["id"], "repository", archive.filename, result)
    return result
