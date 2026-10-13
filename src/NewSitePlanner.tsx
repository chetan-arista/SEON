import { useState, type FormEvent } from 'react'
import { ArrowDownToLine, ArrowRight, BadgeCheck, BookOpen, CircleHelp, Compass, Globe2, Layers3, LoaderCircle, MapPin, Search, Sparkles, Target } from 'lucide-react'

type Blueprint = {
  blueprint_id: string; created_at: string
  business: { name: string; type: string; audience: string; market: string; services: string[]; goal: string; conversion: string; stack: string }
  competitors: { provided: string[]; status: string; note: string }
  page_map: Array<{ path: string; type: string; intent: string; reason: string }>
  service_area_gate: { status: string; message: string; service_areas?: string[]; required_unique_elements?: string[] }
  launch_requirements: string[]
  backlog: Array<{ priority: number; title: string; why: string; effort: string; confidence: string; evidence_grade: string; sources: string[] }>
  limitations: string[]
  sources: Array<{ id: string; title: string; url: string; grade: string; supports: string }>
}

const defaults = { business_name: '', business_type: 'local_service', audience: '', market: 'India · English', services: '', service_areas: '', goal: 'Generate qualified enquiries', conversion: 'Contact form submission', stack: 'Not decided', competitors: '' }

export default function NewSitePlanner() {
  const [form, setForm] = useState(defaults)
  const [blueprint, setBlueprint] = useState<Blueprint | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const field = (key: keyof typeof defaults, value: string) => setForm((state) => ({ ...state, [key]: value }))

  const generate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setLoading(true); setError(''); setBlueprint(null)
    try {
      const response = await fetch('/api/blueprints', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
        ...form,
        services: form.services.split(/[,\n]/).map((x) => x.trim()).filter(Boolean),
        service_areas: form.service_areas.split(/[,\n]/).map((x) => x.trim()).filter(Boolean),
        competitors: form.competitors.split(/[,\n]/).map((x) => x.trim()).filter(Boolean),
      }) })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not create this blueprint.')
      setBlueprint(data)
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not connect to the blueprint service.') }
    finally { setLoading(false) }
  }

  const download = () => {
    if (!blueprint) return
    const lines = [`# SEO Blueprint — ${blueprint.business.name}`, '', `Created: ${new Date(blueprint.created_at).toLocaleString()}`, '', '## Business brief', `- Type: ${blueprint.business.type}`, `- Audience: ${blueprint.business.audience}`, `- Market: ${blueprint.business.market}`, `- Goal: ${blueprint.business.goal}`, `- Conversion: ${blueprint.business.conversion}`, `- Stack: ${blueprint.business.stack}`, '', '## Proposed page map', ...blueprint.page_map.flatMap((page) => [`### ${page.path} — ${page.type}`, `Intent: ${page.intent}`, page.reason, '']), '## Launch requirements', ...blueprint.launch_requirements.map((item) => `- ${item}`), '', '## Prioritized backlog', ...blueprint.backlog.map((item) => `${item.priority}. **${item.title}** — ${item.why} (Effort ${item.effort}; evidence ${item.evidence_grade}; confidence ${item.confidence})`), '', '## Research limitations', ...blueprint.limitations.map((item) => `- ${item}`), '', '## Sources', ...blueprint.sources.map((source) => `- [${source.title}](${source.url}) — Grade ${source.grade}`)]
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${blueprint.business.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-seo-blueprint.md`; link.click(); URL.revokeObjectURL(link.href)
  }

  return <div className="planner-page">
    <div className="planner-heading"><div><div className="eyebrow"><Sparkles size={13}/> NEW WEBSITE · MODE B</div><h1>Plan for search before you build.</h1><p>Tell us what the business needs. Get a page architecture, launch requirements and a prioritized SEO backlog.</p></div><div className="planner-mode"><Compass size={15}/> Blueprint mode</div></div>
    <div className="planner-columns">
      <form className="intake-card" onSubmit={generate}>
        <div className="intake-title"><div className="step-mark">01</div><div><h2>Business intake</h2><p>Set the context before planning pages or keywords.</p></div></div>
        <label>Business or product name<input required value={form.business_name} onChange={(e) => field('business_name', e.target.value)} placeholder="e.g. Northstar Studio" maxLength={140}/></label>
        <label>Business type<select value={form.business_type} onChange={(e) => field('business_type', e.target.value)}><option value="local_service">Local or service business</option><option value="saas">Software / SaaS</option><option value="ecommerce">E-commerce</option><option value="publisher">Publisher / content site</option><option value="other">Other</option></select></label>
        <label>Who do you serve?<textarea required value={form.audience} onChange={(e) => field('audience', e.target.value)} placeholder="Audience, buyer, and the problem they need solved" maxLength={500}/></label>
        <label>Target market and language<input required value={form.market} onChange={(e) => field('market', e.target.value)} placeholder="Country/region · language(s)" maxLength={300}/></label>
        <label>Products or services<textarea value={form.services} onChange={(e) => field('services', e.target.value)} placeholder="Separate each service with a comma"/></label>
        {form.business_type === 'local_service' && <label>Real service areas<input value={form.service_areas} onChange={(e) => field('service_areas', e.target.value)} placeholder="Areas you genuinely serve, comma separated"/></label>}
        <div className="field-pair"><label>Business goal<select value={form.goal} onChange={(e) => field('goal', e.target.value)}><option>Generate qualified enquiries</option><option>Increase online sales</option><option>Grow qualified product signups</option><option>Build readership</option><option>Grow local visits and calls</option></select></label><label>Primary conversion<input required value={form.conversion} onChange={(e) => field('conversion', e.target.value)} placeholder="Purchase, demo, call…" maxLength={200}/></label></div>
        <label>Website platform or technical stack<input required value={form.stack} onChange={(e) => field('stack', e.target.value)} placeholder="Shopify, WordPress, React, not decided…" maxLength={200}/></label>
        <label>Known competitors <span className="optional-label">optional</span><textarea value={form.competitors} onChange={(e) => field('competitors', e.target.value)} placeholder="Domains or brand names, comma separated"/></label>
        {error && <div className="planner-error">{error}</div>}
        <button className="generate-button" disabled={loading}>{loading ? <><LoaderCircle className="loading-spin" size={16}/> Building blueprint…</> : <>Create SEO blueprint <ArrowRight size={16}/></>}</button>
        <div className="intake-note"><CircleHelp size={14}/> This draft uses transparent rules and official guidance. It does not invent keyword volumes or rankings.</div>
      </form>
      <div className="blueprint-output">
        {!blueprint ? <div className="empty-blueprint"><div className="empty-art"><Layers3 size={28}/><div><i/><i/><i/></div></div><div className="eyebrow dark-eyebrow">YOUR STRATEGY WORKSPACE</div><h2>Start with the business.<br/>Then design the site.</h2><p>Your plan will include a business summary, suggested page map, build requirements, and a ranked first backlog.</p><div className="output-points"><div><BadgeCheck size={15}/> Search intent mapped to page types</div><div><BadgeCheck size={15}/> CMS-aware build requirements</div><div><BadgeCheck size={15}/> Evidence sources on recommendations</div></div><div className="expert-chip-row"><span><Target size={13}/> 10 specialist review lenses</span><span><Globe2 size={13}/> Web · Commerce · Local</span></div></div> : <BlueprintView data={blueprint} download={download}/>}
      </div>
    </div>
  </div>
}

function BlueprintView({ data, download }: { data: Blueprint; download: () => void }) {
  return <div className="blueprint-result"><div className="result-head"><div><div className="eyebrow dark-eyebrow">STRATEGY DRAFT · {data.business.type.replace('_', ' ').toUpperCase()}</div><h2>{data.business.name}</h2><p>{data.business.audience} · {data.business.market}</p></div><button onClick={download} className="download-button"><ArrowDownToLine size={15}/> Export report</button></div>
    <div className="result-banner"><div><Sparkles size={15}/><b>Blueprint ready for expert review</b></div><span>Run {data.blueprint_id.slice(0, 8)} · {new Date(data.created_at).toLocaleDateString()}</span></div>
    <section className="result-section"><div className="result-section-head"><span>01</span><div><h3>Proposed site architecture</h3><p>One page per distinct audience need. Paths are starting suggestions.</p></div></div><div className="page-map">{data.page_map.map((page) => <article key={page.path}><div className="page-path">{page.path}</div><span className="page-type">{page.type}</span><b>{page.intent}</b><p>{page.reason}</p></article>)}</div></section>
    <section className="result-section"><div className="result-section-head"><span>02</span><div><h3>Build requirements</h3><p>Turn these into acceptance criteria before launch.</p></div></div><div className="requirements-list">{data.launch_requirements.map((item) => <div key={item}><BadgeCheck size={15}/>{item}</div>)}</div></section>
    <section className="result-section"><div className="result-section-head"><span>03</span><div><h3>First priorities</h3><p>Ranked by strategic dependency, not predicted rank uplift.</p></div></div><div className="backlog-list">{data.backlog.map((item) => <article key={item.priority}><div className="priority-index">{String(item.priority).padStart(2,'0')}</div><div><b>{item.title}</b><p>{item.why}</p><small>Effort {item.effort} · Confidence {item.confidence} · Evidence grade {item.evidence_grade}</small></div></article>)}</div></section>
    {data.service_area_gate.status !== 'not_applicable' && <section className="gate-box"><div className="result-section-head"><span><MapPin size={14}/></span><div><h3>Service-area page quality gate</h3><p>{data.service_area_gate.status.replace('_',' ')}</p></div></div><p>{data.service_area_gate.message}</p><div>{data.service_area_gate.required_unique_elements?.map((x) => <small key={x}>• {x}</small>)}</div></section>}
    <section className="research-box"><div><Search size={15}/><b>Research still needed</b></div><p>{data.competitors.note}</p><p>{data.limitations.map((x) => x).join(' ')}</p></section>
    <section className="sources-section"><h3><BookOpen size={14}/> Evidence registry</h3>{data.sources.map((source) => <a key={source.id} href={source.url.startsWith('http') ? source.url : undefined} target="_blank" rel="noreferrer"><span>{source.id}</span><b>{source.title}</b><small>Grade {source.grade}</small></a>)}</section>
  </div>
}
