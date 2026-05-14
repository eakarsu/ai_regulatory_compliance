import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Nav() {
  const { user, logout } = useAuth();
  const [aiOpen, setAiOpen] = useState(false);

  if (!user) return null;
  return (
    <div className="nav">
      <span className="nav-brand">RegCompliance AI</span>
      <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
        Dashboard
      </NavLink>
      <NavLink to="/regulations" className={({ isActive }) => (isActive ? 'active' : '')}>
        Regulations
      </NavLink>
      <NavLink to="/assessments" className={({ isActive }) => (isActive ? 'active' : '')}>
        Assessments
      </NavLink>
      <NavLink to="/alerts" className={({ isActive }) => (isActive ? 'active' : '')}>
        Alerts
      </NavLink>
      <NavLink to="/calendar" className={({ isActive }) => (isActive ? 'active' : '')}>
        Calendar
      </NavLink>

      {/* AI dropdown */}
      <div style={{ position: 'relative' }}>
        <button
          className="secondary"
          style={{ fontSize: 14, padding: '6px 12px' }}
          onClick={() => setAiOpen(o => !o)}
        >
          AI Tools ▾
        </button>
        {aiOpen && (
          <div
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              background: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: 8,
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              minWidth: 180,
              zIndex: 100,
              padding: 4,
            }}
            onMouseLeave={() => setAiOpen(false)}
          >
            {[
              { to: '/ai/chat', label: 'Chat Assistant' },
              { to: '/ai/analyze', label: 'Analyze Regulation' },
              { to: '/ai/risk', label: 'Risk Assessment' },
              { to: '/ai/gap', label: 'Gap Analysis' },
              { to: '/ai/policy', label: 'Generate Policy' },
              { to: '/ai/backlog-tools', label: 'Backlog Tools' },
              { to: '/ai/history', label: 'AI History' },
            ].map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setAiOpen(false)}
                style={{
                  display: 'block',
                  padding: '8px 14px',
                  color: '#1e293b',
                  borderRadius: 6,
                  fontSize: 14,
                }}
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        )}
      </div>

      <div style={{ marginLeft: 'auto', display: 'flex', gap: 12, alignItems: 'center' }}>
        <NavLink to="/profile" style={{ color: 'white', fontSize: 13 }}>
          {user.name}
        </NavLink>
        <button className="secondary" onClick={logout} style={{ fontSize: 13, padding: '6px 12px' }}>
          Logout
        </button>
      </div>
    </div>
  );
}
