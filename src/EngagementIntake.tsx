import { useState, type ChangeEvent, type FormEvent } from 'react'
import { ArrowDownToLine, ArrowRight, BadgeCheck, BriefcaseBusiness, Code2, FileArchive, Globe2, MapPin, Search, ShieldCheck, Sparkles, Target } from 'lucide-react'

type Scenario = 'live_site' | 'repository' | 'new_site'
type Brief = {
  client_name: string; operator_name: string; business_name: string; business_type: string; business_model: string; industry: string
  audience: string; offerings: string; location: string; service_areas: string; languages: string
  domain: string; competitors: string; search_themes: string; differentiators: string; goal: string
  conversion: string; stack: string; constraints: string; baseline: string
}
type Finding = { id: string; title: string; detail: string; severity: string; area: string; page: string; fix: string; evidence: string; status: string; grade: string }
type Report = Record<string, any>

const initial: Brief = {
  client_name: '', operator_name: '', business_name: '', business_type: 'local_service', business_model: '', industry: '', audience: '', offerings: '',
  location: '', service_areas: '', languages: 'English', domain: '', competitors: '', search_themes: '', differentiators: '',
  goal: 'Generate qualified enquiries', conversion: 'Contact form submission', stack: '', constraints: '', baseline: '',
}
const scenarios: { id: Scenario; title: string; detail: string; icon: typeof Globe2 }[] = [
  { id: 'live_site', title: 'Consult on a live website', detail: 'Crawl public pages, compare competitor references, and produce an approval queue.', icon: Globe2 },
  { id: 'repository', title: 'Review a website repository', detail: 'Upload a ZIP. Inspect source paths and return specific code-level findings.', icon: Code2 },
  { id: 'new_site', title: 'Plan a new website', detail: 'Build the information architecture and an SEO-first launch brief.', icon: BriefcaseBusiness },
]
const split = (value: string) => value.split(/[,\n]/).map((item) => item.trim()).filter(Boolean)

export default function EngagementIntake({ initialScenario = 'live_site' }: { initialScenario?: Scenario }) {
  const [scenario, setScenario] = useState<Scenario>(initialScenario)
  const [brief, setBrief] = useState(initial)
  const [archive, setArchive] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [report, setReport] = useState<Report | null>(null)
  const [findingStatus, setFindingStatus] = useState<Record<string, string>>({})
  const [toast, setToast] = useState('')
  const [step, setStep] = useState(0)
  const set = (key: keyof Brief, value: string) => setBrief((current) => ({ ...current, [key]: value }))

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError(''); setReport(null)
    const context = {
      client_name: brief.client_name, operator_name: brief.operator_name, business_name: brief.business_name,
      business_type: brief.business_type, industry: brief.industry, audience: brief.audience,
      offerings: split(brief.offerings), location: brief.location, service_areas: split(brief.service_areas),
      languages: split(brief.languages), domain: brief.domain, competitors: split(brief.competitors),
      search_themes: split(brief.search_themes), differentiators: brief.differentiators, goal: brief.goal,
      conversion: brief.conversion, stack: brief.stack, constraints: brief.constraints, baseline: brief.baseline,
    }
    try {
      let response: Response
      if (scenario === 'live_site') {
        response = await fetch('/api/crawl', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: brief.domain, max_pages: 25, business_context: context, competitor_urls: context.competitors.filter((item) => /^https?:\/\//i.test(item)).slice(0, 5) }) })
      } else if (scenario === 'repository') {
        if (!archive) throw new Error('Choose a ZIP archive of the website repository first.')
        const formData = new FormData(); formData.append('archive', archive); formData.append('business_context', JSON.stringify(context))
        response = await fetch('/api/repository/analyze', { method: 'POST', body: formData })
      } else {
        response = await fetch('/api/blueprints', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
          client_name: brief.client_name, operator_name: brief.operator_name, business_name: brief.business_name, business_type: brief.business_type, business_model: brief.business_model, audience: brief.audience,
          market: [brief.location, split(brief.languages).join(', ')].filter(Boolean).join(' · ') || 'Not specified',
          location: brief.location, languages: split(brief.languages),
          services: split(brief.offerings), service_areas: split(brief.service_areas), goal: brief.goal,
          conversion: brief.conversion, stack: brief.stack || 'Not decided', competitors: split(brief.competitors),
          industry: brief.industry, domain: brief.domain, search_themes: split(brief.search_themes),
          differentiators: brief.differentiators, constraints: brief.constraints, baseline: brief.baseline,
        }) })
      }
      const data = await response.json()
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'The analysis could not be completed.')
      setReport({ ...data, scenario, business_context: context });
      setFindingStatus(Object.fromEntries((data.findings || []).map((item: Finding) => [item.id, item.status || 'Needs approval'])))
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not reach the SEON API.') }
    finally { setBusy(false) }
  }

  const review = async (id: string, status: 'Approved' | 'Dismissed') => {
    try {
      const response = await fetch(`/api/findings/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
      if (!response.ok) throw new Error('Could not save the review state. Re-run the analysis and try again.')
      setFindingStatus((current) => ({ ...current, [id]: status })); setToast(status === 'Approved' ? 'Approved. The exact next steps are shown in this report.' : 'Marked not relevant.')
      window.setTimeout(() => setToast(''), 3000)
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not save this review.') }
  }

  const download = () => {
    if (!report) return
    const text = JSON.stringify({ ...report, finding_status: findingStatus }, null, 2)
    const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([text], { type: 'application/json' })); link.download = `seon-${scenario}-report.json`; link.click(); URL.revokeObjectURL(link.href)
  }

  return <div className="engagement-page">
    <header className="engagement-heading"><div><div className="eyebrow"><Sparkles size={13}/> CONSULTANT WORKSPACE · PART 1</div><h1>Start with the business context.</h1><p>Give every SEO review the client and operator brief it needs before it analyzes a site, repository, or new build.</p></div><div className="engagement-private"><ShieldCheck size={15}/> No credentials or passwords here</div></header>
    <div className="scenario-grid">{scenarios.map(({ id, title, detail, icon: Icon }) => <button type="button" key={id} onClick={() => { setScenario(id); setStep(0); setReport(null); setError('') }} className={`scenario-card ${scenario === id ? 'scenario-selected' : ''}`}><span className="scenario-icon"><Icon size={19}/></span><b>{title}</b><small>{detail}</small><span className="scenario-arrow"><ArrowRight size={15}/></span></button>)}</div>
    <div className="engagement-layout">
      <form className="engagement-form" onSubmit={submit}>
        <div className="engagement-form-head"><div><div className="step-mark">0{step + 1}</div></div><div><h2>{['Business profile', 'Market and search', 'Goals and implementation'][step]}</h2><p>{['Tell the review what the business offers and who it serves.', 'Set the real market, competitors, and search evidence.', 'Choose the outcome and provide the site or project to review.'][step]}</p></div></div>
        <div className="intake-stepper" aria-label={`Step ${step + 1} of 3`}>{['Business', 'Market', 'Review setup'].map((label, index) => <div key={label} className={`intake-step ${index === step ? 'step-active' : ''} ${index < step ? 'step-done' : ''}`}><span>{index < step ? '✓' : `0${index + 1}`}</span><b>{label}</b></div>)}</div>
        {step === 0 && <>
        <div className="intake-section-title"><span>PEOPLE & BUSINESS</span><i/></div>
        <div className="engagement-pair"><label>Client / organization name<input value={brief.client_name} onChange={(e) => set('client_name', e.target.value)} placeholder="Who commissioned this work?"/></label><label>Operator / consultant<input value={brief.operator_name} onChange={(e) => set('operator_name', e.target.value)} placeholder="Who is running this review?"/></label></div>
        <div className="engagement-pair"><label>Business / brand name<input required value={brief.business_name} onChange={(e) => set('business_name', e.target.value)} placeholder="Public-facing brand"/></label><label>Category<select value={brief.business_type} onChange={(e) => set('business_type', e.target.value)}><option value="local_service">Local or service business</option><option value="saas">Software / SaaS</option><option value="ecommerce">E-commerce / retail</option><option value="publisher">Publisher / content</option><option value="other">Other</option></select></label></div>
        <label>Industry / niche<input required value={brief.industry} onChange={(e) => set('industry', e.target.value)} placeholder="e.g. residential HVAC, B2B payroll software"/></label>
        <label>Business model <span className="optional-label">optional</span><input value={brief.business_model} onChange={(e) => set('business_model', e.target.value)} placeholder="B2B, direct-to-consumer, subscription, local lead generation…"/></label>
        <label>Products or services<textarea required value={brief.offerings} onChange={(e) => set('offerings', e.target.value)} placeholder="What is actually sold? Include priority services/products; separate with commas."/></label>
        <label>Ideal customer and need<textarea required value={brief.audience} onChange={(e) => set('audience', e.target.value)} placeholder="Who decides, what problem do they have, and what matters when choosing?"/></label>
        </>}
        {step === 1 && <>
        <div className="intake-section-title"><span>MARKET & SEARCH CONTEXT</span><i/></div>
        <div className="engagement-pair"><label><MapPin size={13}/> Primary market / location<input required value={brief.location} onChange={(e) => set('location', e.target.value)} placeholder="City, region, country or target market"/></label><label>Languages<input value={brief.languages} onChange={(e) => set('languages', e.target.value)} placeholder="English, Hindi"/></label></div>
        {brief.business_type === 'local_service' && <label>Real service areas<input value={brief.service_areas} onChange={(e) => set('service_areas', e.target.value)} placeholder="Only areas the business genuinely serves"/></label>}
        <label>Known competitors <span className="optional-label">brand names or URLs, comma separated</span><textarea value={brief.competitors} onChange={(e) => set('competitors', e.target.value)} placeholder="These are client-provided leads; we label them as unverified until observed."/></label>
        <label>Known search themes / customer phrases<textarea value={brief.search_themes} onChange={(e) => set('search_themes', e.target.value)} placeholder="Queries heard from customers, Search Console, sales calls, or keyword research. No search volume is inferred."/></label>
        <label>Why should customers choose this business?<textarea value={brief.differentiators} onChange={(e) => set('differentiators', e.target.value)} placeholder="First-hand experience, credentials, locations, proof, delivery or product differences."/></label>
        </>}
        {step === 2 && <>
        <div className="intake-section-title"><span>GOAL, PLATFORM & BASELINE</span><i/></div>
        <div className="engagement-pair"><label>Primary business goal<select value={brief.goal} onChange={(e) => set('goal', e.target.value)}><option>Generate qualified enquiries</option><option>Increase online sales</option><option>Grow qualified product signups</option><option>Build readership</option><option>Grow local visits and calls</option></select></label><label>Success conversion<input required value={brief.conversion} onChange={(e) => set('conversion', e.target.value)} placeholder="Purchase, qualified call, demo booked"/></label></div>
        <label>Known baseline or problem<textarea value={brief.baseline} onChange={(e) => set('baseline', e.target.value)} placeholder="Known ranking/traffic changes, affected pages, Search Console period, or client-reported issue. State source if known."/></label>
        <div className="engagement-pair"><label>Platform / stack<input value={brief.stack} onChange={(e) => set('stack', e.target.value)} placeholder="Shopify, WordPress, Next.js, custom"/></label><label>Constraints<textarea value={brief.constraints} onChange={(e) => set('constraints', e.target.value)} placeholder="Legal, brand, release, budget, or access constraints"/></label></div>
        {scenario === 'live_site' && <label className="scenario-specific">Website to audit<input required type="url" value={brief.domain} onChange={(e) => set('domain', e.target.value)} placeholder="https://example.com"/><small>Read-only crawl; only use sites the client owns or has authorized you to review.</small></label>}
        {scenario === 'live_site' && <section className="research-box client-data-guidance"><div><ShieldCheck size={15}/><b>Client data access for the SEO report</b></div><p>Public crawl and PageSpeed can run without client Google access. To include private performance data, ask the client to grant your Google service-account email access to their Search Console property (read-only) and GA4 property (Viewer). Never ask for their Google password or ask them to send a service-account key.</p><p><b>Ask the client for:</b> the Search Console property URL, numeric GA4 property ID, access for your service-account email, reporting date range, and the conversions they consider meaningful. Keep your service-account JSON key on the API server in <code>.env</code>.</p><p><b>What the report will show:</b> Search Console clicks, impressions, CTR, and average position by query/page (plus available country/device breakdowns); GA4 users, sessions, engagement, configured conversions, and landing-page performance. It should state its date range and data sources, and flag missing data. These are read-only reports; connecting Google data does not change the client’s site.</p><p>If the client cannot grant access yet, continue with the public site audit and mark owned-site search/analytics data unavailable. Open <b>Integrations</b> to connect credentials and run these reports.</p></section>}
        {scenario === 'repository' && <label className="scenario-specific">Website source repository ZIP<input required type="file" accept=".zip,application/zip" onChange={(e: ChangeEvent<HTMLInputElement>) => setArchive(e.target.files?.[0] || null)}/><small>Upload a ZIP of source files. Exclude .env files, credentials, node_modules, build output, and private customer data. Analysis is read-only.</small></label>}
        {scenario === 'new_site' && <label className="scenario-specific">Planned domain <span className="optional-label">optional</span><input value={brief.domain} onChange={(e) => set('domain', e.target.value)} placeholder="example.com or a proposed domain"/></label>}
        </>}
        {error && <div className="planner-error">{error}</div>}
        <div className="intake-navigation">{step > 0 && <button type="button" className="button-secondary" onClick={() => setStep(step - 1)}>Back</button>}{step < 2 ? <button type="button" className="button-primary" onClick={(event) => { const form = event.currentTarget.form; if (form?.reportValidity()) setStep(step + 1) }}>Continue <ArrowRight size={15}/></button> : <button className="generate-button" disabled={busy}>{busy ? 'Analyzing business context…' : scenario === 'new_site' ? 'Create SEO-first brief' : scenario === 'repository' ? 'Analyze repository ZIP' : 'Analyze website'} <ArrowRight size={16}/></button>}</div>
        <div className="intake-note"><ShieldCheck size={14}/> Findings are recommendations. No live website or source files are changed without explicit approval.</div>
      </form>
      <section className="engagement-report">{report ? <ReportView data={report} status={findingStatus} review={review} download={download}/> : <div className="empty-blueprint"><div className="empty-art"><Search size={28}/><div><i/><i/><i/></div></div><div className="eyebrow dark-eyebrow">THE CONSULTANT BRIEF</div><h2>One intake.<br/>Three ways to work.</h2><p>Business context guides service and product themes, location relevance, competitor review, conversion priorities, and platform-specific implementation steps.</p><div className="output-points"><div><BadgeCheck size={15}/> Separate observed facts from hypotheses</div><div><BadgeCheck size={15}/> Prioritize business impact, evidence, and effort</div><div><BadgeCheck size={15}/> Show file paths or CMS locations to act</div><div><BadgeCheck size={15}/> Ask for approval before any change</div></div><div className="expert-chip-row"><span><Target size={13}/> 10 specialist review lenses</span><span><Globe2 size={13}/> Local · Commerce · SaaS · Content</span></div></div>}</section>
    </div>{toast && <div className="toast"><BadgeCheck size={17}/>{toast}</div>}
  </div>
}

function ReportView({ data, status, review, download }: { data: Report; status: Record<string, string>; review: (id: string, status: 'Approved'|'Dismissed') => void; download: () => void }) {
  const findings: Finding[] = data.findings || []
  const keywords: string[] = data.keyword_hypotheses || data.strategy_context?.keyword_hypotheses || []
  const evidence = data.pages?.length ? `${data.page_count ?? data.pages.length} pages analyzed on ${data.url || data.requested_url || 'site'}` : data.file_count ? `${data.file_count} source files reviewed · ${data.framework || 'framework not detected'}` : 'Business strategy draft'
  return <div className="engagement-result"><div className="engagement-result-head"><div><div className="eyebrow dark-eyebrow">{String(data.scenario || (data.blueprint_id ? 'new_site' : 'live_site')).replace('_',' ').toUpperCase()} · CONSULTANT OUTPUT</div><h2>{data.business_context?.business_name || data.business?.name || data.domain || data.url || 'SEO analysis'}</h2><p>{evidence}</p></div><button className="download-button" onClick={download}><ArrowDownToLine size={15}/> Export JSON</button></div>
    {(data.business_context || data.business) && <div className="brief-summary"><b>Brief used for this analysis</b><p>{[data.business_context?.client_name || data.business?.client_name, data.business_context?.operator_name || data.business?.operator_name, data.business_context?.business_model || data.business?.business_model, data.business_context?.industry || data.business?.industry || data.business?.type, data.business_context?.location || data.business?.location || data.business?.market, data.business_context?.goal || data.business?.goal, data.business_context?.conversion || data.business?.conversion].filter(Boolean).join(' · ')}</p><small>Client context is shown with findings so analysts can check relevance.</small></div>}
    {keywords.length > 0 && <section className="result-section"><div className="result-section-head"><span><Search size={14}/></span><div><h3>Location-aware topic hypotheses</h3><p>Seed ideas from the supplied services and market. Validate demand and intent before targeting.</p></div></div><div className="keyword-chips">{keywords.map((term) => <span key={term}>{term}</span>)}</div><small className="data-limit">No search volumes, difficulty, rankings, or SERP features are claimed without a connected provider.</small></section>}
    {(data.competitor_observations?.length > 0 || data.competitors?.provided?.length > 0 || data.business_context?.competitors?.length > 0) && <section className="result-section"><div className="result-section-head"><span>02</span><div><h3>{data.competitor_observations?.length ? 'Competitor observations' : 'Competitor inputs'}</h3><p>{data.competitors?.note || 'Client-provided brands/URLs are not assumed to be search competitors. Public page observation is not a ranking comparison.'}</p></div></div>{(data.competitors?.provided || data.business_context?.competitors || []).length > 0 && <div className="keyword-chips">{(data.competitors?.provided || data.business_context?.competitors || []).map((name: string) => <span key={name}>{name}</span>)}</div>}{data.competitor_observations?.map((item: any) => <article className="competitor-observation" key={item.url}><b>{item.domain || item.url}</b><span>{item.title || 'Title unavailable'} · H1: {item.h1 || 'not found'} · HTTP {item.status_code ?? '—'}</span><small>{item.note || ''}</small></article>)}</section>}
    {data.page_map?.length > 0 && <section className="result-section"><div className="result-section-head"><span>01</span><div><h3>Proposed page architecture</h3><p>One useful page per distinct intent; path proposals need business review.</p></div></div><div className="page-map">{data.page_map.map((page: any) => <article key={page.path}><div className="page-path">{page.path}</div><span className="page-type">{page.type}</span><b>{page.intent}</b><p>{page.reason}</p></article>)}</div></section>}
    {data.findings && <section className="result-section"><div className="result-section-head"><span>03</span><div><h3>Evidence and recommendations</h3><p>Review each item. Approval records your decision and implementation guidance.</p></div></div><div className="consult-finding-list">{findings.map((f) => <article key={f.id} className="consult-finding"><div className="consult-finding-title"><b>{f.title}</b><span>{f.severity}</span></div><p>{f.detail}</p><small><Code2 size={12}/> {f.page} · Evidence grade {f.grade || 'B'}</small><div className="consult-evidence">Observed: {f.evidence}</div><div className="consult-fix"><b>Recommended:</b> {f.fix}</div>{status[f.id] === 'Approved' && <div className="approved-path"><b>Next steps:</b> Review this exact page or source path, apply the recommendation in a draft/staging branch, preview the result, rerun the analysis, and keep a rollback copy. SEON does not publish the change in this release.</div>}<div className="consult-review"><span>Status: {status[f.id] || f.status}</span>{(status[f.id] || f.status) === 'Needs approval' && <><button onClick={() => review(f.id, 'Dismissed')}>Not relevant</button><button onClick={() => review(f.id, 'Approved')}>Approve steps</button></>}</div></article>)}</div></section>}
    {data.backlog?.length > 0 && <section className="result-section"><div className="result-section-head"><span>02</span><div><h3>Prioritized launch backlog</h3><p>Strategic prerequisites, not a promise of search results.</p></div></div><div className="backlog-list">{data.backlog.map((item: any) => <article key={item.priority}><div className="priority-index">{String(item.priority).padStart(2,'0')}</div><div><b>{item.title}</b><p>{item.why}</p><small>Effort {item.effort} · Confidence {item.confidence} · Evidence grade {item.evidence_grade}</small></div></article>)}</div></section>}
    {data.framework_findings?.length > 0 && <section className="result-section"><div className="result-section-head"><span><FileArchive size={14}/></span><div><h3>Repository context</h3><p>Static source analysis may miss generated, CMS, or JavaScript-rendered behavior.</p></div></div><div className="requirements-list">{data.framework_findings.map((line: string) => <div key={line}><Code2 size={14}/>{line}</div>)}</div></section>}
    {data.limitations?.length > 0 && <section className="research-box"><div><ShieldCheck size={15}/><b>What this analysis cannot establish</b></div>{data.limitations.map((line: string) => <p key={line}>{line}</p>)}</section>}
    {data.sources?.length > 0 && <section className="sources-section"><h3>Research sources</h3>{data.sources.map((source: any) => <a key={source.id} href={source.url} target="_blank" rel="noreferrer"><span>{source.id}</span><b>{source.title}</b><small>Grade {source.grade}</small></a>)}</section>}
  </div>
}
