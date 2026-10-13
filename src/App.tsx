import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Activity, ArrowDownToLine, ArrowRight, BadgeCheck, BarChart3, BriefcaseBusiness, Check, ChevronDown, ChevronLeft, ChevronRight, CircleHelp, ClipboardList, Code2, Compass, FileSearch, Globe2, LayoutDashboard, Link2, ListChecks, LockKeyhole, LogOut, Menu, Plus, Search, ShieldCheck, Sparkles, Target, UsersRound, Workflow, X } from 'lucide-react'
import EngagementIntake from './EngagementIntake'
import IntegrationsWorkspace from './IntegrationsWorkspace'
import SearchResearchWorkspace from './SearchResearchWorkspace'
import ClientInputGuide from './ClientInputGuide'
import AuthScreen, { type AuthUser } from './AuthScreen'

type Finding = { id:string; title:string; detail:string; severity:string; area:string; grade:string; page:string; fix:string; evidence:string; status:string }
type AuditRun = { id:string; kind:string; url:string; created_at:string; finding_count:number; score?:number }
type RunDetail = { run_id:string; url:string; created_at:string; kind?:string; health_score?:number; page_count?:number; findings:Finding[]; pages?:unknown[]; [key:string]:any }
type NavItem = { label:string; icon:typeof LayoutDashboard; group:'WORKSPACE'|'RESEARCH'|'TOOLS' }

const navItems: NavItem[] = [
  { label:'Overview', icon:LayoutDashboard, group:'WORKSPACE' },
  { label:'New engagement', icon:Plus, group:'WORKSPACE' },
  { label:'Website audits', icon:FileSearch, group:'WORKSPACE' },
  { label:'Action queue', icon:ListChecks, group:'WORKSPACE' },
  { label:'Keyword & competitors', icon:Target, group:'RESEARCH' },
  { label:'New-site strategy', icon:Compass, group:'RESEARCH' },
  { label:'Reports', icon:BarChart3, group:'RESEARCH' },
  { label:'Integrations', icon:Link2, group:'TOOLS' },
  { label:'Client input guide', icon:ClipboardList, group:'TOOLS' },
  { label:'User access', icon:UsersRound, group:'TOOLS' },
  { label:'Development', icon:Code2, group:'TOOLS' },
]

function App() {
  const [activeNav,setActiveNav] = useState('Overview')
  const [user,setUser] = useState<AuthUser|null>(null)
  const [authLoading,setAuthLoading] = useState(true)
  const [mobileOpen,setMobileOpen] = useState(false)
  const [sidebarCollapsed,setSidebarCollapsed] = useState(()=>localStorage.getItem('seon-sidebar-collapsed')==='true')
  const [collapsedNavGroups,setCollapsedNavGroups] = useState<Record<string,boolean>>(()=>{
    try { return JSON.parse(localStorage.getItem('seon-collapsed-nav-groups')||'{}') as Record<string,boolean> }
    catch { return {} }
  })
  const [runs,setRuns] = useState<AuditRun[]>([])
  const [details,setDetails] = useState<RunDetail[]>([])
  const [selectedRun,setSelectedRun] = useState<RunDetail|null>(null)
  const [auditUrl,setAuditUrl] = useState('')
  const [auditBusy,setAuditBusy] = useState(false)
  const [auditError,setAuditError] = useState('')
  const [loadError,setLoadError] = useState('')
  const [toast,setToast] = useState('')
  const [filter,setFilter] = useState('Needs approval')

  const refresh = useCallback(async () => {
    setLoadError('')
    try {
      const response = await fetch('/api/runs')
      if (!response.ok) throw new Error('Audit history is unavailable. Check that the API is running.')
      const data = await response.json()
      const nextRuns: AuditRun[] = data.runs || []
      setRuns(nextRuns)
      const loaded = await Promise.all(nextRuns.slice(0,12).map(async run => {
        const r = await fetch(`/api/runs/${run.id}`)
        return r.ok ? await r.json() as RunDetail : null
      }))
      const nextDetails = loaded.filter((x): x is RunDetail => Boolean(x))
      setDetails(nextDetails)
      setSelectedRun(current => current ? nextDetails.find(x=>x.run_id===current.run_id) || nextDetails[0] || null : nextDetails[0] || null)
    } catch (error) { setLoadError(error instanceof Error ? error.message : 'Could not load audit history.') }
  },[])

  useEffect(() => { fetch('/api/auth/me').then(async response => { if(!response.ok) return null; const data=await response.json(); return data.user as AuthUser }).then(current=>setUser(current)).catch(()=>setUser(null)).finally(()=>setAuthLoading(false)) },[])
  useEffect(() => { if(user?.role==='client'&&activeNav==='Overview') setActiveNav('Website audits') },[user,activeNav])
  useEffect(() => { if(user) void refresh() },[refresh,activeNav,user])
  const allFindings = useMemo(() => details.flatMap(run => run.findings.map(f => ({...f,run_id:run.run_id,site:safeHostname(run.url),run_date:run.created_at}))),[details])
  const pending = allFindings.filter(f=>f.status==='Needs approval')
  const reviewed = allFindings.filter(f=>f.status==='Approved')
  const toggleNavGroup = (group:string) => setCollapsedNavGroups(current=>{
    const next={...current,[group]:!current[group]}
    localStorage.setItem('seon-collapsed-nav-groups',JSON.stringify(next))
    return next
  })

  const runAudit = async (event:FormEvent) => {
    event.preventDefault(); setAuditBusy(true); setAuditError('')
    try {
      const response=await fetch('/api/crawl',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:auditUrl.trim(),max_pages:25})})
      const data=await response.json()
      if(!response.ok) throw new Error(data.detail||'The audit could not be completed.')
      await refresh(); setActiveNav('Website audits'); setToast(`Audit saved: ${data.page_count || 0} pages checked`); window.setTimeout(()=>setToast(''),4000)
    } catch(error) { setAuditError(error instanceof Error?error.message:'Audit request failed.') }
    finally { setAuditBusy(false) }
  }

  const updateFinding = async (id:string,status:'Approved'|'Dismissed') => {
    try {
      const response=await fetch(`/api/findings/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})})
      const data=await response.json()
      if(!response.ok) throw new Error(data.detail||'Could not save this review.')
      setDetails(current=>current.map(run=>({...run,findings:run.findings.map(f=>f.id===id?data:f)})))
      setToast(status==='Approved'?'Approved for implementation planning. No website change was made.':'Recommendation dismissed.')
      window.setTimeout(()=>setToast(''),4000)
    } catch(error) { setToast(error instanceof Error?error.message:'Could not save review.'); window.setTimeout(()=>setToast(''),4000) }
  }

  const exportRun=(run:RunDetail)=>{
    const site=safeHostname(run.url)
    const body=[`# SEO review — ${site}`,'',`Date: ${new Date(run.created_at).toLocaleString()}`,`Pages checked: ${run.page_count ?? '—'}`,`Heuristic checks: ${run.health_score ?? '—'}/100`,'','## Findings',...run.findings.map((f,i)=>`### ${i+1}. ${f.title}\n- Status: ${f.status}\n- Priority: ${f.severity}\n- Page: ${f.page}\n- Evidence: ${f.evidence}\n- Recommendation: ${f.fix}\n`),'','Observations describe the crawl snapshot and do not guarantee ranking outcomes.']
    const link=document.createElement('a'); link.href=URL.createObjectURL(new Blob([body.join('\n')],{type:'text/markdown'})); link.download=`${site}-seo-review.md`; link.click(); URL.revokeObjectURL(link.href)
  }

  const logout=async()=>{try{await fetch('/api/auth/logout',{method:'POST'})}finally{setUser(null);setRuns([]);setDetails([]);setActiveNav('Overview')}}
  if(authLoading) return <div className="auth-loading"><span className="auth-mark"><i/><i/><i/></span><b>Loading SEON workspace…</b></div>
  if(!user) return <AuthScreen onAuthed={setUser}/>

  const visibleNav = navItems.filter(item => user.role === 'client' ? item.label === 'Website audits' : user.role === 'admin' ? true : item.label !== 'User access' && item.label !== 'Development')
  const groups=['WORKSPACE','RESEARCH','TOOLS'] as const
  return <div className={`workspace-shell ${sidebarCollapsed?'is-sidebar-collapsed':''}`}>
    <aside className={`workspace-sidebar ${mobileOpen?'is-open':''} ${sidebarCollapsed?'is-collapsed':''}`}>
      <div className="workspace-brand"><div className="brand-symbol"><span/></div><span className="brand-wordmark">seon<span className="brand-period">.</span></span><span className="brand-caption">CONSULTANT</span><button className="sidebar-collapse-toggle" onClick={()=>setSidebarCollapsed(current=>{const next=!current;localStorage.setItem('seon-sidebar-collapsed',String(next));return next})} aria-label={sidebarCollapsed?'Expand sidebar':'Collapse sidebar'} aria-expanded={!sidebarCollapsed} title={sidebarCollapsed?'Expand sidebar':'Collapse sidebar'}>{sidebarCollapsed?<ChevronRight size={17}/>:<ChevronLeft size={17}/>}</button></div>
      <div className="sidebar-workspace"><div className="workspace-avatar">{(user.display_name||user.email).slice(0,1).toUpperCase()}</div><div><b>{user.role==='client'?'Client workspace':'SEON workspace'}</b><small>{user.role} · {user.email}</small></div><ChevronRight size={16}/></div>
      {groups.map(group=><div className={`nav-group ${collapsedNavGroups[group]?'is-group-collapsed':''}`} key={group}>{visibleNav.some(item=>item.group===group)&&<><button className="nav-group-toggle" title={sidebarCollapsed?`${group} section`:undefined} aria-expanded={!collapsedNavGroups[group]} onClick={()=>toggleNavGroup(group)}><span>{group}</span><ChevronDown size={14}/></button>{!collapsedNavGroups[group]&&visibleNav.filter(item=>item.group===group).map(({label,icon:Icon})=><button key={label} title={sidebarCollapsed?label:undefined} onClick={()=>{setActiveNav(label);setMobileOpen(false)}} className={`workspace-nav-item ${activeNav===label?'active':''}`}><Icon size={18}/><span>{user.role==='client'&&label==='Website audits'?'Live site review':label}</span>{label==='Action queue'&&pending.length>0&&<b>{pending.length}</b>}</button>)}</>}</div>)}
      <div className="sidebar-bottom-card"><ShieldCheck size={17}/><div><b>Approval-first workflow</b><small>Reviews never publish site edits.</small></div></div>
      <button className="sidebar-logout" onClick={()=>void logout()}><LogOut size={15}/> Sign out</button><div className="sidebar-footer">SEON · {user.role} workspace</div>
    </aside>

    <main className="workspace-main">
      <header className="workspace-topbar"><div className="workspace-crumb"><button className="mobile-nav-toggle" onClick={()=>setMobileOpen(v=>!v)} aria-label="Toggle navigation"><Menu size={19}/></button><span>Workspace</span><ChevronRight size={14}/><b>{user.role==='client'&&activeNav==='Website audits'?'Live site review':activeNav}</b></div><div className="topbar-actions"><span className="role-badge"><LockKeyhole size={13}/>{user.role}</span><span className="api-indicator"><i/> Local API</span><button className="help-button" title="Sign out" onClick={()=>void logout()}><LogOut size={17}/></button></div></header>
      <div className="workspace-content">
        {loadError&&<div className="workspace-alert"><CircleHelp size={17}/>{loadError}</div>}
        {activeNav==='Overview'&&<Overview runs={runs} details={details} pending={pending.length} onNavigate={setActiveNav} onRefresh={()=>void refresh()}/>}
        {activeNav==='New engagement'&&<EngagementIntake/>}
        {activeNav==='New-site strategy'&&<EngagementIntake initialScenario="new_site"/>}
        {activeNav==='Website audits'&&<AuditWorkspace runs={runs} selectedRun={selectedRun} setSelectedRun={setSelectedRun} url={auditUrl} setUrl={setAuditUrl} onSubmit={runAudit} busy={auditBusy} error={auditError} exportRun={exportRun} onRefresh={()=>void refresh()} onNew={()=>setActiveNav('New engagement')}/>}
        {activeNav==='Action queue'&&<ActionQueue items={filter==='All' ? allFindings : filter==='Needs approval'?pending:reviewed} filter={filter} setFilter={setFilter} update={updateFinding} onNew={()=>setActiveNav('New engagement')}/>}
        {activeNav==='Keyword & competitors'&&<SearchResearchWorkspace/>}
        {activeNav==='Reports'&&<ReportsWorkspace runs={runs} details={details} exportRun={exportRun} selectRun={setSelectedRun}/>}
        {activeNav==='Integrations'&&<IntegrationsWorkspace/>}
        {activeNav==='Client input guide'&&<ClientInputGuide onStart={()=>setActiveNav('New engagement')}/>}
        {activeNav==='User access'&&user.role==='admin'&&<AdminUsersWorkspace self={user}/>}
        {activeNav==='Development'&&user.role==='admin'&&<DevelopmentWorkspace/>}
      </div>
    </main>
    {mobileOpen&&<button className="mobile-sidebar-scrim" onClick={()=>setMobileOpen(false)} aria-label="Close navigation"/>}
    {toast&&<div className="workspace-toast"><BadgeCheck size={18}/>{toast}<button onClick={()=>setToast('')} aria-label="Dismiss"><X size={15}/></button></div>}
  </div>
}

function PageHeading({eyebrow,title,description,action}:{eyebrow:string;title:string;description:string;action?:React.ReactNode}) { return <div className="page-heading"><div><div className="section-eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div> }

function Overview({runs,details,pending,onNavigate,onRefresh}:{runs:AuditRun[];details:RunDetail[];pending:number;onNavigate:(s:string)=>void;onRefresh:()=>void}) {
  const latest=details[0]
  const pages=details.reduce((total,run)=>total+(run.page_count||0),0)
  return <div className="workspace-page">
    <PageHeading eyebrow="SEO CONSULTANT" title="Search performance, with evidence." description="Audit technical foundations, validate opportunities with search data, and review every proposed change." action={<button className="button-primary" onClick={()=>onNavigate('New engagement')}><Plus size={17}/> New engagement</button>}/>
    <section className="welcome-panel"><div className="welcome-panel-copy"><div className="welcome-tag"><Sparkles size={14}/> CONSULTANT WORKFLOW</div><h2>Start with the business.<br/>Make the next move clear.</h2><p>Use a client brief, repository review, live site crawl, keyword research, Search Console and performance data to build an evidence-led plan.</p><div className="welcome-actions"><button className="button-light" onClick={()=>onNavigate('New engagement')}>Start a review <ArrowRight size={16}/></button><button className="button-quiet-light" onClick={()=>onNavigate('Integrations')}>Connect data</button></div></div><div className="workflow-steps"><div><span>01</span><div><b>Understand the business</b><small>Market, audience, offer and goals</small></div></div><div><span>02</span><div><b>Gather evidence</b><small>Site, search, competitors and speed</small></div></div><div><span>03</span><div><b>Approve the priorities</b><small>Recommendations stay reviewable</small></div></div></div></section>
    <div className="stat-grid"><StatCard label="Saved site reviews" value={runs.length} detail="Audits in this local workspace" icon={<FileSearch size={19}/>}/><StatCard label="Pages inspected" value={pages} detail="Across the recent audit history" icon={<Globe2 size={19}/>}/><StatCard label="Awaiting review" value={pending} detail="Recommendations that need a decision" icon={<ListChecks size={19}/>}/><StatCard label="Latest review" value={latest?new URL(latest.url).hostname:'Not started'} detail={latest?new Date(latest.created_at).toLocaleDateString():'Run an audit to populate this view'} icon={<Activity size={19}/>}/></div>
    <section className="content-card"><div className="card-heading"><div><span className="section-eyebrow">YOUR WORK</span><h2>Recent site reviews</h2></div><button className="button-secondary" onClick={onRefresh}>Refresh history</button></div>{runs.length?<div className="audit-list">{runs.slice(0,6).map(run=><div className="audit-list-row" key={run.id}><div className="audit-row-icon"><FileSearch size={18}/></div><div className="audit-row-main"><b>{safeHostname(run.url)}</b><span>{run.kind} · {new Date(run.created_at).toLocaleString()} · {run.finding_count} recommendations</span></div><span className="audit-score">{run.score===undefined?'—':`${run.score}/100`}</span><button className="row-link" onClick={()=>onNavigate('Website audits')}>Open <ArrowRight size={15}/></button></div>)}</div>:<EmptyState title="No website reviews yet" text="Start a client engagement to crawl an authorized site, inspect a source ZIP, or create a strategy for a new website." action={<button className="button-primary" onClick={()=>onNavigate('New engagement')}><Plus size={16}/> Create first engagement</button>}/>}</section>
    <section className="quick-tools"><button onClick={()=>onNavigate('Keyword & competitors')}><div className="quick-tool-icon"><Search size={19}/></div><b>Keyword & competitor research</b><span>Ideas, live SERPs, local results and grid checks</span><ArrowRight size={17}/></button><button onClick={()=>onNavigate('Action queue')}><div className="quick-tool-icon"><ListChecks size={19}/></div><b>Review recommendations</b><span>{pending?`${pending} findings await a decision`:'Audit findings appear here after a scan'}</span><ArrowRight size={17}/></button><button onClick={()=>onNavigate('New-site strategy')}><div className="quick-tool-icon"><Compass size={19}/></div><b>Plan a new website</b><span>Build an SEO-first page and launch strategy</span><ArrowRight size={17}/></button></section>
  </div>
}

function AuditWorkspace({runs,selectedRun,setSelectedRun,url,setUrl,onSubmit,busy,error,exportRun,onRefresh,onNew}:{runs:AuditRun[];selectedRun:RunDetail|null;setSelectedRun:(r:RunDetail)=>void;url:string;setUrl:(s:string)=>void;onSubmit:(e:FormEvent)=>void;busy:boolean;error:string;exportRun:(run:RunDetail)=>void;onRefresh:()=>void;onNew:()=>void}) {
  const [loading,setLoading]=useState(false)
  const loadRun=async(id:string)=>{setLoading(true);try{const response=await fetch(`/api/runs/${id}`);if(response.ok)setSelectedRun(await response.json())}finally{setLoading(false)}}
  return <div className="workspace-page"><PageHeading eyebrow="TECHNICAL REVIEW" title="Website audits" description="Run a read-only crawl or open a saved result. Crawl observations are diagnostic signals, not ranking guarantees." action={<button className="button-secondary" onClick={onNew}><BriefcaseBusiness size={16}/> Full client brief</button>}/>
    <section className="audit-launch-card"><div className="launch-icon"><Globe2 size={22}/></div><div className="launch-copy"><h2>Audit a public website</h2><p>Checks page metadata, headings, canonical/indexability signals, image alt attributes, robots rules and internal page discovery.</p><form className="launch-form" onSubmit={onSubmit}><input required type="url" value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://example.com" aria-label="Website URL"/><button className="button-primary" disabled={busy}>{busy?'Crawling…':'Start 25-page crawl'} <ArrowRight size={16}/></button></form>{error&&<p className="form-error">{error}</p>}<small>Only audit websites you own or have authorization to review. No website edits are made.</small></div></section>
    <div className="audit-workspace-columns"><section className="content-card"><div className="card-heading"><div><span className="section-eyebrow">SAVED HISTORY</span><h2>Audit runs</h2></div><button className="button-secondary" onClick={onRefresh}>Refresh</button></div>{runs.length?<div className="audit-list">{runs.map(run=><button className={`audit-list-row audit-select ${selectedRun?.run_id===run.id?'selected':''}`} key={run.id} onClick={()=>void loadRun(run.id)}><div className="audit-row-icon"><FileSearch size={18}/></div><div className="audit-row-main"><b>{safeHostname(run.url)}</b><span>{new Date(run.created_at).toLocaleString()} · {run.finding_count} findings</span></div><span className="audit-score">{run.score??'—'}</span></button>)}</div>:<EmptyState title="Audit history is empty" text="Run the first crawl to create an evidence-backed technical review."/>}</section>
      <section className="content-card selected-audit">{selectedRun?<><div className="card-heading"><div><span className="section-eyebrow">SELECTED REVIEW</span><h2>{safeHostname(selectedRun.url)}</h2></div><button className="button-secondary" onClick={()=>exportRun(selectedRun)}><ArrowDownToLine size={15}/> Export</button></div>{loading&&<p>Loading audit…</p>}<div className="selected-audit-metrics"><StatCard label="Pages" value={selectedRun.page_count??0} detail="In this crawl" icon={<Globe2 size={18}/>}/><StatCard label="Recommendations" value={selectedRun.findings?.length??0} detail="Observed findings" icon={<ListChecks size={18}/>}/><StatCard label="Heuristic checks" value={`${selectedRun.health_score??'—'}/100`} detail="Not a Google ranking score" icon={<Activity size={18}/>}/></div><div className="mini-findings">{selectedRun.findings?.slice(0,5).map(item=><div key={item.id}><span className={`priority-dot ${item.severity.toLowerCase()}`}/><div><b>{item.title}</b><small>{item.page} · {item.status}</small></div><ChevronRight size={15}/></div>)}</div></>:<EmptyState title="Select an audit to inspect" text="Open a saved run to review its evidence, findings and exportable report."/>}</section></div>
  </div>
}

function ActionQueue({items,filter,setFilter,update,onNew}:{items:any[];filter:string;setFilter:(s:string)=>void;update:(id:string,status:'Approved'|'Dismissed')=>void;onNew:()=>void}) {
  return <div className="workspace-page"><PageHeading eyebrow="HUMAN REVIEW" title="Action queue" description="Prioritize evidence-backed work. Approving a recommendation records your decision; it does not edit or publish your website." action={<button className="button-secondary" onClick={onNew}><Plus size={16}/> New review</button>}/><div className="queue-toolbar"><div className="queue-tabs">{['Needs approval','Approved','All'].map(item=><button className={filter===item?'selected':''} key={item} onClick={()=>setFilter(item)}>{item}</button>)}</div><span>{items.length} recommendations</span></div>{items.length?<div className="queue-list">{items.map((f:any)=><article className="queue-item" key={`${f.run_id}-${f.id}`}><div className={`priority-label ${f.severity.toLowerCase()}`}>{f.severity}</div><div className="queue-item-main"><div className="queue-item-heading"><h2>{f.title}</h2><span>{f.site}</span></div><p>{f.detail}</p><div className="queue-evidence"><b>Observed</b><span>{f.evidence}</span></div><div className="queue-fix"><b>Recommended action</b><span>{f.fix}</span></div><div className="queue-meta"><span>{f.area}</span><span>{f.page}</span><span>Evidence grade {f.grade}</span><span>{f.status}</span></div>{f.status==='Needs approval'&&<div className="queue-actions"><button className="button-secondary" onClick={()=>update(f.id,'Dismissed')}>Dismiss</button><button className="button-primary" onClick={()=>update(f.id,'Approved')}><Check size={16}/> Approve recommendation</button></div>}</div></article>)}</div>:<EmptyState title={filter==='Needs approval'?'Nothing waiting for review':'No recommendations in this view'} text="Run an authorized website crawl or repository analysis to produce client-specific findings. SEON will not invent action items." action={<button className="button-primary" onClick={onNew}><Plus size={16}/> Start a review</button>}/>}</div>
}

function ReportsWorkspace({runs,details,exportRun,selectRun}:{runs:AuditRun[];details:RunDetail[];exportRun:(run:RunDetail)=>void;selectRun:(run:RunDetail)=>void}) {
  const [selectedId,setSelectedId]=useState('')
  const selected=details.find(x=>x.run_id===selectedId)||details[0]
  return <div className="workspace-page"><PageHeading eyebrow="CLIENT DELIVERABLES" title="Reports" description="Export an audit report with page paths, observations, recommendations, evidence grades and review states."/><section className="content-card"><div className="card-heading"><div><span className="section-eyebrow">SAVED REPORTS</span><h2>Choose a completed site review</h2></div><span className="count-chip">{runs.length} stored</span></div>{runs.length?<div className="report-picker">{runs.map(run=><button className={selected?.run_id===run.id?'selected':''} key={run.id} onClick={()=>{setSelectedId(run.id);const found=details.find(d=>d.run_id===run.id);if(found)selectRun(found)}}><span className="audit-row-icon"><FileSearch size={18}/></span><span><b>{safeHostname(run.url)}</b><small>{new Date(run.created_at).toLocaleString()} · {run.finding_count} findings</small></span><ChevronRight size={16}/></button>)}</div>:<EmptyState title="No reports to export" text="Run a site audit first. The finished review will appear here."/>}{selected&&<div className="report-preview"><div><h3>{safeHostname(selected.url)}</h3><p>{selected.page_count??0} pages · {selected.findings?.length??0} findings · Run {new Date(selected.created_at).toLocaleString()}</p></div><button className="button-primary" onClick={()=>exportRun(selected)}><ArrowDownToLine size={16}/> Download Markdown report</button></div>}</section></div>
}

function AdminUsersWorkspace({self}:{self:AuthUser}) {
  const [users,setUsers]=useState<any[]>([])
  const [error,setError]=useState('')
  const [busy,setBusy]=useState('')
  const load=async()=>{setError('');try{const response=await fetch('/api/admin/users');const data=await response.json();if(!response.ok)throw new Error(data.detail||'Could not load accounts.');setUsers(data.users||[])}catch(e){setError(e instanceof Error?e.message:'Could not load accounts.')}}
  useEffect(()=>{void load()},[])
  const update=async(id:string,path:string,body:object)=>{setBusy(id);setError('');try{const response=await fetch(`/api/admin/users/${id}/${path}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await response.json();if(!response.ok)throw new Error(data.detail||'Could not update account.');await load()}catch(e){setError(e instanceof Error?e.message:'Could not update account.')}finally{setBusy('')}}
  return <div className="workspace-page"><PageHeading eyebrow="ADMINISTRATOR · ACCESS CONTROL" title="User access" description="Signup creates client accounts. Assign company or admin access here."/><div className="admin-role-cards"><article><UsersRound size={18}/><b>Client</b><span>Own live-site audits only</span></article><article><BriefcaseBusiness size={18}/><b>Company</b><span>All SEO workspace features</span></article><article><ShieldCheck size={18}/><b>Admin</b><span>All features + development</span></article></div>{error&&<div className="workspace-alert">{error}</div>}<section className="content-card"><div className="card-heading"><div><span className="section-eyebrow">ACCOUNTS</span><h2>{users.length} registered</h2></div><button className="button-secondary" onClick={()=>void load()}>Refresh</button></div><div className="admin-user-list">{users.map(user=><article className="admin-user-row" key={user.id}><div className="admin-user-avatar">{(user.display_name||user.email).slice(0,1).toUpperCase()}</div><div className="admin-user-info"><b>{user.display_name||user.email}</b><span>{user.email}</span><small>{user.google_connected?'Google OAuth linked':'Email and password'} · {new Date(user.created_at).toLocaleDateString()}</small></div><select aria-label={`Role for ${user.email}`} value={user.role} disabled={busy===user.id||user.id===self.id} onChange={e=>void update(user.id,'role',{role:e.target.value})}><option value="client">Client</option><option value="company">Company</option><option value="admin">Admin</option></select><button className={`account-state ${user.disabled?'disabled':''}`} disabled={busy===user.id||user.id===self.id} onClick={()=>void update(user.id,'state',{disabled:!user.disabled})}>{user.disabled?'Disabled':'Active'}</button></article>)}</div><p className="admin-note"><LockKeyhole size={14}/> Role changes are enforced by the API. Disabled accounts have all active sessions revoked.</p></section></div>
}

function DevelopmentWorkspace() {
  const [data,setData]=useState<Record<string,any>>({})
  const [error,setError]=useState('')
  const [loading,setLoading]=useState(false)
  const load=async()=>{setLoading(true);setError('');try{const names=['health','experts','sources','integrations'];const responses=await Promise.all(names.map(name=>fetch(name==='health'?'/api/health':name==='experts'?'/api/experts':name==='sources'?'/api/sources':'/api/integrations/status')));const json=await Promise.all(responses.map(r=>r.json()));const bad=responses.findIndex(r=>!r.ok);if(bad>=0)throw new Error(json[bad].detail||'A development endpoint failed.');setData(Object.fromEntries(names.map((name,i)=>[name,json[i]])))}catch(e){setError(e instanceof Error?e.message:'Could not load development diagnostics.')}finally{setLoading(false)}}
  useEffect(()=>{void load()},[])
  const specialists=data.experts?.specialists||[]
  const integrations=data.integrations?.integrations||[]
  return <div className="workspace-page"><PageHeading eyebrow="ADMIN ONLY · DEVELOPER TOOLS" title="Development console" description="Read-only status for the API, specialist playbook, sources, and provider adapters." action={<button className="button-secondary" disabled={loading} onClick={()=>void load()}>{loading?'Refreshing…':'Refresh status'}</button>}/>{error&&<div className="workspace-alert">{error}</div>}<div className="dev-health-grid"><article><Activity size={18}/><span>API</span><b>{data.health?.status||'Loading'}</b></article><article><Workflow size={18}/><span>Workflow</span><b>{data.experts?.workflow?.length||'—'} steps</b></article><article><UsersRound size={18}/><span>Specialists</span><b>{specialists.length||'—'} lenses</b></article><article><Link2 size={18}/><span>Connectors</span><b>{integrations.length||'—'} providers</b></article></div><section className="content-card"><div className="card-heading"><div><span className="section-eyebrow">PROVIDER READINESS</span><h2>Integration status</h2></div></div><div className="dev-provider-grid">{integrations.map((item:any)=><article key={item.id}><span className={`provider-status ${item.status}`}>{String(item.status).replace(/_/g,' ')}</span><b>{item.name}</b><small>{item.capabilities}</small></article>)}</div></section><section className="content-card"><div className="card-heading"><div><span className="section-eyebrow">DEVELOPMENT REFERENCE</span><h2>Workflow and source registry</h2></div></div><div className="dev-workflow">{(data.experts?.workflow||[]).map((item:string,index:number)=><span key={item}><i>{String(index+1).padStart(2,'0')}</i>{item.replace(/_/g,' ')}</span>)}</div><div className="dev-sources">{(data.sources?.sources||[]).map((item:any)=><a key={item.id} href={item.url} target="_blank" rel="noreferrer"><b>{item.id}</b><span>{item.title}</span><ArrowRight size={14}/></a>)}</div></section><div className="admin-note"><Code2 size={15}/> Provider status reports configured credentials; it does not make or reveal secret values.</div></div>
}

function StatCard({label,value,detail,icon}:{label:string;value:string|number;detail:string;icon:React.ReactNode}) { return <article className="stat-card"><div className="stat-card-icon">{icon}</div><div className="stat-card-label">{label}</div><div className="stat-card-value">{value}</div><div className="stat-card-detail">{detail}</div></article> }
function EmptyState({title,text,action}:{title:string;text:string;action?:React.ReactNode}) { return <div className="empty-state"><div className="empty-state-icon"><FileSearch size={22}/></div><h3>{title}</h3><p>{text}</p>{action}</div> }
function safeHostname(value:string) { try{return new URL(value).hostname}catch{return value} }

export default App
