import { useState, type FormEvent } from 'react'
import { ArrowRight, BadgeCheck, CircleHelp, Compass, Globe2, MapPin, Search, Target } from 'lucide-react'

type Mode='keywords'|'serp'|'local'|'grid'|'backlinks'
type Result=Record<string,any>
const modes:{id:Mode;label:string;detail:string;icon:typeof Search}[]=[
  {id:'keywords',label:'Keyword ideas',detail:'Provider estimates with location targeting',icon:Search},
  {id:'serp',label:'Organic competitors',detail:'Live organic search results and SERP features',icon:Target},
  {id:'local',label:'Local map results',detail:'Business listings around a selected market',icon:MapPin},
  {id:'grid',label:'Local rank grid',detail:'Map visibility sampled across coordinate points',icon:Compass},
  {id:'backlinks',label:'Backlink profile',detail:'Referring domains and sample links',icon:Globe2},
]

export default function SearchResearchWorkspace(){
  const [mode,setMode]=useState<Mode>('keywords')
  const [keyword,setKeyword]=useState('')
  const [location,setLocation]=useState('United States')
  const [language,setLanguage]=useState('English')
  const [domain,setDomain]=useState('')
  const [latitude,setLatitude]=useState('')
  const [longitude,setLongitude]=useState('')
  const [radius,setRadius]=useState('5')
  const [gridSize,setGridSize]=useState('3')
  const [result,setResult]=useState<Result|null>(null)
  const [error,setError]=useState('')
  const [busy,setBusy]=useState(false)

  const run=async(event:FormEvent)=>{
    event.preventDefault();setBusy(true);setError('');setResult(null)
    let path='/api/research/keywords', body:Record<string,unknown>={seeds:keyword.split(/[\n,;]/).map(x=>x.trim()).filter(Boolean),location,language,limit:50}
    if(mode==='serp'){path='/api/research/serp';body={keyword,location,language}}
    if(mode==='local'){path='/api/research/local-maps';body={keyword,location,language,...(latitude&&longitude?{latitude:Number(latitude),longitude:Number(longitude)}:{})}}
    if(mode==='grid'){path='/api/research/geo-grid';body={keyword,business_domain:domain.replace(/^https?:\/\//i,'').replace(/\/$/,''),latitude:Number(latitude),longitude:Number(longitude),radius_km:Number(radius),grid_size:Number(gridSize),language}}
    if(mode==='backlinks'){path='/api/research/backlinks';body={target:domain,limit:50}}
    try{const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await response.json();if(!response.ok)throw new Error(data.detail||'Research request failed.');setResult(data)}catch(err){setError(err instanceof Error?err.message:'Could not run provider query.')}finally{setBusy(false)}
  }

  return <div className="workspace-page research-page">
    <div className="page-heading"><div><div className="section-eyebrow">SEARCH RESEARCH</div><h1>Find opportunities in the market.</h1><p>Use location-aware keyword estimates, live SERPs and local map observations. Provider results are not owned-site performance data.</p></div><div className="provider-ready"><i/> DataForSEO connector</div></div>
    <div className="research-layout">
      <aside className="research-menu">{modes.map(({id,label,detail,icon:Icon})=><button key={id} className={mode===id?'active':''} onClick={()=>{setMode(id);setResult(null);setError('')}}><span className="research-menu-icon"><Icon size={18}/></span><span><b>{label}</b><small>{detail}</small></span><ArrowRight size={15}/></button>)}<div className="provider-usage-note"><CircleHelp size={17}/><p>Live queries are submitted only when you press the run button. DataForSEO may charge each keyword, SERP or map request.</p></div></aside>
      <section className="research-main-card">
        <div className="research-form-heading"><div className="research-form-icon">{mode==='grid'?<Compass size={20}/>:mode==='local'?<MapPin size={20}/>:mode==='serp'?<Target size={20}/>:mode==='backlinks'?<Globe2 size={20}/>:<Search size={20}/>}</div><div><span className="section-eyebrow">{modes.find(x=>x.id===mode)?.label.toUpperCase()}</span><h2>{mode==='keywords'?'Expand the search topic map':mode==='serp'?'See who ranks for a query':mode==='local'?'Inspect local map results':mode==='backlinks'?'Review the backlink profile':'Measure map visibility by location'}</h2></div></div>
        <form className="research-form" onSubmit={run}>
          {mode==='keywords'?<label>Seed phrases<textarea required minLength={3} value={keyword} onChange={e=>setKeyword(e.target.value)} placeholder={'e.g. emergency plumber\nboiler repair'}/><small>Use one to ten core services, products or customer phrases, separated by commas or new lines.</small></label>:mode==='backlinks'?<label>Domain or page URL<input required minLength={3} value={domain} onChange={e=>setDomain(e.target.value)} placeholder="example.com or https://example.com/service"/><small>Use a domain to summarize its full backlink profile or a page URL for a page-level sample.</small></label>:<label>Search query<input required minLength={2} value={keyword} onChange={e=>setKeyword(e.target.value)} placeholder={mode==='local'||mode==='grid'?'emergency plumber':'best payroll software for small business'}/></label>}
          {mode!=='grid'&&mode!=='backlinks'&&<label>{mode==='local'?'Market / city':'Google search location'}<input value={location} onChange={e=>setLocation(e.target.value)} placeholder="Austin, Texas, United States" required/></label>}
          {mode==='grid'&&<><label>Business domain<input required value={domain} onChange={e=>setDomain(e.target.value)} placeholder="example.com"/><small>Listings are matched to this domain when the Maps result includes a website URL.</small></label><div className="research-input-pair"><label>Center latitude<input required type="number" step="any" min="-90" max="90" value={latitude} onChange={e=>setLatitude(e.target.value)} placeholder="30.2672"/></label><label>Center longitude<input required type="number" step="any" min="-180" max="180" value={longitude} onChange={e=>setLongitude(e.target.value)} placeholder="-97.7431"/></label></div><div className="research-input-pair"><label>Radius · km<select value={radius} onChange={e=>setRadius(e.target.value)}><option value="1">1 km</option><option value="3">3 km</option><option value="5">5 km</option><option value="10">10 km</option><option value="20">20 km</option></select></label><label>Grid size<select value={gridSize} onChange={e=>setGridSize(e.target.value)}><option value="3">3 × 3 · 9 searches</option><option value="5">5 × 5 · 25 searches</option></select></label></div></>}
          {mode==='local'&&<div className="research-input-pair"><label>Center latitude <span>optional</span><input type="number" step="any" min="-90" max="90" value={latitude} onChange={e=>setLatitude(e.target.value)} placeholder="30.2672"/></label><label>Center longitude <span>optional</span><input type="number" step="any" min="-180" max="180" value={longitude} onChange={e=>setLongitude(e.target.value)} placeholder="-97.7431"/></label></div>}
          {mode!=='grid'&&mode!=='backlinks'&&<label>Search language<input value={language} onChange={e=>setLanguage(e.target.value)} placeholder="English" required/></label>}
          {mode==='grid'&&<label>Search language<input value={language} onChange={e=>setLanguage(e.target.value)} placeholder="English" required/></label>}
          <button className="button-primary research-run" disabled={busy}>{busy?'Contacting provider…':mode==='grid'?`Run ${Number(gridSize)*Number(gridSize)}-point grid scan`:mode==='keywords'?'Get keyword ideas':mode==='local'?'Get Maps results':mode==='backlinks'?'Analyze backlink profile':'Fetch organic SERP'} <ArrowRight size={16}/></button>
          {mode==='grid'&&<div className="billable-confirm-note"><CircleHelp size={16}/><span>This will request {Number(gridSize)*Number(gridSize)} live Maps results. Each coordinate can be billed by your DataForSEO account. Review the provider cost returned with the results.</span></div>}
        </form>
        {error&&<div className="research-error"><CircleHelp size={16}/>{error}</div>}
        {result&&<ResearchResults result={result} mode={mode}/>}
      </section>
    </div>
  </div>
}

function ResearchResults({result,mode}:{result:Result;mode:Mode}){
  const rows:Result[]=result.results||result.organic_results||result.backlinks||[]
  return <section className="research-results"><div className="research-result-heading"><div><span className="section-eyebrow">LIVE PROVIDER RESPONSE</span><h3>{result.source}</h3><p>{result.note}</p></div><span className="result-source-badge"><BadgeCheck size={14}/> Real provider data</span></div>
    <div className="research-result-stats"><ResultStat label="Results" value={result.rows_returned??rows.length??result.items_returned??0}/>{result.location&&<ResultStat label="Location" value={result.location}/>}<ResultStat label="Provider cost" value={result.cost??result.total_cost??'Not returned'}/>{mode==='grid'&&<ResultStat label="Visible grid points" value={`${result.ranked_cells}/${result.nodes_requested}`}/>}{mode==='backlinks'&&Object.entries(result.metrics||{}).map(([key,value])=><ResultStat key={key} label={key.replace(/_/g,' ')} value={String(value??'—')}/>)}</div>
    {mode==='grid'?<GridResults cells={result.cells||[]}/>:rows.length?<div className="research-table-scroll"><table className="research-table"><thead><tr>{Object.keys(rows[0]).filter(key=>key!=='trend').slice(0,7).map(key=><th key={key}>{key.replace(/_/g,' ')}</th>)}</tr></thead><tbody>{rows.slice(0,100).map((row,index)=><tr key={index}>{Object.entries(row).filter(([key])=>key!=='trend').slice(0,7).map(([key,value])=><td key={key}>{Array.isArray(value)?value.join(', '):typeof value==='object'&&value!==null?JSON.stringify(value):String(value??'—')}</td>)}</tr>)}</tbody></table></div>:<div className="research-no-rows">Provider returned no result rows for this query and location.</div>}
    <small className="research-result-foot">Request time: {result.checked_at||'not supplied'} · No position, volume or local pack is inferred beyond these returned records.</small>
  </section>
}
function ResultStat({label,value}:{label:string;value:string|number}){return <div><small>{label}</small><b>{String(value)}</b></div>}
function GridResults({cells}:{cells:Result[]}){const size=Math.sqrt(cells.length);return <div className="geo-grid-results" style={{gridTemplateColumns:`repeat(${size},minmax(0,1fr))`}}>{cells.map((cell,index)=><article key={index} className={cell.business_rank?'found':'not-found'}><span>{cell.business_rank?`#${cell.business_rank}`:'—'}</span><b>{cell.business_rank?'Visible':'Not in results'}</b><small>{Number(cell.latitude).toFixed(4)}, {Number(cell.longitude).toFixed(4)}</small></article>)}</div>}
