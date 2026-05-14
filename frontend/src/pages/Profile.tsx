import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { auth } from '../services/api';

export default function Profile() {
  const { user, setUser } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [organization, setOrganization] = useState(user?.organization || '');
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  if (!user) return null;

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);
    try {
      const updated: any = await auth.updateMe(name, organization);
      if (setUser) setUser(updated);
      setSuccess('Profile updated successfully.');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 600 }}>
      <h1 className="h1">Profile</h1>

      <div className="card">
        <div className="col">
          <div>
            <span className="label">Email</span>
            <p style={{ marginTop: 4 }}>{user.email}</p>
          </div>
          <div>
            <span className="label">Role</span>
            <p style={{ marginTop: 4 }}>
              <span className="badge badge-info">{user.role}</span>
            </p>
          </div>
          <div>
            <span className="label">Member since</span>
            <p style={{ marginTop: 4 }}>{new Date(user.created_at).toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="h2">Edit Profile</h2>
        <form onSubmit={save} className="col">
          <div className="col">
            <label className="label">Full Name</label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              required
              placeholder="Your name"
            />
          </div>
          <div className="col">
            <label className="label">Organization</label>
            <input
              value={organization}
              onChange={e => setOrganization(e.target.value)}
              placeholder="Your organization"
            />
          </div>
          {error && <div className="error">{error}</div>}
          {success && <div className="success">{success}</div>}
          <button type="submit" disabled={saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  );
}
