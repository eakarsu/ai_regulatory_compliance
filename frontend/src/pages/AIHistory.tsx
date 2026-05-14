import { useEffect, useState } from 'react';
import { ai } from '../services/api';

export default function AIHistory() {
  const [data, setData] = useState<any[]>([]);
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 });
  const [typeFilter, setTypeFilter] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = (page = 1) => {
    setLoading(true);
    ai.logs({ page, limit: 20, analysis_type: typeFilter || undefined })
      .then((r: any) => {
        setData(r.data || []);
        setPagination(r.pagination || { page: 1, total_pages: 1, total: 0 });
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(1); }, [typeFilter]);

  const typeLabel = (t: string) => t.replace(/_/g, ' ');

  return (
    <div className="container">
      <h1 className="h1">AI Analysis History</h1>
      <div className="card" style={{ marginBottom: 12 }}>
        <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} style={{ width: 240 }}>
          <option value="">All types</option>
          <option value="analyze_regulation">Analyze Regulation</option>
          <option value="risk_assessment">Risk Assessment</option>
          <option value="gap_analysis">Gap Analysis</option>
          <option value="generate_policy">Generate Policy</option>
          <option value="run_assessment">Run Assessment</option>
          <option value="weekly_compliance_summary">Weekly Summary</option>
          <option value="compliance_summary_stream">Streaming Summary</option>
        </select>
      </div>

      <div style={{ marginBottom: 8, color: '#64748b', fontSize: 13 }}>
        {pagination.total} record{pagination.total !== 1 ? 's' : ''}
      </div>

      {loading ? (
        <p style={{ color: '#64748b' }}>Loading...</p>
      ) : data.length === 0 ? (
        <div className="card"><p style={{ color: '#64748b' }}>No AI analysis history.</p></div>
      ) : (
        data.map((log: any) => (
          <div className="card" key={log.id} style={{ marginBottom: 12 }}>
            <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
              <div>
                <span className="badge badge-info">{typeLabel(log.analysis_type)}</span>{' '}
                <span style={{ fontSize: 13, color: '#64748b' }}>{log.input_summary}</span>
              </div>
              <div className="row">
                <span style={{ fontSize: 12, color: '#64748b' }}>{log.tokens_used} tokens</span>
                <span style={{ fontSize: 12, color: '#64748b' }}>
                  {new Date(log.created_at).toLocaleString()}
                </span>
                <button
                  className="secondary"
                  style={{ fontSize: 12, padding: '4px 10px' }}
                  onClick={() => setExpanded(expanded === log.id ? null : log.id)}
                >
                  {expanded === log.id ? 'Hide' : 'View Result'}
                </button>
              </div>
            </div>
            {expanded === log.id && log.result && (
              <div style={{ marginTop: 12 }}>
                {log.result.summary && (
                  <p style={{ marginBottom: 8 }}><strong>Summary:</strong> {log.result.summary}</p>
                )}
                {log.result.headline && (
                  <p style={{ marginBottom: 8 }}><strong>Headline:</strong> {log.result.headline}</p>
                )}
                <details>
                  <summary style={{ cursor: 'pointer', fontSize: 13 }}>Full JSON</summary>
                  <div className="code" style={{ marginTop: 8 }}>{JSON.stringify(log.result, null, 2)}</div>
                </details>
              </div>
            )}
          </div>
        ))
      )}

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
