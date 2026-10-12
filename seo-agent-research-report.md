# SEO Agentic AI: Research Report, Market Gaps and Business Scope

**Prepared:** 12 October 2026
**Purpose:** Decide what to build, why it can win, and how to build and sell it: an SEO agent system (orchestrator + sub-agents) that does the work of a ~10-person SEO team, used internally first and then licensed to other companies.

---

## 0. How to read this report (and what I could and could not verify)

I read your text file line by line, then opened or searched the sources below. Every number in this report carries a source link in Section 15. Anything I could not confirm is marked **[unverified]** or **[my analysis]**.

**What I actually reviewed**

| Source from your file | Status |
|---|---|
| onelittleweb.com best SEO content optimization tools | Read in full |
| frase.io/blog/best-seo-content-platforms | Read in full |
| github.com/dannwaneri/seo-agent | Read in full (README) |
| AgriciDaniel/claude-seo | Read through its release notes (v1.9.9 to v2.3.1). I did not read the repo tree itself |
| semji.com/guide/best-writing-platforms | **Not reviewed** |
| YouTube video `_0wKlt1vHLY` | **Not reviewed** (I cannot watch video from here) |
| GitHub topic pages (`seo-agent`, `seo-agents-github`) | **Not reviewed** |
| `aiapplications001-art/seo-page-creator-agent`, `wfprieto/World-Class-SEO-Agent-System`, `serpapi/seo-agent` | **Not reviewed.** You gave repo names only, no URLs |

**Two honest limits.** First, "PhD-level" research in the strict sense (peer-reviewed literature review, experiments) is not something one session can deliver. What this report does is a serious desk study plus a build plan, and it points out where you would need your own experiments. Second, vendor blogs (Frase, OneLittleWeb) sell something. I use them for facts about products and prices, and I flag their opinions as opinions.

---

## 1. Executive summary

1. **The market is big and moving, but the money is shifting.** Forecasts for SEO software in 2026 range from about $46B to $97B depending on who draws the boundary (Section 3). Whatever the true number, search itself is changing: about 68% of US Google searches ended without a click in early 2026, up from about 60% in 2024, and AI Overviews now cut clicks to the #1 result by roughly 58% in Ahrefs' data.
2. **Existing tools mostly tell you what is wrong. Few close the loop** (find the issue, fix it, publish, measure, learn). Content graders (Surfer, Clearscope, Frase), suites (Semrush, Ahrefs, SE Ranking) and AI-visibility trackers (Profound, Peec, Brand Radar) each cover one slice. A serious team pays for three to five of them.
3. **Open-source SEO agents exist but are thin.** `dannwaneri/seo-agent` is a local audit co-pilot (52 stars, MIT). `claude-seo` is a large skill/agent pack for Claude Code. Neither is a multi-tenant, licensable product with an orchestrator, an evidence-graded indicator registry and a research radar.
4. **The strongest gap for your build** is a system that (a) optimizes for Google ranking and AI-answer citation together, (b) explains every recommendation with evidence and a confidence grade, (c) acts through approved integrations (CMS, GSC), and (d) keeps its own knowledge current. That matches your features 3, 4, 7 and 8 closely.
5. **Three of your feature ideas need a rethink before you build them:** "scrape Medium/YouTube/Reddit" (legal and reliability risk), "train our model on top YouTube videos" (use retrieval and evals, not training), and "200+ indicators" (Google publishes no such list, so you need an evidence-graded registry). Section 7 covers each.
6. **Recommended build order:** audit engine + GSC → competitor/SERP analysis → AI-visibility tracking → research radar → multi-tenant licensing. A usable internal MVP is realistic in 8 to 10 weeks for a small team **[my estimate, not a benchmark]**.

---

## 2. What you asked for, restated (line-by-line understanding of your file)

**Your goal:** An SEO agentic AI plus orchestrator, used inside your company and later sold under license. Target outcome: replace the work of roughly 10 SEO employees to cut time and free the team for other work.

**Platform list (top of your file).** WordPress, Substack, Medium, LinkedIn Articles, Hashnode/Dev.to. This is a "where should content be published" list. It matters for the agent's **publishing connectors** (Section 8). Of these, only WordPress has a mature self-hosted publishing API in practice. Treat the others as "optional channels" later **[my analysis]**.

**Tool list (middle of your file).** Surfer, Clearscope, Frase, Semrush Writing Assistant, Semrush, Ahrefs, SE Ranking, Yoast, Rank Math, Google Search Console, Keyword Planner, Trends. These are your **competitors and your data sources**. Section 4 maps them.

**Links.** Reference reading and repos for existing SEO agents. Section 5 covers what I reviewed.

**Your 11 feature ideas.** Mapped one by one in Section 7.

**Your closing instruction.** "Do the work of 10 SEO employees." Section 10 maps each human role to an agent.

### Corrections and notes on the data in your file

- **Frase pricing is inconsistent in the source.** Your file says $38/month, which comes from the OneLittleWeb table. The same OneLittleWeb article also says "$15/month entry tier" in Frase's overview text, and Frase's own page says plans start at $49/month. Verify on the Frase pricing page before you quote any number.
- **OneLittleWeb sells link building and SEO services.** Its tool rankings are useful, but not neutral.
- **Frase's "best platform" article is written by Frase.** Good for what Frase says it does. Not good as a ranking.
- **Tool prices change often.** All prices in this report are "as published in the cited article, October 2026". Re-check before any pricing decision.

---

## 3. Market size and direction

### 3.1 Size (the numbers disagree, and that is the finding)

| Source | What it measures | 2026 value | Forecast |
|---|---|---|---|
| 360iResearch (report A) | SEO software | $45.9B | $91.6B by 2032, 12.04% CAGR |
| 360iResearch (report B) | SEO software | $86.95B | $190.6B by 2032, 13.93% CAGR |
| Coherent Market Insights | SEO software and tools | $97B | $239B by 2033, 12.5% CAGR |
| SkyQuest | SEO software | ($69.3B in 2024) | $214.9B by 2033, 13.4% CAGR |
| Mordor Intelligence (via SEOWorks) | SEO **services** | $83.98B | $148.86B by 2031 |

**Reading this:** The same publisher (360iResearch) shows $45.9B and $86.95B for 2026 in two reports. Do not quote one number as fact. For a pitch deck, say "published estimates for 2026 range from roughly $46B to $97B, with 12% to 14% annual growth" and cite the range. **[my analysis]** These firms define "SEO software" differently (some include services, local SEO, e-commerce marketplaces).

Coherent also names the **high cost of premium SEO subscriptions as a barrier for small and micro businesses**. That is a pricing opening for you (Section 11).

### 3.2 The shift that matters more than the market size

| Fact | Figure | Source |
|---|---|---|
| US Google searches ending with no click | 68.01% (Jan–Apr 2026) vs 60.45% (2024) | SparkToro, via Webtonic |
| CTR loss for the #1 result when an AI Overview shows | -58% (Dec 2025 data); earlier run showed -34.5% | Ahrefs, via Webtonic |
| Organic CTR on AIO queries | 1.76% → 0.61% (mid-2024 to Sept 2025) | Seer Interactive, via SEO Discovery |
| Benefit of being cited inside an AI Overview | 35% higher organic CTR, 91% higher ad engagement | Seer Interactive |
| Pew Research | CTR 15% → 8% when an AI summary is present | Pew, via SEO Discovery / BusySeed |
| AI Overviews reach | 2.5B+ monthly users (Google, I/O 2026) | via Webtonic (secondary) |
| AIO presence on queries | ~48% of tracked queries (Feb 2026) vs 25.11% of a 21.9M-query sample (Conductor) | Webtonic compiling studies |
| Gartner prediction (Feb 2024) | Traditional search volume down 25% by 2026 | via Scube Marketing |
| GEO research | Princeton/Georgia Tech/IIT Delhi paper (KDD 2024): adding statistics and credible citations were among the most effective ways to get cited; the paper reports up to ~40% visibility lift | via Webtonic / Scube Marketing |

**Notes on reliability.** Several of these figures reach me through secondary blogs, not the original studies. The AIO-presence numbers conflict (48% vs 25%) because the samples differ. In your deck, cite the original (Ahrefs, Seer, SparkToro, Pew) after you open the originals yourself. The direction is consistent across sources: fewer clicks, more answers inside the results page, and a new need to be cited, not only ranked.

**What this means for your product:** an SEO agent built only for classic blue-link ranking is already half-obsolete. Citation in AI answers (GEO/AEO) has to be a core module, not an add-on.

---

## 4. What exists today (competitive map)

### 4.1 Content optimization tools (from your file, verified against OneLittleWeb's article)

| Tool | Strength | Weakness (per the reviewer) | Published price |
|---|---|---|---|
| Surfer SEO | Live content score, NLP terms, SERP analyzer, Google Docs integration | No rank tracking; keyword suggestions can repeat; AI drafts are generic | $79 / $175 / from $999 per month |
| Clearscope | Readability, content grade, decay monitoring, GSC integration | Thin SERP analysis, no AI writing | $129 / $399 / custom |
| Frase | SERP research, outlines, briefs, now also GEO scoring and AI visibility | Older review says weak integrations and uneven AI writing | $38 (OneLittleWeb) or $49 (Frase's own page) |
| MarketMuse | Topic modeling, site-wide audits | Steep learning curve, slow reports | Not published |
| Ahrefs Content Helper | Search-intent breakdown, inside Ahrefs | Basic scoring, opaque score method, no Docs/WordPress integration | Lite $129 up to Enterprise $1,499 |
| Semrush Writing Assistant | Technical flags, tone, plagiarism | Fewer keyword suggestions, scoring "feels arbitrary" per reviewer | From $165.17 |
| PageOptimizer Pro | TF-IDF, E-E-A-T analysis | Dated UI, no live scoring | $56 / $108 / $275 |
| Yoast | Free, WordPress-native | Very basic, one focus keyword free | $118.80/yr premium |
| Dashword, Lex | Briefs / writing quality | Lighter SEO depth, Lex has no SEO features | $99 / $24.99 |

### 4.2 Suites and research platforms

Semrush (~$117–$140+/month entry), Ahrefs (from $129), SE Ranking (from $65). Strengths: keyword databases, backlink indexes, rank tracking, site audits. These are also your likely **data suppliers or API partners** rather than only competitors.

### 4.3 AI-visibility trackers (new category)

| Tool | Notes | Source |
|---|---|---|
| Semrush AI Visibility Toolkit | $99/month per domain (annual billing) | Debutify comparison |
| Ahrefs Brand Radar | Add-on to Ahrefs; covers AI Overviews, AI Mode, ChatGPT, Perplexity, Gemini, Copilot; **does not track Claude or Grok** per the same comparison | Debutify |
| Profound | AI-answer specialist; enterprise pricing per MRS Digital | MRS Digital, Datadab |
| Peec AI | From EUR 89/month | Debutify |
| Scrunch AI | Acquired by Sitecore in June 2026 | Debutify |
| Otterly, AthenaHQ, Writesonic GEO, others | Listed among top AI-SEO tools | Airefs |

A reviewer reported that Brand Radar surfaced only a small fraction of the mentions they counted by hand, and Ahrefs Brand Radar lacked sentiment tracking at the time of testing (MRS Digital). Treat that as one agency's experience, not a benchmark. It does hint at a gap (Section 6, gap 4).

### 4.3b What a "full AI SEO stack" costs today

One reviewer prices the Ahrefs equivalent (Lite plus full Brand Radar) at $828/month and $927 with AI Content Helper, against Semrush One Starter at $199/month bundling AI visibility, full SEO and content AI (Fritz.ai comparison; one reviewer's figures, unverified by me). Even if these are off, the point stands: teams stack subscriptions.

### 4.4 Frase is moving toward your idea

Frase's own article describes: research → writing → publishing (WordPress, Webflow, Sanity, Wix) → SEO and GEO scoring → AI-visibility monitoring → "Content Guard" that watches Search Console decay and proposes fixes, an MCP server and CLI, and an "autonomy dial" (publish automatically, or keep every page under review). This is the closest commercial product to a content-side SEO agent. It is content-focused. It does not claim technical SEO audits, competitor reverse-engineering, or an admin radar for new tools.

### 4.5 Open-source SEO agents

**`dannwaneri/seo-agent`** (MIT, Python, 52 stars, 23 commits when I read it)
- Visits pages in a real Chromium browser (Browser Use + Playwright), extracts title/meta/H1/canonical via Claude, checks broken links, resumable runs, human-in-the-loop pauses for login walls and 404s.
- Modules: backlink qualifier, GSC insights (quick wins and cannibalization), internal-link relevance scorer, topic-cluster audit, SERP-feature detection and LLM-visibility check across Claude, ChatGPT, Gemini, Perplexity and Copilot (via SearchApi).
- **Cost data point:** about $0.006 per URL at the Sonnet tier, about $0.0001 at Haiku; a 20-URL audit at the top tier costs about $0.12. Tiered routing (deterministic checks first, cheap model next, strong model last) is the cost pattern to copy.
- **Stated limits:** runs with a visible browser (not built for server CI), backlink scores are model estimates and not Ahrefs/Moz authority scores, and the author reports the five AI engines rarely agree with each other.
- Optional attestation module cross-checks API calls against billing records. Useful idea for a licensed product (usage integrity).

**`AgriciDaniel/claude-seo`** (read via release notes: v1.9.9 → v2.3.1, latest v2.3.1 dated 10 Sep 2026)
- A Claude Code plugin with a large skill set (v2.2.5 notes: 33 skills, 439 tests) and sub-agents; five judgment-heavy agents (content, GEO, SXO, cluster, drift) run on the stronger model and the other thirteen on the mid tier.
- Tracks Google changes (the v2.2.5 notes mention the August 2026 spam update and Search Console changes). That is a manual version of your feature 8.
- Security fixes in its own history are instructive: SSRF and DNS-rebinding protections, a path-traversal bug in a cache script, an unvalidated WHOIS referral. These show what goes wrong when SEO agents fetch arbitrary URLs. Read Section 9 with that in mind.
- **License not verified by me.** Check before reusing any code commercially.

Neither project is built as a multi-tenant product with billing, roles, white-labeling or an evidence registry.

---

## 5. Gaps in the industry (my analysis, grounded in the sources above)

**Gap 1: Fragmentation and cost.** A real stack is a suite + a content grader + an AI-visibility tracker + a technical crawler. Prices above add up quickly for a small company. Coherent names subscription cost as a barrier for small firms.

**Gap 2: Insight without action.** Most tools produce scores, reports and briefs. Humans still edit the page, update the CMS, add schema, fix links, re-check. Frase's Content Guard and "autonomy dial" show the market wants action with a human approval switch. Almost nobody does it across technical, content, links and AI visibility together.

**Gap 3: Google and AI-citation optimization are scored separately, if at all.** Frase claims it scores both. Incumbent suites add AI visibility as a separate add-on. Few show, for one page, "this change helps Google ranking but hurts AI citation" or the reverse.

**Gap 4: AI-visibility measurement is noisy, and tools rarely show the noise.** The `seo-agent` author found that five engines rarely agreed. One agency found a major tracker missed most manual mentions. A product that runs repeated samples, reports a confidence interval, and states which engines it can and cannot cover would be more honest than a single score. **[my analysis]**

**Gap 5: Scores that nobody validates.** Reviewers describe content scores that "feel arbitrary" (Semrush), with undisclosed formulas (Ahrefs). No vendor publishes how well its score predicts rankings. An agent that backtests its own scoring against the customer's real Search Console data and says how reliable it is would stand out. **[my analysis]**

**Gap 6: "Why do they rank higher" is answered by correlation only.** Competitor tools show what top pages contain. They rarely separate causes from coincidences or propose a test. Your feature 6 should output hypotheses with evidence strength, plus an experiment plan, not a claim.

**Gap 7: Few tools run SEO experiments.** Content tools optimize drafts. Testing whether a change moved rankings, with a control, is a separate niche. As far as I know, dedicated SEO split-testing vendors exist, but I have not verified them here. A built-in "change → control group → measured effect" loop would be rare in an agent.

**Gap 8: Knowledge goes stale.** Google guidance, spam updates and AI-search behavior changed repeatedly in 2026 (see the claude-seo release notes tracking them). Vendors update on their own schedule. Your feature 8 (watch GitHub, Hugging Face, official docs) addresses this directly, if you add human review.

**Gap 9: Agent reliability and cost control in production.** The open-source agents show the problems: headful browsers, model-estimated scores, SSRF risks, failed engine queries. A licensed product needs sandboxing, retries, budget caps per tenant, audit logs and evals. This is engineering work most tool vendors do not advertise.

**Gap 10 (hypothesis, needs checking): regional and language depth.** Frase advertises 70+ languages. I have no data on how well any major tool serves Indian languages or Indian search behavior. If your first customers are in India, test this before treating it as an opening. **[unverified]**

---

## 6. Product definition

### 6.1 One-line pitch
An SEO operating system made of cooperating AI agents that audits, researches, recommends, executes (with approvals), and measures, across classic search and AI answers, with every recommendation backed by cited evidence.

### 6.2 Users
1. **Your internal marketing/SEO team** (first customer).
2. **Agencies** (want white-label reports and multi-client management).
3. **SMB and mid-size companies** with no SEO staff.
4. **Enterprises** (want self-hosted or private-cloud licensing, SSO, audit logs).

### 6.3 The two modes you described
- **Mode A, existing site (consultant mode):** crawl and audit → pull Search Console/analytics → competitor gaps → prioritized fix list (keywords, UI/UX, internal links, backlinks, schema, speed) → optional execution through CMS → re-measure.
- **Mode B, new product/site (research mode):** you describe what you are building and its category → market and keyword research → SERP and competitor study → content and site-architecture plan → launch SEO checklist → report.

Both modes end in a structured report plus an action queue.

### 6.4 Principles
- Evidence first: every finding links to a source, a data point, or a stated assumption.
- Human approval before anything changes a live site.
- Cheapest check first (deterministic code before a model call), as `seo-agent` demonstrates.
- Honest uncertainty: confidence grades and sampling for noisy signals.

---

## 7. Feature specification (your 11 ideas, plus additions)

Priority: **P0** = MVP, **P1** = next, **P2** = later.

| # | Your idea | How I would build it | Main risk | Priority |
|---|---|---|---|---|
| 1 | Scrape latest R&D from Medium and similar | **Research Radar agent.** Prefer RSS feeds, official APIs, sitemaps, newsletters, vendor changelogs, Google Search Central, and academic sources. Store summaries, links and metadata, not full copies. | Copyright and site terms of use. Medium has no open content API as far as I know **[verify]**. Many posts are low quality | P1 |
| 2 | Scrape top 10 trending SEO / SEO-agent YouTube videos and "train our model" | Use the official YouTube Data API for metadata, and transcripts only where permitted. Extract *claims*, then verify each claim before it enters the knowledge base. **Do not fine-tune.** Use retrieval (RAG), playbooks and evals | SEO video content is full of unverified claims. Fine-tuning is expensive, goes stale quickly and adds nothing a good knowledge base does not | P1 |
| 3a | Existing-site changes like a consultant | Mode A workflow (Section 6.3). Findings → ticket-style actions with impact, effort, evidence | Wrong advice at scale. Needs evals and approvals | P0 |
| 3b | New-product category research report | Mode B workflow. Output: market/keyword map, competitor set, content plan, technical checklist | Report quality depends on data sources. Needs a fixed report template and fact-check pass | P0 |
| 4 | Find new ranking parameters/keywords from verified sources and social media | **Signal Discovery agent:** trending queries (Search Console, Trends), community discussions (see #11), vendor studies, experiments. Every "parameter" gets an **evidence grade** (see Section 7.2) | Folklore presented as fact. The grade system is the defense | P1 |
| 5 | Ask for niche, industry and competitors, then find what they do better | Intake wizard → competitor discovery (SERP-based, not only user-supplied) → gap matrix (content, links, technical, SERP features, AI citation) | Competitor list bias. Always add SERP-discovered competitors | P0 |
| 6 | Study the top 3 competitor sites and why they rank higher | Browser/crawl agent on top 10 results (not only 3, to see a distribution) → feature extraction → z-score against the SERP set → ranked hypotheses with evidence strength and a proposed test | Correlation mistaken for cause. Top 3 alone is too small | P0 |
| 7 | 200+ indicators | **Indicator Registry** (Section 7.1) | Google publishes no such list. Weights are guesses unless validated | P0 (registry), P1 (weights) |
| 8 | Admin panel watches GitHub, Hugging Face and tools for new agents/models | **Update Radar:** scheduled scans of chosen repos/releases/model hubs → summarize → security review → sandbox test → human approval → merge to a plugin registry | **Supply-chain risk.** Never auto-integrate third-party agent code. claude-seo's own history includes SSRF and path-traversal fixes | P1 |
| 9 | Sub-agents per task (e.g., content keyword optimization by category) | Specialist agents, one job each (Section 8.2) | Over-engineering. Start with 6 to 8 agents, not 30 | P0 |
| 10 | Run some agents in parallel | Fan-out/fan-in orchestration with a job queue, rate limits and per-tenant budgets | Cost spikes and API limits | P0 |
| 11 | Deep info from Reddit and similar | Use the official Reddit Data API and its terms **[verify commercial-use terms before building]**. Pull question themes, pain points, language people use, then map them to content gaps | Terms of service and API cost. Also, Reddit sentiment is not search demand | P1 |

### 7.1 The Indicator Registry (how to reach "200+" honestly)

Google does not publish a list of ranking factors, and "200 factors" is folklore in the industry. I recall that a 2024 leak of Google Search API documentation fueled new lists, but I did not verify it for this report **[unverified]**. So do not sell "200 Google ranking factors." Sell **"200+ checks, each with a stated evidence level"**.

**Registry design.** One YAML/JSON record per indicator:

```
id, name, category, what_it_checks,
data_source (crawl / GSC / API / SERP / LLM judge),
method (deterministic | statistical | LLM-judged),
evidence_grade (A/B/C/D), evidence_link,
severity_default, weight (learned or manual),
applies_to (page / site / SERP), last_verified, owner
```

**Evidence grades**
- **A: Documented by Google/Bing** (official docs, Search Central).
- **B: Supported by a published controlled experiment or credible study.**
- **C: Correlational** (observed in your own data or third-party data).
- **D: Folklore or vendor claim, unverified.** Shown only as "worth testing", never as a recommendation.

**Starter taxonomy (about 240 checks, easy to expand)**

| Category | Example indicators | Approx. count |
|---|---|---|
| Crawl and indexation | robots.txt, sitemaps, canonicals, noindex errors, redirects, status codes | 30 |
| On-page | title/meta length, H1 count, heading structure, image alt text, URL structure | 30 |
| Content quality and E-E-A-T | author pages, citations, originality, freshness, thin content | 25 |
| Semantic and topical | entity coverage, topic clusters, intent match, cannibalization | 20 |
| Structured data | schema types, validity, required vs recommended fields | 15 |
| Performance and UX | Core Web Vitals, mobile rendering, layout shift, intrusive interstitials | 20 |
| Links and authority | referring-domain quality, anchor mix, toxic patterns, link velocity | 20 |
| Internal linking and architecture | orphan pages, depth, hub pages, link equity flow | 15 |
| Local and international | hreflang, local pack signals, NAP consistency | 15 |
| SERP features and CTR | AI Overview, featured snippet, PAA, snippet fit | 10 |
| AI search / GEO | citation presence per engine, answer-ready structure, statistics and source usage, AI crawler access rules | 20 |
| Brand and off-site | mentions, reviews, community presence | 10 |
| Security, accessibility, compliance | HTTPS, accessibility basics, consent and privacy signals | 10 |

### 7.2 Features I would add that are not in your list
1. **AI visibility tracking** across ChatGPT, Gemini, Perplexity, Copilot, Claude and Google AI Overviews, run as repeated samples with a confidence range (see Gap 4).
2. **Measurement and experiment loop:** every change gets a before/after check against a control group of similar pages.
3. **Content Guard-style decay detection** from Search Console.
4. **Publishing connectors** (WordPress first, then Webflow and others) with an approval queue, as Frase's autonomy dial does.
5. **Cost and budget controls** per tenant.
6. **Audit log and reproducibility:** each report stores the data snapshot, model versions and prompts used.
7. **Report builder** with white-label export.
8. **MCP server and API** so the system can be used from other AI tools and automations, as Frase and claude-seo now do.

---

## 8. Architecture

### 8.1 Layers

```
[ Web app / Admin panel / API / MCP server ]
              |
        [ Orchestrator ]  ← planner, task graph, budgets, approvals
              |
 ---------------------------------------------------------
 | Specialist agents (parallel workers)                  |
 ---------------------------------------------------------
              |
 [ Tool layer: crawler, browser, SERP API, GSC/GA4, PageSpeed,
   link-data provider, YouTube/Reddit APIs, CMS connectors ]
              |
 [ Data layer: Postgres (tenants, jobs, findings), object store
   (page snapshots), vector store (knowledge base), cache ]
              |
 [ Safety layer: URL safety / SSRF guard, sandbox, secrets,
   rate limiter, audit log ]
```

### 8.2 Agents (start with these)

| Agent | Job | Replaces (human role) |
|---|---|---|
| Intake agent | Collects niche, goals, competitors, site access | SEO account manager |
| Technical audit agent | Crawl, indexation, speed, schema, links | Technical SEO specialist |
| Content/keyword agent | Keyword research, briefs, on-page optimization by category | Content strategist, SEO writer |
| Competitor agent | SERP and top-10 teardown, gap matrix, hypotheses | SEO analyst |
| Link/authority agent | Backlink gaps, outreach targets, link quality | Link builder |
| AI-visibility agent | Prompt sets, multi-engine sampling, citation tracking | New role (GEO specialist) |
| Research Radar agent | Tracks research, updates, new tools; feeds the knowledge base | SEO researcher |
| Reporting agent | Builds the report, executive summary, action queue | SEO reporting analyst |
| Execution agent (later) | Applies approved changes through CMS | SEO executor / web editor |
| Orchestrator | Plans, parallelizes, enforces budgets and approvals | SEO lead |

### 8.3 Design decisions
- **Tiered model routing.** Deterministic checks first (cost $0), a small model next, the strongest model only for judgment calls. `seo-agent` documents this pattern with real per-URL costs.
- **Resumable jobs with saved state.** `seo-agent` writes results incrementally, so a crash at URL 47 restarts at 48. Copy the idea, but use a real database and job queue for multi-tenant use.
- **No model fine-tuning to start.** Knowledge goes into a retrieval index with source links and dates. Playbooks and prompts carry the logic.
- **Evals are part of the product.** Build a test set of real sites with known problems. Track precision of findings, false alarms, cost per report, and variance between runs.
- **Human-in-the-loop by default.** Same pattern as `seo-agent`'s pauses and Frase's autonomy dial. Let the customer choose the autonomy level per action type.
- **Server-side browsing.** `seo-agent` runs a visible browser and says it is not built for server CI. Plan for headless, containerized browsing with an SSRF guard (claude-seo's history shows why).

---

## 9. Data sources, legality and risk

| Need | Preferred source | Watch-outs |
|---|---|---|
| Real search performance | Google Search Console API (customer-authorized) | Per-property OAuth, data limits |
| Traffic | Google Analytics API | Consent and privacy rules |
| Page speed | PageSpeed Insights API | Rate limits |
| SERP data | Licensed SERP API (SerpApi, SearchApi and similar) | Scraping Google directly breaks its terms; use a provider **[verify provider terms]** |
| AI engine answers | Provider APIs or an answer-engine API such as SearchApi, as `seo-agent` does | Results differ by engine, vary run to run, and individual calls can fail (the author saw 503s and timeouts) |
| Backlinks | Licensed link index (Ahrefs, Semrush, others) or Open PageRank-type free sources | Model-estimated link scores are not authority scores |
| Articles/research | RSS, official feeds, sitemaps, publisher APIs | Respect robots.txt and terms; store summaries and links only |
| Videos | YouTube Data API | Transcript access and reuse limits **[verify]** |
| Community data | Official Reddit API | Commercial-use terms **[verify]** |
| Tool/model updates | GitHub API, Hugging Face API | Treat all third-party code as untrusted |

**Legal and commercial checklist before you license this to others**
1. Confirm the license of any open-source code you reuse (`seo-agent` is MIT; `claude-seo` I did not verify).
2. Get a legal review of scraping and data-use terms per source. I am not a lawyer, and this report is not legal advice.
3. Decide data ownership and retention for customer data (GSC tokens, analytics).
4. Privacy and compliance: consent-aware analytics for the EU, data-processing terms for customers.
5. Do not claim "ranks #1" or guaranteed results. Sell process, evidence and time saved.

**Key technical risks:** SSRF and malicious pages, prompt injection from crawled pages, runaway cost, rate limits, model drift, wrong advice delivered with confidence.

---

## 10. "The work of 10 SEO employees": how far is that realistic?

**[my analysis]** Agents can take over most of the repeatable, data-heavy work. They cannot replace judgment and relationships fully.

| Human role | Share an agent can plausibly do | Still needs a human |
|---|---|---|
| Technical SEO | High (audits, fix lists) | Fix approval, dev coordination |
| SEO analyst / reporting | High | Interpretation for business context |
| Keyword/content research | High | Brand voice, expertise, final editing |
| SEO writer | Medium | Original experience and expertise, which search quality guidance rewards |
| Link builder | Low to medium | Relationships and outreach replies |
| SEO lead / strategist | Low to medium | Prioritization against business goals |

A realistic claim is **"cuts the SEO workload of a team by a large share and lets 2 to 3 people do what took 10"**, which you then prove with a time-and-cost study on your own company. Measure it: hours per audit, per report, per brief, before and after. Those numbers become your sales case.

---

## 11. Business scope

### 11.1 Revenue models
1. **SaaS subscription** by number of sites/domains, with usage caps for AI-heavy features.
2. **Usage-based credits** for deep reports and AI-visibility sampling (matches your cost structure).
3. **Agency and white-label plan:** multi-client dashboard, branded reports.
4. **Self-hosted / private license** for enterprises (annual license + support).
5. **API/MCP access** for other tools and automation platforms.

### 11.2 Price anchors from the sources
Content tools $38–$165 per month; Surfer $79–$999; Semrush AI toolkit $99 per domain; Ahrefs Lite $129; one reviewer's full Ahrefs AI stack at $828–$927 per month; Profound enterprise-priced. A product that replaces 3 to 4 of these at one price has room between the bottom and the top. Set the actual price only after you know your cost per report.

### 11.3 Unit economics: what is known and what is not
- **Known:** `seo-agent` reports about $0.006 per URL at the stronger model tier and about $0.0001 at the cheap tier for its simple checks.
- **Not known:** the cost of a deep competitor report (browser sessions, SERP API calls, multi-engine sampling, many model calls). I have no benchmark for that. **Measure it in the MVP** and set plan limits from real numbers, with a safety margin.

### 11.3b Go-to-market
1. Use it internally for 2 to 3 months, record hours saved and ranking/traffic effects.
2. Publish the results as case studies. OneLittleWeb's case-study style shows how agencies sell this.
3. Start with agencies and SMBs that cannot afford a 4-tool stack.
4. Add enterprise licensing after security, SSO and audit logs are in place.

### 11.4 Defensibility (what would be hard to copy)
- The evidence-graded indicator registry and the validated weights.
- A history of measured experiments across customers (if their terms allow aggregation).
- Reliable execution and approvals (boring, but hard).
- Fresh knowledge pipeline with human curation.

**Not defensible:** prompts alone, and generic "AI writing".

### 11.5 Competitive threats
Semrush and Ahrefs bolting on agents, Frase's content-OS direction, AI-native visibility vendors, Google changing search again, and open-source packs like claude-seo lowering the entry barrier for DIY users.

---

## 12. Roadmap (rough, for a small team; estimates are mine)

| Phase | Weeks | Deliverables |
|---|---|---|
| 0. Decisions | 1–2 | Target customer, success metrics, indicator registry v0, eval set of 15–20 real sites |
| 1. Audit MVP | 3–8 | Crawler + audit agent, GSC integration, report builder, job queue, cost tracking, human approvals |
| 2. Competitor and SERP | 9–14 | Competitor discovery, top-10 teardown, gap matrix, hypotheses with evidence grades |
| 3. AI visibility | 12–18 | Multi-engine sampling with confidence ranges, GEO checks, citation reports |
| 4. Radar and admin | 16–22 | Research Radar, Update Radar with security review, admin panel |
| 5. Productization | 20–30 | Multi-tenant, billing, white-label, SSO/audit logs, licensing, docs |

**Team guess:** 1 senior backend/agent engineer, 1 full-stack engineer, 1 SEO domain expert (essential, since agents without a domain reviewer produce plausible but wrong advice), part-time design and security review.

---

## 13. Success metrics
- **Quality:** precision of findings vs expert review; false-alarm rate; run-to-run variance.
- **Impact:** change in clicks, impressions and AI citation for pages the agent changed vs control pages.
- **Efficiency:** hours saved per audit, per brief, per report; cost per report.
- **Reliability:** job success rate, resume success, API failure handling.
- **Business:** trial-to-paid conversion, churn, gross margin per plan.

---

## 14. Open questions I need you to answer
1. Who is the first customer: your own company's site(s), or client sites?
2. Which markets and languages matter first?
3. Do you plan to use paid data providers (link index, SERP API), or free sources only?
4. What is the team size and the budget for the first 6 months?
5. How much autonomy are you willing to give the agent on live sites?
6. Is the product a SaaS, a self-hosted package, or both?

---

## 15. Sources (all opened or returned by search in this session)

**From your file**
- OneLittleWeb, "10 Best SEO Content Optimization Tools in 2026": https://onelittleweb.com/top-tools/best-seo-content-optimization-tools/
- Frase, "The 10 Best SEO Content Platforms in 2026": https://www.frase.io/blog/best-seo-content-platforms
- dannwaneri/seo-agent: https://github.com/dannwaneri/seo-agent
- AgriciDaniel/claude-seo release notes: https://github.com/AgriciDaniel/claude-seo/releases/tag/v2.3.1 (also v2.2.5, v2.2.6, v2.2.0, v2.0.0, v1.9.9 under the same releases path)

**Market size**
- 360iResearch via Research and Markets: https://www.researchandmarkets.com/report/seo-software
- 360iResearch (other edition) via GII: https://www.gii.tw/report/ires2098922-seo-software-market-global-forecast.html and https://www.gii.tw/report/ires2004162-seo-software-market-by-component-deployment.html
- Coherent Market Insights: https://www.coherentmarketinsights.com/ko/통찰력/검색엔진최적화SEO소프트웨어및도구시장-9988/분할
- SkyQuest via GII Japan: https://www.gii.co.jp/report/sky1945742-seo-software-market-size-share-growth-analysis-by.html
- SEOWorks UK SEO Industry Report 2026 (Mordor figures): https://www.seoworks.co.uk/downloads/uk-seo-industry-market-report-2026/

**AI search impact**
- Seer Interactive: https://www.seerinteractive.com/news/fast-company-featured-ai-search-study-from-seer-interactive
- SEO Discovery (Pew and Seer figures): https://www.seodiscovery.com/blog/ai-search-impact-on-ctr/
- Webtonic, GEO statistics (SparkToro, Ahrefs, Google I/O figures): https://www.webtonic.io/blog/generative-engine-optimization-aeo-statistics/ and https://www.webtonic.io/blog/generative-engine-optimization-statistics
- Scube Marketing (Ahrefs, Gartner, GEO paper summary): https://www.scubemarketing.com/blog/ai-seo-aeo-geo-statistics
- Wellows GEO statistics: https://wellows.com/blog/statistics/

**AI-visibility and AI-SEO tool comparisons**
- Debutify, Profound alternatives: https://debutify.com/blog/best-profound-alternatives-for-ai-search-visibility
- MRS Digital, Ahrefs vs Otterly vs Peec: https://mrs.digital/blog/best-ai-seo-tools/
- Datadab, Brand Radar vs Semrush AI Toolkit vs Profound: https://www.datadab.com/research/ahrefs-brand-radar-vs-semrush-ai-toolkit-vs-profound
- Fritz.ai, Semrush AI vs Ahrefs AI: https://fritz.ai/?p=20952
- Airefs, top AI SEO tools: https://getairefs.com/blog/ai-seo-tools/
- Whitehat SEO UK, AI SEO tools: https://whitehat-seo.co.uk/blog/ai-seo-tools

**Not yet reviewed (from your file; next candidates)**
- https://semji.com/guide/best-writing-platforms
- https://www.youtube.com/watch?v=_0wKlt1vHLY
- https://github.com/topics/seo-agent?o=desc&s=updated
- https://github.com/topics/seo-agents-github
- Repos named without URLs: `aiapplications001-art/seo-page-creator-agent`, `wfprieto/World-Class-SEO-Agent-System`, `serpapi/seo-agent`

---

## 16. Suggested next steps
1. Answer the questions in Section 14.
2. Let me review the remaining links and the three repos listed above, and add a "what to copy / what to avoid" section for each.
3. Turn Section 7.1 into a real indicator-registry file (YAML) with the first 60 to 80 checks and evidence grades.
4. Draft the orchestrator's task graph and the agent interfaces (inputs, outputs, tools, budgets).
5. Build the evaluation set before writing agent code.
