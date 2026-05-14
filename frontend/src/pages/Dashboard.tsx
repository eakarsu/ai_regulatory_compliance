import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { assessments, alerts } from '../services/api';

const API_BASE = (import.meta as any).env?.VITE_API_BASE || '/api';

export default function Dashboard() {
  const [stats, setStats] = useState<any>({
    total_assessments: 0,
    compliant_count: 0,
    partial_count: 0,
    non_compliant_count: 0,
    compliance_rate_percent: 0,
    open_risks: 0,
    upcoming_reviews: 0,
    average_score: 0,
  });
  const [alertList, setAlertList] = useState<any[]>([]);
  const [unread, setUnread] = useState(0);
  const [summary, setSummary] = useState('');
  const [streaming, setStreaming] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  const load = () => {
    assessments.dashboard().then((s: any) => setStats(s)).catch(() => {});
    alerts.list({ limit: 5 }).then((a: any) => {
      setAlertList(a.data || []);
      setUnread(a.unread_count || 0);
    }).catch(() => {});
  };
  useEffect(() => { load(); return () => { esRef.current?.close(); }; }, []);

  const generateAlerts = async () => {
    await alerts.generate();
    load();
  };

  const streamSummary = () => {
    setSummary('');
    setStreaming(true);
    const token = localStorage.getItem('token');
    const es = new EventSource(
      `${API_BASE}/ai/compliance-summary/stream`,
      // EventSource doesn't support headers natively; pass token via query in production
    );
    esRef.current = es;

    // Workaround: use fetch for SSE to send auth header
    es.close();
    const ctrl = new AbortController();
    esRef.current = { close: () => ctrl.abort() } as any;

    fetch(`${API_BASE}/ai/compliance-summary/stream`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: ctrl.signal,
    }).then(async res => {
      if (!res.body) return;
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') { setStreaming(false); return; }
            try {
              const parsed = JSON.parse(data);
              if (parsed.chunk) setSummary(prev => prev + parsed.chunk);
              if (parsed.error) { setSummary(`Error: ${parsed.error}`); setStreaming(false); return; }
            } catch {}
          }
        }
      }
      setStreaming(false);
    }).catch(err => {
      if (err.name !== 'AbortError') setSummary('Failed to load summary.');
      setStreaming(false);
    });
  };

  return (
    <div className="container">
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
        <h1 className="h1">Compliance Dashboard</h1>
        <div className="row">
          <button className="secondary" onClick={generateAlerts}>Generate Alerts</button>
          <button onClick={streamSummary} disabled={streaming}>
            {streaming ? 'Generating summary...' : 'AI Summary'}
          </button>
        </div>
      </div>

      {summary && (
        <div className="card" style={{ background: '#eff6ff', borderLeft: '4px solid #2563eb', marginBottom: 16 }}>
          <h2 className="h2">AI Compliance Summary</h2>
          <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{summary}</p>
        </div>
      )}

      <div className="grid grid-4">
        <div className="stat">
          <div className="stat-label">Total Assessments</div>
          <div className="stat-value">{stats.total_assessments}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Compliance Rate</div>
          <div className="stat-value success">{stats.compliance_rate_percent}%</div>
        </div>
        <div className="stat">
          <div className="stat-label">Open Risks</div>
          <div className="stat-value danger">{stats.open_risks}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Upcoming Reviews (30d)</div>
          <div className="stat-value warn">{stats.upcoming_reviews}</div>
        </div>
      </div>

      <div className="spacer" />

      <div className="grid grid-4">
        <div className="stat">
          <div className="stat-label">Compliant</div>
          <div className="stat-value success">{stats.compliant_count}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Partial</div>
          <div className="stat-value warn">{stats.partial_count}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Non-Compliant</div>
          <div className="stat-value danger">{stats.non_compliant_count}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Avg Score</div>
          <div className={`stat-value ${stats.average_score >= 80 ? 'success' : stats.average_score >= 50 ? 'warn' : 'danger'}`}>
            {stats.average_score}
          </div>
        </div>
      </div>

      <div className="spacer" />

      <div className="card">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <h2 className="h2">
            Recent Alerts {unread > 0 && <span className="badge badge-danger">{unread} unread</span>}
          </h2>
          <Link to="/alerts">View all</Link>
        </div>
        {alertList.length === 0 ? (
          <p style={{ color: '#64748b' }}>No alerts.</p>
        ) : (
          <ul style={{ listStyle: 'none' }}>
            {alertList.map((a) => (
              <li key={a.id} style={{ padding: 10, borderBottom: '1px solid #f1f5f9' }}>
                <span
                  className={`badge badge-${a.severity === 'critical' ? 'critical' : a.severity === 'warning' ? 'warn' : 'info'}`}
                >
                  {a.severity}
                </span>{' '}
                {a.message}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="grid grid-4">
        <Link to="/regulations" className="card" style={{ textAlign: 'center', padding: 24 }}>
          <h3 className="h3">Browse Regulations</h3>
          <p style={{ color: '#64748b', fontSize: 13 }}>GDPR, HIPAA, SOX, and more</p>
        </Link>
        <Link to="/ai/risk" className="card" style={{ textAlign: 'center', padding: 24 }}>
          <h3 className="h3">Risk Assessment</h3>
          <p style={{ color: '#64748b', fontSize: 13 }}>Profile your compliance posture</p>
        </Link>
        <Link to="/ai/chat" className="card" style={{ textAlign: 'center', padding: 24 }}>
          <h3 className="h3">AI Chat Assistant</h3>
          <p style={{ color: '#64748b', fontSize: 13 }}>Ask any compliance question</p>
        </Link>
        <Link to="/calendar" className="card" style={{ textAlign: 'center', padding: 24 }}>
          <h3 className="h3">Compliance Calendar</h3>
          <p style={{ color: '#64748b', fontSize: 13 }}>Upcoming review deadlines</p>
        </Link>
      </div>
    </div>
  );
}
