import { useEffect, useState, type FormEvent } from 'react'
import { Activity, ArrowRight, BarChart3, CheckCircle2, CircleHelp, Gauge, Globe2, Search, ShieldCheck, Sparkles } from 'lucide-react'

type Integration = { id: string; name: string; status: string; capabilities: string[]; setup: string }
type Payload = Record<string, unknown> | null
const today = new Date().toISOString().slice(0, 10)
const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)

export default function IntegrationsWorkspace() {
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [security, setSecurity] = useState('')
  const [pageUrl, setPageUrl] = useState('')
  const [strategy, setStrategy] = useState('mobile')
  const [keyword, setKeyword] = useState('')
  const [location, setLocation] = useState('United States')
  const [siteUrl, setSiteUrl] = useState('')
  const [sites, setSites] = useState<{site_url:string;permission:string}[]>([])
  const [property, setProperty] = useState('')
  const [startDate, setStartDate] = useState(monthAgo)
  const [endDate, setEndDate] = useState(today)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState<Payload>(null)

  useEffect(() => { fetch('/api/integrations/status').then(async r => { if (!r.ok) throw new Error('Could not load provider status'); return r.json() }).then(data => { setIntegrations(data.integrations || []); setSecurity(data.security || '') }).catch(e => setError(e.message)) }, [])
  const call = async (key: string, path: string, body?: object) => {
    setBusy(key); setError(''); setResult(null)
    try { const response = await fetch(path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : undefined); const data = await response.json(); if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`); if (key === 'sites') setSites(data.sites || []); else if (key === 'status') { setIntegrations(data.integrations || []); setSecurity(data.security || '') } else setResult(data) }
    catch (e) { setError(e instanceof Error ? e.message : 'Provider request failed') }
    finally { setBusy('') }
  }
  const run = (e: FormEvent, key: string, path: string, body: object) => { e.preventDefault(); void call(key, path, body) }

  return <div className="integration-workspace">
    <div className="welcome-row"><div><div className="eyebrow"><Activity size={13}/> DATA CONNECTIONS</div><h1>Connect search evidence</h1><p className="welcome-sub">Live provider data supports the consultant; crawl-only checks cannot reveal rankings, traffic, or conversions.</p></div><span className="read-only-pill"><ShieldCheck size={14}/> Read-only connectors</span></div>
    <section className="integration-summary"><div className="summary-orb"><Sparkles size={22}/></div><div><b>Use real data to prioritize work</b><p>Search Console reveals queries and clicks, GA4 reports visits and configured conversions, PageSpeed measures lab performance and available field data, and localized SERP research shows current search results.</p></div></section>
    <section className="integration-section"><div className="integration-section-head"><div><div className="eyebrow dark-eyebrow">AVAILABLE PROVIDERS</div><h2>Connection status</h2></div><button className="text-button" onClick={() => void call('status','/api/integrations/status')}>Refresh status <ArrowRight size={14}/></button></div>
      <div className="provider-grid">{integrations.map(provider => <article className="provider-card" key={provider.id}><div className="provider-top"><div className="provider-icon"><CheckCircle2 size={17}/></div><span className={`provider-status ${provider.status}`}>{provider.status.replace(/_/g,' ')}</span></div><h3>{provider.name}</h3><p>{provider.setup}</p><div className="provider-capabilities">{provider.capabilities.map(item => <span key={item}>{item}</span>)}</div></article>)}</div>
    </section>
    <section className="integration-section"><div className="integration-section-head"><div><div className="eyebrow dark-eyebrow">RUN A LIVE QUERY</div><h2>Research tools</h2><p>Credentials stay in the API server environment. Results below are from the requested provider.</p></div></div>
      <div className="research-grid">
        <article className="research-card"><div className="research-title"><div className="research-icon"><Gauge size={17}/></div><div><h3>PageSpeed Insights</h3><span>Lab audits + available CrUX field data</span></div></div><form onSubmit={e => run(e,'pagespeed','/api/performance/pagespeed',{url:pageUrl,strategy})}><label>Public page URL<input required type="url" placeholder="https://example.com/" value={pageUrl} onChange={e=>setPageUrl(e.target.value)}/></label><label>Device<select value={strategy} onChange={e=>setStrategy(e.target.value)}><option value="mobile">Mobile</option><option value="desktop">Desktop</option></select></label><button className="primary-button" disabled={!!busy}>{busy==='pagespeed'?'Running…':'Run PageSpeed check'} <ArrowRight size={14}/></button></form></article>
        <article className="research-card"><div className="research-title"><div className="research-icon"><Search size={17}/></div><div><h3>Localized SERP research</h3><span>DataForSEO · may incur provider charges</span></div></div><form onSubmit={e => run(e,'serp','/api/research/serp',{keyword,location,language:'English'})}><label>Search phrase<input required minLength={2} placeholder="emergency plumber" value={keyword} onChange={e=>setKeyword(e.target.value)}/></label><label>Market or location<input required placeholder="Austin, Texas" value={location} onChange={e=>setLocation(e.target.value)}/></label><button className="primary-button" disabled={!!busy}>{busy==='serp'?'Researching…':'Fetch live results'} <ArrowRight size={14}/></button></form></article>
        <article className="research-card"><div className="research-title"><div className="research-icon"><Globe2 size={17}/></div><div><h3>Search Console queries</h3><span>Verified property · clicks, impressions and position</span></div></div><div className="inline-actions"><button className="quiet-button" disabled={!!busy} onClick={()=>void call('sites','/api/integrations/search-console/sites')}>{busy==='sites'?'Loading…':'Load verified properties'}</button></div>{sites.length>0&&<label className="full-label">Select property<select value={siteUrl} onChange={e=>setSiteUrl(e.target.value)}><option value="">Choose a verified property</option>{sites.map(s=><option key={s.site_url} value={s.site_url}>{s.site_url} · {s.permission}</option>)}</select></label>}<form onSubmit={e=>run(e,'gsc','/api/reports/search-console',{site_url:siteUrl,start_date:startDate,end_date:endDate,row_limit:100})}><label>Property URL<input required placeholder="https://example.com/ or sc-domain:example.com" value={siteUrl} onChange={e=>setSiteUrl(e.target.value)}/></label><DateFields startDate={startDate} setStartDate={setStartDate} endDate={endDate} setEndDate={setEndDate}/><button className="primary-button" disabled={!!busy}>{busy==='gsc'?'Loading report…':'Run Search Console report'} <ArrowRight size={14}/></button></form></article>
        <article className="research-card"><div className="research-title"><div className="research-icon"><BarChart3 size={17}/></div><div><h3>Google Analytics 4</h3><span>Sessions, users, conversions and engagement</span></div></div><form onSubmit={e=>run(e,'ga4','/api/reports/ga4',{property_id:property,start_date:startDate,end_date:endDate})}><label>Numeric GA4 property ID<input required inputMode="numeric" placeholder="123456789" value={property} onChange={e=>setProperty(e.target.value)}/></label><DateFields startDate={startDate} setStartDate={setStartDate} endDate={endDate} setEndDate={setEndDate}/><button className="primary-button" disabled={!!busy}>{busy==='ga4'?'Loading report…':'Run GA4 report'} <ArrowRight size={14}/></button></form></article>
      </div>
    </section>
    {error&&<div className="integration-error"><CircleHelp size={16}/><span>{error}</span></div>}
    {result&&<section className="provider-result"><div className="result-head"><div><div className="eyebrow dark-eyebrow">PROVIDER RESPONSE</div><h2>{String(result.source || 'Query result')}</h2></div><button className="quiet-button" onClick={()=>setResult(null)}>Dismiss</button></div><p>{String(result.note || '')}</p><ResultContent result={result}/></section>}
    <div className="integration-security"><ShieldCheck size={16}/><span>{security || 'Provider calls are read-only. No website changes or publication actions are performed.'}</span></div>
  </div>
}

function DateFields({startDate,setStartDate,endDate,setEndDate}:{startDate:string;setStartDate:(s:string)=>void;endDate:string;setEndDate:(s:string)=>void}) { return <div className="date-fields"><label>From<input type="date" value={startDate} max={endDate} onChange={e=>setStartDate(e.target.value)}/></label><label>To<input type="date" value={endDate} min={startDate} max={today} onChange={e=>setEndDate(e.target.value)}/></label></div> }
function ResultContent({result}:{result:Record<string,unknown>}) {
  const rows = (result.rows || result.organic_results || result.opportunities || []) as Record<string,unknown>[]
  const cats = result.categories as Record<string,{score?:number}> | undefined
  return <><div className="result-stats">{result.rows_returned!==undefined&&<span><b>{String(result.rows_returned)}</b> rows returned</span>}{result.items_returned!==undefined&&<span><b>{String(result.items_returned)}</b> SERP items</span>}{result.field_data_available!==undefined&&<span><b>{result.field_data_available?'Available':'Unavailable'}</b> field data</span>}{cats&&Object.entries(cats).map(([name,info])=><span key={name}><b>{info.score===undefined?'—':`${Math.round(info.score*100)}`}</b> {name}</span>)}</div>{rows.length>0?<div className="result-table-wrap"><table className="result-table"><thead><tr>{Object.keys(rows[0]).slice(0,6).map(k=><th key={k}>{k.replace(/_/g,' ')}</th>)}</tr></thead><tbody>{rows.slice(0,30).map((row,i)=><tr key={i}>{Object.values(row).slice(0,6).map((v,j)=><td key={j}>{typeof v==='object'?JSON.stringify(v):String(v ?? '—')}</td>)}</tr>)}</tbody></table></div>:<pre>{JSON.stringify(result,null,2)}</pre>}</>
}
