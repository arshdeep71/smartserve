import { useState } from 'react';
import { Coffee, LockKeyhole } from 'lucide-react';
import { request } from '../services/api';

export default function Login({ onLogin }) {
  const [businessId, setBusinessId] = useState(localStorage.getItem('businessId') || '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      const result = await request(`/businesses/${businessId}/users/login`, { method: 'POST', body: JSON.stringify({ email, password }) });
      localStorage.setItem('businessId', businessId); localStorage.setItem('token', result.access_token); onLogin();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <main className="login-screen"><form className="login-card" onSubmit={submit}><span className="brand-icon large"><Coffee /></span><p className="eyebrow">SMARTSERVE PORTAL</p><h1>Welcome back</h1><p className="muted">Sign in to manage your food business.</p><label>Business ID<input required value={businessId} onChange={e => setBusinessId(e.target.value)} placeholder="Your business ID" /></label><label>Email address<input required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@business.com" /></label><label>Password<input required type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter your password" /></label>{error && <p className="error">{error}</p>}<button className="primary-button full" disabled={busy}><LockKeyhole size={17} />{busy ? 'Signing in…' : 'Sign in'}</button><p className="login-hint">Ask your business administrator for an account.</p></form></main>;
}
