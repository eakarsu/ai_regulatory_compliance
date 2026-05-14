import { useEffect, useState } from 'react';
import { alerts } from '../services/api';

export default function Alerts() {
  const [data, setData] = useState<any[]>([]);
  const [unread, setUnread] = useState(0);
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 });
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [severity, setSeverity] = useState('');
  const [loading, setLoading] = useState(true);

  const load = (page = 1) => {
    setLoading(true);
    alerts
      .list({ page, limit: 20, unread_only: unreadOnly || undefined, severity: severity || undefined })
      .then((r: any) => {
        setData(r.data || []);
        setUnread(r.unread_count || 0);
        setPagination(r.pagination || { page: 1, total_pages: 1, total: 0 });
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(1); }, [unreadOnly, severity]);

  const generate = async () => {
    await alerts.generate();
    load(1);
  };

  const markRead = async (id: string) => {
    await alerts.markRead(id);
    load(pagination.page);
  };

  const markAllRead = async () => {
    await alerts.markAllRead();
    load(1);
  };

  const dismiss = async (id: string) => {
    if (!confirm('Dismiss this alert?')) return;
    await alerts.dismiss(id);
    load(pagination.page);
  };

  return (
    <div className="container">
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 className="h1" style={{ marginBottom: 0 }}>
          Compliance Alerts {unread > 0 && <span className="badge badge-danger">{unread} unread</span>}
        </h1>
        <div className="row">
          {unread > 0 && (
            <button className="secondary" onClick={markAllRead}>Mark all read</button>
          )}
          <button onClick={generate}>Generate Alerts</button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 12 }}>
        <div className="grid grid-2">
          <div className="row">
            <label style={{ fontSize: 13, whiteSpace: 'nowrap' }}>Unread only:</label>
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={e => setUnreadOnly(e.target.checked)}
              style={{ width: 'auto' }}
            />
          </div>
          <select value={severity} onChange={e => setSeverity(e.target.value)} style={{ width: '100%' }}>
            <option value="">All severities</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <div style={{ marginBottom: 8, color: '#64748b', fontSize: 13 }}>
        {pagination.total} alert{pagination.total !== 1 ? 's' : ''}
      </div>

      <div className="card">
        {loading ? (
          <p style={{ color: '#64748b' }}>Loading...</p>
        ) : data.length === 0 ? (
          <p style={{ color: '#64748b' }}>No alerts.</p>
        ) : (
          <ul style={{ listStyle: 'none' }}>
            {data.map((a) => (
              <li
                key={a.id}
                style={{
                  padding: 14,
                  borderBottom: '1px solid #f1f5f9',
                  background: a.is_read ? 'transparent' : '#eff6ff',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: 12,
                }}
              >
                <div>
                  <span
                    className={`badge badge-${
                      a.severity === 'critical' ? 'critical' :
                      a.severity === 'warning' ? 'warn' : 'info'
                    }`}
                  >
                    {a.severity}
                  </span>{' '}
                  <strong>{a.alert_type.replace(/_/g, ' ')}</strong>
                  <div style={{ marginTop: 4 }}>{a.message}</div>
                  <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                    {new Date(a.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="row" style={{ flexShrink: 0 }}>
                  {!a.is_read && (
                    <button className="secondary" onClick={() => markRead(a.id)} style={{ fontSize: 12 }}>
                      Mark read
                    </button>
                  )}
                  <button className="danger" onClick={() => dismiss(a.id)} style={{ fontSize: 12 }}>
                    Dismiss
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {pagination.total_pages > 1 && (
        <div className="row" style={{ justifyContent: 'center', gap: 8 }}>
          <button className="secondary" disabled={pagination.page <= 1} onClick={() => load(pagination.page - 1)}>
            Previous
          </button>
          <span style={{ fontSize: 13, color: '#64748b' }}>
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <button className="secondary" disabled={pagination.page >= pagination.total_pages} onClick={() => load(pagination.page + 1)}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}
