# SEO consultant workflow and specialist responsibilities

This playbook converts the build spec, research material, and official Google Search Central guidance into practical roles. The ten roles are review lenses in the current application, not ten independently running AI agents or a substitute for a qualified human SEO reviewer.

## How an SEO engagement runs

1. **Intake:** establish the business goal, audience, products/services, markets and languages, locations, conversions, stack, constraints, baseline, and known competitors.
2. **Measure what is owned:** connect Search Console and analytics for the customer's verified properties. A public crawl cannot reveal owned-site query clicks, impressions, indexing reports, or conversions.
3. **Diagnose the site:** discover URLs, crawl permitted pages, inspect rendered content, responses, redirects, canonicals, robots directives, sitemaps, internal links, page templates, mobile behavior, and structured data.
4. **Map search intent to pages:** use the customer's query data and an authorized SERP/keyword source. Classify intent from result shape and map one page to each distinct need; identify cannibalization and missing content.
5. **Review content:** assess usefulness, accuracy, audience fit, distinctiveness, first-hand evidence, expert review, maintenance needs, and conversion path. Do not create scaled, interchangeable pages.
6. **Prioritize:** combine severity, confidence, business value, and effort. Attach evidence, data snapshot, method, limits, evidence grade, proposed steps, and a verification method.
7. **Get approval:** keep high-risk edits and every external write in a human approval queue. Make the exact target and proposed change clear.
8. **Implement and verify:** create a draft or patch, preview it, rerun checks, preserve before/after evidence, provide rollback, and only then publish through a configured connector.
9. **Measure outcomes:** compare the agreed search and conversion baseline after sufficient time. Use matched controls where practical, record confounders, and do not promise a position or date.

Google describes Search in distinct discovery/crawling, indexing, and serving stages. A page can be crawled but not indexed, and eligibility does not guarantee that it will be served for a query. Therefore SEON should report the stage and evidence it actually observed and ask for Search Console data when the diagnosis needs it.

## Specialist lenses

| Role | Work product |
|---|---|
| SEO lead / intake | Business brief, scope, goal and conversion criteria |
| Technical SEO | Crawl/render/index/serve diagnostics and reproducible checks |
| Information architect | Intent-to-page map, hierarchy, internal links and duplicate-intent review |
| Content strategist | Useful content briefs, originality, first-hand proof and maintenance plan |
| SERP / competitor analyst | Observed top-result landscape, gap matrix and clearly labeled hypotheses |
| Search analytics specialist | Owned-site Search Console and analytics baselines, opportunities and annotations |
| Page experience / accessibility | Mobile and field/lab context, accessibility and conversion friction |
| Structured data specialist | Valid syntax, visible-content match and feature eligibility |
| Local SEO specialist | Real presence, business profile, NAP, local demand, anti-gating and unique-value checks |
| SEO editor / QA | Evidence review, policy guard, approval, implementation verification and rollback |

## Research notes applied

- The Indonesian WordPress case study argues that technical content optimization should connect to marketing objectives and conversion measurement. It is a single-company qualitative case, so it informs workflow design rather than universal ranking effects.
- The internal-link paper proposes graph-based link planning. SEON should measure link depth, reachability, and orphan risk deterministically before claiming that a particular graph arrangement improves rankings.
- The AI-and-e-commerce review motivates automation and personalization as research directions. It does not validate a particular SEO agent, so outputs must retain uncertainty and be measured.

## Current app coverage

The app now has a shared three-scenario engagement intake, contextual public-site reviews, bounded static repository ZIP analysis, and new-site strategy drafts. Public competitor URLs can be checked for observable initial-HTML page signals. Audit runs and approvals are stored locally in SQLite. Repository inspection is read-only and does not create patches or write into an uploaded repository. Search Console, GA4, PageSpeed/Lighthouse with direct CrUX lookup, and DataForSEO organic SERP, keyword ideas, Maps, geo-grid, and backlink estimates have read-only provider adapters. Rendered-browser crawling, Google Ads Keyword Planner, Bing Webmaster account reporting, direct Ahrefs, private Business Profile management, repository-hosting connections, patch generation, CMS writes and production deployment controls remain unimplemented and require account access, provider terms, credentials, and secure infrastructure.

## Client Google-data access and report scope

For a live-site engagement, begin with the public crawl; Search Console and GA4 are optional evidence sources and are not prerequisites for the first review. If private performance data is needed, ask the client to grant the project's Google service-account email access to the relevant Search Console property (read-only) and GA4 property (Viewer). Never ask the client for a Google password or for the service-account JSON key. The operator keeps that key in the API server's secret configuration. Ask for the exact Search Console property URL, numeric GA4 property ID, reporting dates, and the conversions the client considers meaningful. If the client cannot grant access, proceed and label owned-site performance data unavailable.

State the requested report scope clearly: Search Console clicks, impressions, CTR, and average position grouped by query and page, with country/device breakdowns when available; GA4 users, sessions, engagement, configured conversions, and landing-page performance. Include the date range and data source, and call out missing or unavailable data. These are read-only reports; the connectors do not edit or publish client-site changes. Public crawl and PageSpeed findings must remain distinct from private Search Console/GA4 measurements.

## Required pre-analysis brief

Before analysis, ask the client and operator for the following. Mark fields as **unknown** when not supplied; do not fill missing facts with generated assumptions.

| Intake group | Required context | Why the review needs it |
|---|---|---|
| Engagement | Client/organization, operator/consultant, authorization to crawl or inspect a repository, analysis scenario, report owner | Records who requested the work, its scope, and permitted access. |
| Business identity | Public brand, business type, industry/niche, business model, products/services, priority offerings, differentiators, proof, regulated claims and excluded offers | Separates real customer value from generic content or irrelevant keyword suggestions. |
| Audience & intent | Buyer/user roles, needs, questions, purchase stage, objections, terminology used by customers, primary/secondary language | Guides page intent and useful content requirements. |
| Market & geography | Country/market, city/region, currency where relevant, genuine service locations, delivery/shipping coverage, local business presence | Makes location-aware analysis specific and prevents doorway/location pages for areas the business does not serve. |
| Search demand evidence | Client phrases, Search Console queries/pages/date window, keyword-provider data source and date, known seasonal patterns, competitors named by client vs observed in actual SERPs | Separates seed ideas from measured demand and business competitors from search competitors. |
| Website context | Live domain, canonical host and variants, CMS/framework, rendering approach, languages/locale routes, high-value page templates, migrations/releases, access limits, known technical issues | Tells the audit what it can inspect and which implementation route is practical. |
| Repository context | Repository root/branch, framework/router, package manager, server/client rendering, deployment/preview process, test command, excluded files, staging and rollback owner | Makes a code review reproducible and gives approved work a safe place to land. |
| Outcomes | Primary business outcome, measurable conversion event, acceptable lead/order quality, baseline and time period, analytics/CRM attribution limits | Keeps prioritization tied to outcomes rather than traffic alone. |
| Constraints | Brand/legal rules, technical limitations, release freeze, budgets/effort, required human reviewers, data/privacy restrictions, preferred implementation owner | Prevents unsuitable proposals and unsafe writes. |
| Competitors | Up to five named competitors and public URLs, why each competes, product/market overlap, known strengths/weaknesses | Helps compare observable pages; SERP evidence is still needed to assert search competition. |

Never request or store passwords, API secrets, payment details, or private user records in the intake. Store connector credentials separately in a secret manager after the client authorizes a connection.

## Scenario-specific analysis

### Existing public website

- Ask for the authorized site URL plus the business brief. Crawl permitted same-site pages, discover sitemaps and links, and retain URL, status, title, description, heading, canonical, robots, language, internal-link, image-alt and structured-data observations.
- Compare up to five client-provided competitor URLs at the public landing-page level. This does not establish their ranking keywords or why they rank.
- For an actual diagnosis of low rankings, connect verified Search Console query/page/country/device/date data, inspect authorized indexing evidence, and compare analytics/CRM outcomes. A public crawl alone cannot identify ranking causes.
- Give each action evidence, business relevance, confidence, effort, exact target, CMS path or source path, approval state and verification instruction.

### Existing code repository

- Ask for the repository root/branch, deployment/preview process, framework, routing and rendering approach, and files excluded from review. Use a clean branch and keep the original checkout recoverable.
- Inventory routes, templates, metadata, canonical/robots/sitemap logic, structured data, internal links, image alt text, locale routing, generated pages, and content sources. Compare static source with rendered output before concluding an implementation is absent.
- Produce a file path, evidence excerpt, proposed change, impact rationale, review requirements, validation command and rollback path. Do not execute untrusted project code during intake or analysis.
- After a client approves a specific change, create a patch on a reviewable branch, run the repository validation commands, preview representative pages, and show the diff before deployment. Do not publish without explicit authorization.

### New website

- Capture the same business brief before proposing URLs. Map audience needs and observed/validated topics to a small set of distinct page intents, then include CMS/rendering, analytics, crawling, accessibility, structured-data and launch acceptance criteria.
- Use service/location combinations only where genuine coverage and unique information support a useful page. Avoid mass-generating interchangeable pages.
- Present keyword themes as hypotheses until validated with Search Console after launch or a permitted keyword/SERP provider before launch.

## Factor map for the first review

Treat these as diagnostic dimensions, not a claim that every item is a ranking factor:

1. **Discovery & crawl:** permitted access, robots directives, sitemap quality, status codes, redirects, link discovery, crawl depth and orphan risk.
2. **Indexation & URL control:** indexability, canonical consistency, duplicate/parameter URLs, noindex, staging protection, locale/hreflang and sitemap/canonical alignment.
3. **Rendering & delivery:** meaningful content and links in rendered HTML, mobile parity, server/client rendering, response size, HTTPS, server errors and template behavior.
4. **Page relevance:** one clear user intent, accurate title/snippet, useful headings, matching page type, descriptive internal anchors, image context and duplicate/cannibalized intent checks.
5. **Content quality & trust:** first-hand value, factual accuracy, expert/author review where appropriate, sourcing, update date, proof, unique product/service detail and maintenance.
6. **Architecture & internal links:** logical hierarchy, important-page reachability, related page hubs, descriptive anchors, breadcrumbs, duplicate templates and useful navigation.
7. **Structured information:** accurate structured data that matches visible content; local entity/product facts where relevant; no promise of rich results.
8. **Local & commerce fit:** genuine location coverage, consistent business details, useful service-area pages, product facts, price/availability/shipping/returns, and actionable conversions.
9. **Experience & accessibility:** mobile usability, keyboard and screen-reader access, readable content, form friction, field performance data where available, and lab/field metrics labeled separately.
10. **Measurement & competition:** Search Console baseline, analytics/CRM conversion quality, licensed search data, SERP page types, competitor evidence, backlinks/referring domains and change annotations.

Only report what the selected data source can establish. A missing title in fetched HTML is observable; low rankings, backlink quality, conversions and actual query demand require other data.

## Open-source patterns reviewed

- [SEO-crawler](https://github.com/kiranbabuthatha/SEO-crawler) illustrates structured per-URL crawling, sitemap seeds, indexability, heading hierarchy, internal links, hreflang, structured data and sitewide duplicate clusters.
- [seo-auditor](https://github.com/ISTIFANO/seo-auditor) illustrates a FastAPI + React workflow, report-ready findings, polite robots-aware crawls, and separation between inferred on-page topics and ranking data.
- [OpenSEO keyword-research skill](https://github.com/every-app/open-seo/blob/main/web/content/docs/skills/keyword-research.mdx) uses company/market context, seed topics, live metrics, SERP inspection, filtering and approval before saving selected opportunities.
- [SEO-Agent](https://github.com/shekharpatel21/SEO-Agent) demonstrates provider-backed keyword/SERP research and pluggable APIs. Its repository states commercial use requires a separate license, so SEON treats it as a workflow reference and does not copy its code.

Use open-source projects as references only. Check each project's current license and dependencies before adapting code; do not copy code into a commercial product unless its license permits it.

## References

- [Google Search Central SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [Google Search technical requirements](https://developers.google.com/search/docs/essentials/technical)
- [Google Search crawling troubleshooting](https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors)
- [How Google Search works](https://developers.google.com/search/docs/fundamentals/how-search-works)
- [SEON SEO agent build spec](../seo-agent-build-spec.md)
- Research papers in `../research papers/`

## Advanced provider connections

The integrations workspace wires read-only provider flows for Search Console property listing and reports, GA4 Data API reports, PageSpeed Insights/Lighthouse with optional CrUX field data, and DataForSEO organic SERP, keyword ideas, Maps, coordinate geo-grid, and backlink estimates. The server reads credentials from process environment, puts no secret into browser responses, caps report windows/rows, and includes provider/source metadata and caveats with results. A missing credential yields a setup error rather than sample metrics.

Use `.env.example` as the local template. Google service-account access is granted to the client property and read-only scopes are requested by each connector. Production deployments need authentication, per-tenant authorization, encrypted secrets, auditing, rate limits, and consent before running any billable provider query. Remaining candidate integrations are explicitly planned pending implementation and provider terms review.
