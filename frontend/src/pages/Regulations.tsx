import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { regulations, watches } from '../services/api';

export default function Regulations() {
  const [data, setData] = useState<any[]>([]);
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 });
  const [search, setSearch] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [category, setCategory] = useState('');
  const [watchedIds, setWatchedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const loadWatches = () => {
    watches.list().then((ws: any[]) => {
      setWatchedIds(new Set(ws.map((w: any) => w.regulation_id)));
    }).catch(() => {});
  };

  const load = (page = 1) => {
    setLoading(true);
    regulations
      .list({
        search: search || undefined,
        jurisdiction: jurisdiction || undefined,
        category: category || undefined,
        page,
        limit: 20,
      })
      .then((r: any) => {
        setData(r.data || []);
        setPagination(r.pagination || { page: 1, total_pages: 1, total: 0 });
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(1); }, [search, jurisdiction, category]);
  useEffect(() => { loadWatches(); }, []);

  const toggleWatch = async (regId: string) => {
    if (watchedIds.has(regId)) {
      await watches.unwatch(regId);
      setWatchedIds(prev => { const s = new Set(prev); s.delete(regId); return s; });
    } else {
      await watches.watch(regId);
      setWatchedIds(prev => new Set(prev).add(regId));
    }
  };

  return (
    <div className="container">
      <h1 className="h1">Regulations</h1>
      <div className="card">
        <div className="grid grid-3">
          <input
            placeholder="Search title or summary..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <input
            placeholder="Jurisdiction (US, EU, UK...)"
            value={jurisdiction}
            onChange={(e) => setJurisdiction(e.target.value)}
          />
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            <option value="GDPR">GDPR</option>
            <option value="HIPAA">HIPAA</option>
            <option value="SOX">SOX</option>
            <option value="PCI">PCI DSS</option>
            <option value="CCPA">CCPA</option>
            <option value="Other">Other</option>
          </select>
        </div>
      </div>

      <div style={{ marginBottom: 8, color: '#64748b', fontSize: 13 }}>
        {pagination.total} regulation{pagination.total !== 1 ? 's' : ''}
      </div>

      <div className="card">
        {loading ? (
          <p style={{ color: '#64748b' }}>Loading...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Jurisdiction</th>
                <th>Category</th>
                <th>Effective Date</th>
                <th>Status</th>
                <th>Watch</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link to={`/regulations/${r.id}`}>{r.title}</Link>
                  </td>
                  <td>{r.jurisdiction}</td>
                  <td>
                    <span className="badge badge-info">{r.category}</span>
                  </td>
                  <td>{r.effective_date || '-'}</td>
                  <td>
                    <span className={`badge badge-${r.is_active ? 'success' : 'gray'}`}>
                      {r.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <button
                      className={watchedIds.has(r.id) ? 'danger' : 'secondary'}
                      style={{ fontSize: 12, padding: '4px 10px' }}
                      onClick={() => toggleWatch(r.id)}
                    >
                      {watchedIds.has(r.id) ? 'Unwatch' : 'Watch'}
                    </button>
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', color: '#64748b' }}>
                    No regulations found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
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
