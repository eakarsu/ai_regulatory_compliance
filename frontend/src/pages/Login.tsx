import { useRef as useDemoLoginRef, useState as useDemoLoginState } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const demoLoginLock = useDemoLoginRef(false);
  const [demoLoginBusy, setDemoLoginBusy] = useDemoLoginState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [organization, setOrganization] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent, demoLoginCredentials: { email: string; password: string } | undefined = undefined) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if ((demoLoginCredentials || mode === 'login')) await login((demoLoginCredentials?.email ?? email), (demoLoginCredentials?.password ?? password));
      else await register(email, password, name, organization);
      navigate('/governance');
    } catch (err: any) {
      setError(err.message || 'Failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 420, margin: '60px auto', padding: 20 }}>
      <div className="card">
        <h1 className="h1">{mode === 'login' ? 'Sign In' : 'Create Account'}</h1>
        <form onSubmit={submit} className="col">
          {mode === 'register' && (
            <>
              <div className="col">
                <label className="label">Name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="col">
                <label className="label">Organization</label>
                <input value={organization} onChange={(e) => setOrganization(e.target.value)} />
              </div>
            </>
          )}
          <div className="col">
            <label className="label">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="col">
            <label className="label">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <div className="error">{error}</div>}
          <button
            type="button"
            onClick={async (event) => {
 if (demoLoginLock.current) return;
 demoLoginLock.current = true; setDemoLoginBusy(true);
 const values: {email?: string; password?: string; error?: unknown} = {};
 const captureDemoValue = (key: "email" | "password" | "error", value: any) => { values[key] = value; return value; };
 try {
  await (async () => { setEmail(captureDemoValue("email", import.meta.env.VITE_DEMO_EMAIL || '')); setPassword(captureDemoValue("password", import.meta.env.VITE_DEMO_PASSWORD || '')); })();
  if (values.error || typeof values.email !== 'string' || !values.email || typeof values.password !== 'string' || !values.password) { setError(typeof values.error === 'string' ? values.error : 'Demo credentials are unavailable.'); return; }
  await submit(event, { email: values.email, password: values.password });
 } finally { demoLoginLock.current = false; setDemoLoginBusy(false); }
}}
            disabled={demoLoginBusy || (!import.meta.env.VITE_DEMO_EMAIL || !import.meta.env.VITE_DEMO_PASSWORD)}
            aria-label="Log In as Demo"
            style={{ width: '100%', marginBottom: '12px', padding: '10px 14px', borderRadius: '8px', border: '1px solid currentColor', background: 'transparent', cursor: 'pointer' }}
          >
            Log In as Demo
          </button>
          <button type="submit" disabled={loading}>
            {loading ? '...' : mode === 'login' ? 'Sign In' : 'Register'}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
          >
            {mode === 'login' ? 'Need an account? Register' : 'Have an account? Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}
