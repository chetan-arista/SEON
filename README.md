# SEON Consultant — Part 1 MVP

This is the Part 1 consultant application: a React + Vite dashboard and Python FastAPI service with three engagement scenarios — an existing-site audit, a source-repository review, and a new-site strategy brief. All three start with the same client/operator business intake.

## Run locally (Windows)

### Software to install

- **Python 3.13, 64-bit** from [python.org/downloads/windows](https://www.python.org/downloads/windows/) (currently 3.13.16). In the installer, select **Add python.exe to PATH**. Python 3.12.10 or newer also works.
- **Node.js 24 LTS** from [nodejs.org](https://nodejs.org/). npm is included with Node. Vite requires Node 20.19+ or 22.12+.
- **Git** is optional for running the app. VS Code is optional as an editor.

Do not install Vite, React, FastAPI, or Uvicorn globally; the commands below install the versions declared by this project.

### Start the app

Open PowerShell in the project folder and run:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
npm install
```

If PowerShell blocks environment activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again. Alternatively, skip activation and run `.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`, and use `.venv\Scripts\python.exe -m uvicorn ...` below.

Open **two** PowerShell terminals in the project folder. In terminal 1, activate `.venv` if needed and run:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

In terminal 2, run:

```powershell
npm run dev
```

Open `http://localhost:5173` to use the app. Open `http://localhost:5173/seon-project-brief.html` for the visual, print-ready team-lead briefing. The Vite development server forwards `/api` requests to `127.0.0.1:8000`.

### Accounts and access levels

Copy `.env.example` to `.env`, set `SEON_ADMIN_EMAIL` and a unique `SEON_ADMIN_PASSWORD` of at least 12 characters, then start the API with `--env-file .env`. The configured account is created as the first administrator on startup. Restarting the API will not reset its password. Normal email/password signup creates a client account. The first administrator can promote accounts to `company` or `admin` from **User access**.

- **Admin:** all workspace features, user/account controls and Development diagnostics.
- **Company:** all consultant workspaces and research tools.
- **Client:** live-site audits, own audit history, findings review and report export. Client accounts cannot access repository review, new-site strategy, integrations or other clients' records.

Google sign-in is optional. Create a Google OAuth web client and add `http://localhost:8000/api/auth/google/callback` as an authorized redirect URI. Set `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` and `GOOGLE_OAUTH_REDIRECT_URI` in `.env`. Google sign-in creates client accounts; an administrator can change their role afterward. For HTTPS deployment, set `SEON_COOKIE_SECURE=true` and configure the production frontend URL and exact allowed origins.

## What it does now

- Crawls up to 25 same-site URLs, starting from the submitted URL and sitemap when available, and follows same-site links.
- Honors basic `robots.txt` agent/path rules. Private/reserved IPs are blocked, each request is pinned to its validated DNS answer, redirects are rechecked, redirect count is bounded, and HTML responses are capped.
- Checks initial HTML for page titles, meta descriptions, headings, viewport, language, canonical, `noindex`, and missing image alt attributes. It flags repeated page titles across crawled pages.
- Produces a new-site strategy draft from a business intake, including a page map, technical launch requirements, prioritized backlog, source registry, and unique-value gate for service-area pages.
- Collects the client, operator, industry, business category, audience, products/services, location, languages, competitors, search themes, differentiators, goal, conversion, platform, baseline and constraints before analysis.
- Reviews a website source ZIP using bounded, read-only static scanning. Findings include ZIP-relative source paths and require rendered-output review before a code change.
- Generates location-aware search-topic hypotheses from stated services and search themes. They are not validated keywords and contain no fabricated search volumes, difficulty, SERP positions or ranking predictions.
- Reads up to five client-provided competitor URLs for public landing-page title, description and H1 observations, subject to basic robots rules. This is not SERP competitor discovery.
- Includes ten specialist review lenses and the consultant workflow described in `docs/expert-workflow.md`.
- Records crawl runs and approval state in a local SQLite database; exports audit and blueprint reports as Markdown.
- Reports the raw observation, a practical remediation, and a page path or CMS editor location.
- Treats findings as reviewable proposals. Approval decisions persist locally with the audit; they never write to a website.

## Known limits

- The current score is a heuristic summary of the checks above, not a Google score or ranking forecast.
- Repository ZIP analysis has bounded limits: 20 MB upload, 80 MB expanded content, 1,200 archive entries, and a maximum 1 MB per text file. It does not execute project code, install packages, create patches, or write into the client repository.
- The crawler is bounded to at most 50 URLs per run (the UI requests 25), parses initial HTML without a browser, and only interprets basic robots rules. It is not a full JavaScript/browser audit.
- Search Console, GA4, PageSpeed Insights/Lighthouse, DataForSEO organic SERP, keyword ideas, Google Maps snapshots, coordinate geo-grid scans, and backlink estimates are available when credentials/properties are configured. Without Search Console access, the app cannot diagnose actual owned-site query performance or explain ranking changes from search data.
- New-site blueprints use deterministic rules, not a live language model or keyword/competitor data provider. The app does not invent query volume or rank data.
- The workspace starts with real empty states and locally persisted run history; it does not seed fake client findings or metrics.
- Authentication and server-side role checks are implemented for local use. This remains a local, single-workspace development app, not a production multi-tenant SaaS deployment. It lacks organization-level tenant isolation, hosted database, encrypted secrets management, login throttling, password recovery/email verification, job queue, observability, backups and CMS write/rollback connectors.
- Approval decisions persist locally, but approval does not publish a change. CMS writes must wait for connector credentials, staging/preview, verification, and rollback behavior.

## Product rules carried into the MVP

- No ranking guarantees. Findings distinguish direct observations from hypotheses and label uncertainty.
- Human approval before any live change. No external writes are implemented.
- Crawled page content is treated as data, never as instructions.
- The next safe build steps are a bounded same-origin multi-page crawler, persisted findings and approvals, a GSC read-only connector, then CMS-specific draft/apply adapters with rollback and verification.

See [seo-agent-build-spec.md](seo-agent-build-spec.md) for the full product requirements and research plan, [expert-workflow.md](docs/expert-workflow.md) for the roles and process, and [competitive-notes.md](docs/competitive-notes.md) for lessons from Vectoron.

## Advanced data integrations

Open **Integrations** in the sidebar to check provider readiness and run live, read-only reports:

- **Google Search Console**: verified property list and query/page/country/device clicks, impressions, CTR, and average position.
- **Google Analytics 4**: page and channel-group sessions, users, configured conversions, engagement rate, and page views.
- **PageSpeed Insights**: mobile or desktop Lighthouse scores, performance audits, and CrUX field data when Google has enough data.
- **DataForSEO**: localized organic results, keyword ideas with provider-reported estimates, Maps snapshots, 3×3/5×5 coordinate scans, and backlink index estimates. Queries (especially every geo-grid point) may be billable.

Set provider environment variables in the API process. Copy `.env.example` to `.env` and launch Uvicorn with `--env-file .env` so the values are loaded:

```powershell
python -m uvicorn backend.main:app --reload --port 8000 --env-file .env
```

For Google data, create a Google Cloud service account, enable Search Console API and Google Analytics Data API, set `GOOGLE_APPLICATION_CREDENTIALS` to the JSON file path, add the account to each GSC property as a read-only user, and grant Viewer access in GA4. Use the numeric GA4 property ID, not the `G-...` measurement ID. `PAGESPEED_API_KEY` is optional at low volume. Set `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` to enable paid SERP lookups. Do not commit credential files or `.env`.

The integration status endpoint never returns secret values. GSC and GA4 share the service-account file path but each adapter requests only its read scope. Google OAuth sign-in credentials are separate from the service account used for Search Console/GA4 reports.

Still not implemented: Google Ads Keyword Planner, Bing Webmaster account reports, direct Ahrefs connection, private Google Business Profile account management, CMS writes for WordPress/Shopify, scheduled alerts, content publishing, AI visibility monitoring, and research-radar feeds. Public Maps results and geo-grid scans are implemented through DataForSEO; they do not connect to or modify a Business Profile account. Backlink estimates/samples are implemented through DataForSEO and are not an Ahrefs connection. Read-only research can inform recommendations; approvals are recorded, but this release does not apply or publish site changes.

## Current scope and production readiness

The ten specialists are implemented as review lenses and a deterministic SEO workflow, not ten autonomous expert-grade AI agents. The current analysis is a deterministic local MVP; provider reports add external evidence where configured. It does not promise rankings. Before serving multiple organizations, add organization-level tenant-scoped data and connector credentials, encrypted secrets, audit logs, rate limits, background jobs, monitoring, backups, password recovery/email verification, and deployment hardening. Current role checks isolate client audit data by account; company accounts share the workspace's organization data.
