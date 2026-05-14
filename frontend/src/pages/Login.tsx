import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [organization, setOrganization] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') await login(email, password);
      else await register(email, password, name, organization);
      navigate('/');
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
