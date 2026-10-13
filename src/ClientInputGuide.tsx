import { useState } from 'react'
import { ArrowRight, BadgeCheck, BriefcaseBusiness, ChevronDown, Code2, FileSearch, KeyRound, ShieldCheck } from 'lucide-react'

const scenarios = [
  {
    id: 'live-site', title: 'Live website SEO review', subtitle: 'What to ask for before auditing an existing website', icon: FileSearch,
    items: [
      ['Website and authorization', 'The public website URL and confirmation that the client authorizes a read-only crawl. Ask about staging or restricted pages that should be excluded.'],
      ['Business and market context', 'Priority products or services, target audience, locations genuinely served, languages, competitors, business goal, and the conversion that matters.'],
      ['Search Console (optional)', 'Ask the client to grant the project service-account email read-only access to the correct property. Collect the property URL and report date range.'],
      ['GA4 (optional)', 'Ask the client to grant the service-account email Viewer access. Collect the numeric GA4 property ID, date range, and conversion events they care about.'],
      ['Baseline and known issues', 'Any ranking or traffic changes, affected pages, launches or migrations, and the source and dates for each reported issue.'],
    ], report: 'Public crawl findings plus, when access is connected, Search Console clicks, impressions, CTR and average position by query/page; GA4 users, sessions, engagement, conversions and landing pages. Label sources, dates and gaps.'
  },
  {
    id: 'repository', title: 'Website repository review', subtitle: 'What to ask for when reviewing source code', icon: Code2,
    items: [
      ['Source files', 'A ZIP of the website repository, or the exact repository archive and branch/commit to inspect. Confirm the client is authorized to share it.'],
      ['Platform and deployment', 'Framework or CMS, routing/rendering approach, production or preview URL, and how the site is deployed.'],
      ['Review scope', 'Important page templates/routes, known SEO issues, files or folders excluded from review, and any special privacy constraints.'],
      ['Validation details', 'The project’s build or test command, how to preview a proposed change, and the person who reviews and deploys approved changes.'],
      ['Safe handoff', 'Ask them to remove `.env`, API keys, credentials, private customer data, dependencies, and build output before sharing. Do not request repository passwords or tokens in the intake.'],
    ], report: 'Specific source paths and observed code signals, recommendation and rationale, evidence/confidence, how the client can validate the rendered result, and any limits of static analysis. No code is changed by this review.'
  },
  {
    id: 'new-site', title: 'New website SEO plan', subtitle: 'What to ask for before proposing site structure', icon: BriefcaseBusiness,
    items: [
      ['Business and offer', 'Business name, business model, products/services, priority offerings, differentiators, proof, and offers or claims that must be excluded.'],
      ['Audience and intent', 'Who the site should serve, what those people need, common questions/objections, and the actions they should take.'],
      ['Markets and language', 'Target countries or regions, languages, delivery coverage or genuine service locations, and any local business presence.'],
      ['Goals and measurement', 'Primary business outcome, meaningful conversion event, expected analytics setup, and any existing baseline or launch target.'],
      ['Build constraints', 'Planned domain (if known), CMS/framework, brand/legal requirements, budget or timeline constraints, and named competitors with URLs.'],
    ], report: 'A proposed page map with intent and rationale, technical and measurement launch requirements, prioritized backlog, assumptions, missing inputs, and research limitations. Keyword themes remain hypotheses unless supported by data.'
  },
]

export default function ClientInputGuide({ onStart }: { onStart: () => void }) {
  const [expanded, setExpanded] = useState('live-site')
  return <div className="workspace-page client-guide-page">
    <header className="page-heading"><div><span className="section-eyebrow">CLIENT INTAKE · FIELD GUIDE</span><h1>What to request for an SEO engagement</h1><p>Use the scenario checklist to collect the right context, access and report scope. Unknown answers can stay unknown; never ask clients to send passwords or private keys.</p></div><button className="button-primary" onClick={onStart}>Start client intake <ArrowRight size={16}/></button></header>
    <div className="client-guide-safety"><ShieldCheck size={18}/><div><b>Credentials stay with the project operator</b><span>For Google reports, ask the client to grant your service-account email property access. Keep the JSON key on the API server; do not collect or share account passwords.</span></div></div>
    <section className="client-guide-list" aria-label="Scenario input checklists">
      {scenarios.map(({id,title,subtitle,icon:Icon,items,report})=><article className={`client-guide-card ${expanded===id?'is-expanded':''}`} key={id}>
        <button className="client-guide-trigger" aria-expanded={expanded===id} onClick={()=>setExpanded(current=>current===id?'':id)}><span className="client-guide-icon"><Icon size={19}/></span><span className="client-guide-title"><b>{title}</b><small>{subtitle}</small></span><ChevronDown size={18}/></button>
        {expanded===id&&<div className="client-guide-content"><h2>Ask the client for</h2><div className="client-guide-items">{items.map(([label,description])=><div className="client-guide-item" key={label}><BadgeCheck size={16}/><p><b>{label}</b><span>{description}</span></p></div>)}</div><div className="client-guide-report"><div><KeyRound size={15}/><b>Make the report scope clear</b></div><p>{report}</p></div></div>}
      </article>)}
    </section>
    <div className="client-guide-note"><KeyRound size={15}/><span>Google property access is optional for starting a public-site review. Without it, proceed and mark Search Console/GA4 data unavailable.</span></div>
  </div>
}
