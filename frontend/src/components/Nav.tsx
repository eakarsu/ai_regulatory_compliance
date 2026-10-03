import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './AppSidebar.css';

const WORKSPACE = [
  { to: '/governance', label: 'Governed Release' },
  { to: '/profile', label: 'Profile' },
];
const LEGACY = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/regulations', label: 'Regulations' },
  { to: '/assessments', label: 'Assessments' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/calendar', label: 'Calendar' },
  { to: '/control-attestation-queue', label: 'Control Attestation' },
];
const AI_TOOLS = [
  { to: '/ai/chat', label: 'Chat Assistant' },
  { to: '/ai/analyze', label: 'Analyze Regulation' },
  { to: '/ai/risk', label: 'Risk Assessment' },
  { to: '/ai/gap', label: 'Gap Analysis' },
  { to: '/ai/policy', label: 'Generate Policy' },
  { to: '/ai/backlog-tools', label: 'Backlog Tools' },
  { to: '/ai/history', label: 'AI History' },
];

export default function Nav() {
  const { user, logout } = useAuth();
  const [query, setQuery] = useState('');
  const legacyUiEnabled = (import.meta as any).env?.VITE_ENABLE_LEGACY_UI === 'true';
  if (!user) return null;
  const groups = [
    { label: 'Workspace', items: legacyUiEnabled ? [...WORKSPACE, ...LEGACY] : WORKSPACE },
    ...(legacyUiEnabled ? [{ label: 'AI tools', items: AI_TOOLS }] : []),
  ];
  return <aside className="codex-side" aria-label="Application navigation">
    <div className="codex-side-brand"><strong>RegCompliance AI</strong><span>{user.name}</span></div>
    <label className="codex-side-search-label" htmlFor="codex-side-search">Find a section</label>
    <input id="codex-side-search" className="codex-side-search" type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search navigation" />
    <nav className="codex-side-links" aria-label="Sections">
      {groups.map(group => {
        const items = group.items.filter(item => item.label.toLowerCase().includes(query.toLowerCase().trim()));
        return items.length ? <div className="codex-side-group" key={group.label}>
          <span className="codex-side-heading">{group.label}</span>
          {items.map(item => <NavLink key={item.to} to={item.to} className={({ isActive }) => `codex-side-link${isActive ? ' active' : ''}`}>{item.label}</NavLink>)}
        </div> : null;
      })}
    </nav>
    <button className="codex-side-logout" type="button" onClick={logout}>Sign out</button>
  </aside>;
}
