import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { assessments } from '../services/api';

export default function Assessments() {
  const [data, setData] = useState<any[]>([]);
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 });
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const load = (page = 1) => {
    setLoading(true);
    assessments
      .list({ page, limit: 20, status: statusFilter || undefined })
      .then((r: any) => {
        setData(r.data || []);
        setPagination(r.pagination || { page: 1, total_pages: 1, total: 0 });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(1); }, [statusFilter]);

  const statusBadge = (status: string) => {
    if (status === 'compliant') return <span className="badge badge-success">Compliant</span>;
    if (status === 'partial') return <span className="badge badge-warn">Partial</span>;
    if (status === 'non_compliant') return <span className="badge badge-danger">Non-Compliant</span>;
    return <span className="badge badge-gray">{status}</span>;
  };

  return (
    <div className="container">
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 className="h1" style={{ marginBottom: 0 }}>Compliance Assessments</h1>
        <div className="row">
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            style={{ width: 160 }}
          >
            <option value="">All statuses</option>
            <option value="compliant">Compliant</option>
            <option value="partial">Partial</option>
            <option value="non_compliant">Non-Compliant</option>
          </select>
        </div>
      </div>

      <div style={{ marginBottom: 8, color: '#64748b', fontSize: 13 }}>
        {pagination.total} assessment{pagination.total !== 1 ? 's' : ''} total
      </div>

      <div className="card">
        {loading ? (
          <p style={{ color: '#64748b' }}>Loading...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Regulation</th>
                <th>Status</th>
                <th>Score</th>
                <th>Assessed</th>
                <th>Next Review</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.map((a) => (
                <tr key={a.id}>
                  <td>
                    <Link to={`/regulations/${a.regulation_id}`} style={{ fontSize: 13, color: '#64748b' }}>
                      {a.regulation_title || a.regulation_id.slice(0, 8) + '…'}
                    </Link>
                  </td>
                  <td>{statusBadge(a.status)}</td>
                  <td>
                    <strong>{a.overall_score}</strong>/100
                    <div className="score-bar">
                      <span
                        className={`score-fill ${a.overall_score >= 80 ? 'high' : a.overall_score >= 50 ? 'medium' : 'low'}`}
                        style={{ width: `${a.overall_score}%` }}
                      />
                    </div>
                  </td>
                  <td>{new Date(a.assessed_at).toLocaleDateString()}</td>
                  <td>
                    {a.next_review_date ? (
                      <span style={{ color: new Date(a.next_review_date) < new Date() ? '#dc2626' : undefined }}>
                        {new Date(a.next_review_date).toLocaleDateString()}
                      </span>
                    ) : '-'}
                  </td>
                  <td>
                    <Link to={`/assessments/${a.id}`} className="badge badge-info">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', color: '#64748b' }}>
                    No assessments yet. Start one from the regulations page.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {pagination.total_pages > 1 && (
        <div className="row" style={{ justifyContent: 'center', gap: 8 }}>
          <button
            className="secondary"
            disabled={pagination.page <= 1}
            onClick={() => load(pagination.page - 1)}
          >
            Previous
          </button>
          <span style={{ fontSize: 13, color: '#64748b' }}>
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <button
            className="secondary"
            disabled={pagination.page >= pagination.total_pages}
            onClick={() => load(pagination.page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
