"""Evidence-oriented workflows distilled from Search Central and the project spec."""

import re

EXPERT_ROLES = [
    {"id": "intake", "name": "SEO lead & intake", "scope": "Business objectives, audience, market, conversions, stack, baseline, constraints.", "output": "A scoped brief and measurable success criteria."},
    {"id": "technical", "name": "Technical SEO specialist", "scope": "Discovery, crawl access, rendering, status codes, canonicals, directives, sitemap, mobile parity.", "output": "Page-level evidence and crawl/index diagnostic path."},
    {"id": "architecture", "name": "Information architect", "scope": "Intent-to-page mapping, hubs, internal links, orphan risk, URL stability, cannibalization.", "output": "A page map with one primary intent per page."},
    {"id": "content", "name": "Content strategist", "scope": "Search intent, reader needs, first-hand expertise, originality, content gaps and maintenance.", "output": "Useful page briefs with evidence and expert review requirements."},
    {"id": "serp", "name": "SERP & competitor analyst", "scope": "Discover actual competitors from licensed/provider SERPs; compare top-result page types and observable gaps.", "output": "A gap matrix and hypotheses, never causal claims from correlation."},
    {"id": "analytics", "name": "Search analytics specialist", "scope": "Owned-site Search Console query/page clicks, impressions, CTR, position, index coverage; analytics conversions.", "output": "A measured baseline and opportunity list tied to business outcomes."},
    {"id": "experience", "name": "Page experience & accessibility specialist", "scope": "Mobile usability, field/lab performance distinction, accessible content and conversion friction.", "output": "Reproducible checks with device/data context."},
    {"id": "structured-data", "name": "Structured data specialist", "scope": "Syntax, visible-content parity, eligibility, product/local entity data.", "output": "Markup recommendations that do not promise rich results."},
    {"id": "local", "name": "Local SEO specialist", "scope": "Real business locations, profile completeness, NAP consistency, local demand, unique-value gate.", "output": "Compliant local plan; no review gating or doorway pages."},
    {"id": "editor", "name": "SEO editor & QA", "scope": "Evidence grade, factual accuracy, policy checks, approval scope, post-change verification.", "output": "A reviewed recommendation with a rollback/verification path."},
]

SOURCES = [
    {"id": "GSC-STARTER", "title": "Google Search Central SEO Starter Guide", "url": "https://developers.google.com/search/docs/fundamentals/seo-starter-guide", "grade": "A", "supports": "Search-friendly pages, useful original content, titles, snippets, links, and image context."},
    {"id": "GSC-TECH", "title": "Google Search technical requirements", "url": "https://developers.google.com/search/docs/essentials/technical", "grade": "A", "supports": "Crawl access, successful responses, indexable content; eligibility does not guarantee indexing."},
    {"id": "GSC-CRAWL", "title": "Troubleshoot Google Search crawling errors", "url": "https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors", "grade": "A", "supports": "Crawling diagnostics, sitemaps, robots, and the difference between crawling and indexing."},
    {"id": "GSC-HOW", "title": "How Google Search works", "url": "https://developers.google.com/search/docs/fundamentals/how-search-works", "grade": "A", "supports": "Discovery, crawling, indexing, and serving are separate stages; no guarantee of serving."},
    {"id": "PROJECT-DOORWAY", "title": "SEON project spec: Unique-Value Gate", "url": "seo-agent-build-spec.md#37-service--location-matrix-with-doorway-gate", "grade": "A", "supports": "Project policy requiring real service coverage and unique value before service-area pages."},
    {"id": "PROJECT-APPROVAL", "title": "SEON project spec: approval and repair rules", "url": "seo-agent-build-spec.md#5-repair-agent-serves-part-1-and-part-2", "grade": "A", "supports": "Human approval for live changes, evidence retention, verification, and rollback."},
]

def get_sources_for_area(area: str) -> list[str]:
    mapping = {
        "Crawlability": ["GSC-TECH", "GSC-CRAWL"],
        "Indexation": ["GSC-TECH", "GSC-HOW"],
        "On-page SEO": ["GSC-STARTER"],
        "Content structure": ["GSC-STARTER"],
        "Accessibility": ["GSC-STARTER"],
        "Structured data": ["GSC-STARTER"],
        "Mobile experience": ["GSC-TECH"],
        "Internal links": ["GSC-STARTER"],
    }
    return mapping.get(area, ["GSC-STARTER"])

def build_blueprint(data: dict) -> dict:
    business_type = data["business_type"]
    services = data["services"]
    audience = data["audience"]
    market = data["market"]
    stack = data["stack"]
    competitors = data["competitors"]
    industry = data.get("industry", "")
    search_themes = data.get("search_themes", [])
    pages = [
        {"path": "/", "type": "Homepage", "intent": "Brand + primary category", "reason": "Explain who you serve, the main outcome, and the next action."},
        {"path": "/about/", "type": "About / expertise", "intent": "Brand trust and entity clarity", "reason": "Show real people, experience, credentials, and first-hand evidence."},
        {"path": "/contact/", "type": "Contact / conversion", "intent": "Contact the business", "reason": "Make the primary conversion action clear and measurable."},
    ]
    if business_type == "ecommerce":
        pages.extend([
            {"path": "/collections/", "type": "Category hub", "intent": "Browse a product category", "reason": "Provide useful category guidance and link to products."},
            {"path": "/products/{product}/", "type": "Product detail", "intent": "Evaluate or buy a specific product", "reason": "Use accurate specs, price, availability, shipping and returns information."},
            {"path": "/shipping-returns/", "type": "Policy", "intent": "Understand purchase terms", "reason": "Answer material buyer questions before purchase."},
        ])
    elif business_type == "local_service":
        pages.append({"path": "/services/", "type": "Service hub", "intent": "Compare the services offered", "reason": "Link to each real service page and explain how the services differ."})
        for service in services:
            slug = re.sub(r"[^a-z0-9]+", "-", service.lower()).strip("-")
            pages.append({"path": f"/services/{slug}/", "type": "Service page", "intent": f"Evaluate {service}", "reason": "Explain process, suitability, proof, cost factors and next step."})
    elif business_type == "saas":
        pages.extend([
            {"path": "/product/", "type": "Product overview", "intent": "Evaluate the product", "reason": "Explain capabilities and fit with verifiable product detail."},
            {"path": "/solutions/", "type": "Solution hub", "intent": "Evaluate a use case", "reason": "Organize materially different use cases without thin template pages."},
            {"path": "/pricing/", "type": "Pricing", "intent": "Evaluate price and plans", "reason": "Make package boundaries and conversion options clear."},
            {"path": "/docs/", "type": "Documentation", "intent": "Learn or implement", "reason": "Provide accessible, maintained product documentation."},
        ])
    else:
        pages.extend([
            {"path": "/topics/", "type": "Topic hub", "intent": "Explore a subject area", "reason": "Organize related resources around a clear reader need."},
            {"path": "/resources/", "type": "Resource library", "intent": "Find an answer or reference", "reason": "Publish original, maintained resources with expert review."},
        ])
    if business_type == "local_service" and data.get("service_areas"):
        gate = {"status": "needs_evidence", "message": "Do not create one page per service-area combination yet. Create an area page only when the business really serves it, demand is evidenced, it has at least three page-specific value elements, and it has a place in the internal-link hierarchy.", "service_areas": data["service_areas"], "required_unique_elements": ["real local jobs or projects", "area-specific guidance/pricing/regulations", "local staff or genuine testimonials", "distinct service-area logistics"]}
    else:
        gate = {"status": "not_applicable", "message": "No service-area page matrix was requested."}
    backlog = [
        {"priority": 1, "title": "Confirm business goal and conversion measurement", "why": f"The plan should optimize for {data['goal']} and the conversion event: {data['conversion']}.", "effort": "S", "confidence": "High", "evidence_grade": "A", "sources": ["GSC-STARTER"]},
        {"priority": 2, "title": "Build one useful page per distinct search intent", "why": "Map observed demand and audience needs to page types before drafting content.", "effort": "M", "confidence": "Medium", "evidence_grade": "A", "sources": ["GSC-STARTER"]},
        {"priority": 3, "title": "Set crawl, rendering, indexation and URL requirements", "why": "Important content and links need to be accessible and the site's indexation signals need to agree.", "effort": "M", "confidence": "High", "evidence_grade": "A", "sources": ["GSC-TECH", "GSC-CRAWL"]},
        {"priority": 4, "title": "Instrument a baseline before launch", "why": "Connect Search Console and analytics and record conversions so changes can be measured against the baseline.", "effort": "M", "confidence": "High", "evidence_grade": "A", "sources": ["GSC-HOW"]},
    ]
    return {
        "business": {"client_name": data.get("client_name", ""), "operator_name": data.get("operator_name", ""), "name": data["business_name"], "type": business_type, "business_model": data.get("business_model", ""), "industry": industry, "audience": audience, "market": market, "location": data.get("location", ""), "languages": data.get("languages", []), "domain": data.get("domain", ""), "services": services, "search_themes": search_themes, "differentiators": data.get("differentiators", ""), "goal": data["goal"], "conversion": data["conversion"], "stack": stack, "constraints": data.get("constraints", ""), "baseline": data.get("baseline", "")},
        "competitors": {"provided": competitors, "status": "public_page_observed" if any(str(item).startswith(("http://", "https://")) for item in competitors) else "unverified_inputs", "note": "Competitor domains are client-supplied inputs. The report observes only the supplied public landing pages; actual search competitors, query overlap, rankings, and keyword gaps require permitted SERP or search-data access."},
        "page_map": pages, "service_area_gate": gate, "launch_requirements": [
            "Stable, descriptive URLs with one primary intent per page.",
            "Server-render or statically render important content and crawlable links; verify the rendered page on mobile.",
            "Use consistent indexation, canonical, redirect, robots and sitemap signals; staging must be kept out of search.",
            "Create unique titles and useful snippets; use accurate structured data only when it matches visible eligible content.",
            "Capture author/reviewer, sources, first-hand evidence and review status in the content workflow.",
            "Connect owned-site Search Console and analytics; track the primary conversion, not just visits.",
            f"Use the business category ({industry or business_type}), audience needs, supplied locations, language, and verified differentiators to review every page brief before drafting.",
            "Compare client-provided competitor landing pages for public metadata, message, page type, proof and conversion paths; do not treat those observations as proof of ranking factors.",
        ],
        "backlog": backlog, "limitations": [
            "This is a strategy draft from your intake, not measured keyword research or a complete competitor teardown.",
            "Search-theme suggestions use the client's phrases and services/locations. No search-volume, keyword difficulty, competitor ranking, or rank estimates are invented. Add a permitted SERP/keyword provider to measure them.",
            "Review the plan with a domain expert before publishing. No ranking outcome or date is guaranteed.",
        ],
        "sources": SOURCES,
    }
