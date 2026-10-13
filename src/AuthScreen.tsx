import { useState, type FormEvent } from 'react'
import { ArrowRight, BadgeCheck, Eye, EyeOff, Globe2, LockKeyhole, Search, ShieldCheck, Sparkles } from 'lucide-react'

export type AuthUser = { id: string; email: string; display_name: string; role: 'admin' | 'company' | 'client' }

export default function AuthScreen({ onAuthed }: { onAuthed: (user: AuthUser) => void }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(() => new URLSearchParams(window.location.search).has('auth_error') ? 'Google sign-in could not be completed. Try again or use email and password.' : '')

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const response = await fetch(`/api/auth/${mode === 'login' ? 'login' : 'signup'}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mode === 'login' ? { email, password } : { display_name: name, email, password }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not sign in.')
      window.history.replaceState({}, '', window.location.pathname)
      onAuthed(data.user)
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not reach the SEON API.') }
    finally { setBusy(false) }
  }

  const google = async () => {
    setBusy(true); setError('')
    try {
      const response = await fetch('/api/auth/google/start')
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Google sign-in is unavailable.')
      window.location.assign(data.authorization_url)
    } catch (err) { setError(err instanceof Error ? err.message : 'Google sign-in is unavailable.'); setBusy(false) }
  }

  return <main className="auth-shell">
    <section className="auth-story"><div className="auth-brand"><span className="auth-mark"><i/><i/><i/></span><b>seon<span>.</span></b><small>SEARCH EXPERIENCE OPERATING NETWORK</small></div><div className="auth-story-copy"><span className="auth-kicker"><Sparkles size={14}/> EVIDENCE-LED SEO WORK</span><h1>Make the next<br/>search move <em>clear.</em></h1><p>One workspace for business context, site reviews, search research, and human-approved action.</p><div className="auth-mini-flow"><span><Globe2 size={16}/> Inspect</span><i/><span><Search size={16}/> Understand</span><i/><span><BadgeCheck size={16}/> Improve</span></div></div><div className="auth-story-footer"><ShieldCheck size={15}/> Recommendations stay reviewable. Website edits require approval.</div><div className="auth-orb auth-orb-one"/><div className="auth-orb auth-orb-two"/></section>
    <section className="auth-panel-wrap"><div className="auth-panel"><div className="auth-panel-head"><div className="auth-lock"><LockKeyhole size={19}/></div><span className="auth-panel-label">SEON WORKSPACE</span><h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2><p>{mode === 'login' ? 'Sign in to continue to your workspace.' : 'New accounts start with client access. An admin can assign company access.'}</p></div>
      <div className="auth-switch"><button className={mode === 'login' ? 'selected' : ''} onClick={() => { setMode('login'); setError('') }}>Sign in</button><button className={mode === 'signup' ? 'selected' : ''} onClick={() => { setMode('signup'); setError('') }}>Create account</button></div>
      <form className="auth-form" onSubmit={submit}>{mode === 'signup' && <label>Your name<input required autoComplete="name" value={name} onChange={e => setName(e.target.value)} placeholder="Name" maxLength={160}/></label>}<label>Email address<input required type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" maxLength={254}/></label><label>Password<span className="auth-password"><input required type={showPassword ? 'text' : 'password'} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={mode === 'signup' ? 12 : 1} value={password} onChange={e => setPassword(e.target.value)} placeholder={mode === 'signup' ? 'At least 12 characters' : 'Your password'}/><button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(v => !v)}>{showPassword ? <EyeOff size={16}/> : <Eye size={16}/>}</button></span></label>{error && <div className="auth-error">{error}</div>}<button className="auth-submit" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create client account'}<ArrowRight size={16}/></button></form>
      <div className="auth-divider"><span/>or continue with<span/></div><button className="auth-google" onClick={() => void google()} disabled={busy}><GoogleMark/>Continue with Google</button><div className="auth-footnote"><ShieldCheck size={14}/><span>Secure session · Client data is separated by account</span></div><small className="auth-role-note">Company and administrator roles are assigned by an administrator.</small>
    </div></section>
  </main>
}

function GoogleMark() { return <svg width="17" height="17" viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5Z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.91a11.1 11.1 0 0 1-4.78 7.27l7.73 5.99c4.51-4.17 7.12-10.31 7.12-17.73Z"/><path fill="#FBBC05" d="M10.53 28.59a14.4 14.4 0 0 1 0-9.18l-7.98-6.19a23.94 23.94 0 0 0 0 21.56l7.98-6.19Z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.73l-7.73-5.99c-2.14 1.43-4.88 2.27-8.17 2.27-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48Z"/></svg> }
