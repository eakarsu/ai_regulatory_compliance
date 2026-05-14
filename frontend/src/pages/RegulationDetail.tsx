import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { regulations, assessments, watches } from '../services/api';

export default function RegulationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [reg, setReg] = useState<any>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [watched, setWatched] = useState(false);

  useEffect(() => {
    if (!id) return;
    regulations.get(id).then((r: any) => setReg(r));
    watches.list().then((ws: any[]) => {
      setWatched(ws.some((w: any) => w.regulation_id === id));
    }).catch(() => {});
  }, [id]);

  const startAssessment = async () => {
    setError('');
    setCreating(true);
    try {
      const a: any = await assessments.create(id!);
      navigate(`/assessments/${a.id}`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const toggleWatch = async () => {
    if (watched) {
      await watches.unwatch(id!);
      setWatched(false);
    } else {
      await watches.watch(id!);
      setWatched(true);
    }
  };

  if (!reg) return <div className="container">Loading...</div>;

  return (
    <div className="container">
      <Link to="/regulations">&larr; Back to regulations</Link>
      <div className="card" style={{ marginTop: 12 }}>
        <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <h1 className="h1" style={{ marginBottom: 0 }}>{reg.title}</h1>
          <div className="row">
            <button
              className={watched ? 'secondary' : 'success'}
              onClick={toggleWatch}
              style={{ fontSize: 13 }}
            >
              {watched ? 'Unwatch Regulation' : 'Watch Regulation'}
            </button>
            <button onClick={startAssessment} disabled={creating}>
              {creating ? 'Creating...' : 'Start Compliance Assessment'}
            </button>
          </div>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <span className="badge badge-info">{reg.jurisdiction}</span>
          <span className="badge badge-gray">{reg.category}</span>
          {reg.effective_date && (
            <span className="badge badge-gray">Effective: {reg.effective_date}</span>
          )}
          {reg.is_active ? (
            <span className="badge badge-success">Active</span>
          ) : (
            <span className="badge badge-gray">Inactive</span>
          )}
          {watched && <span className="badge badge-info">Watching</span>}
        </div>
        <div className="spacer" />
        <p>{reg.summary}</p>
        {reg.source_url && (
          <p style={{ marginTop: 8 }}>
            Source: <a href={reg.source_url} target="_blank" rel="noreferrer">{reg.source_url}</a>
          </p>
        )}
        {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
      </div>

      {reg.requirements && reg.requirements.length > 0 && (
        <div className="card">
          <h2 className="h2">Requirements ({reg.requirements.length})</h2>
          <table>
            <thead>
              <tr>
                <th>Requirement</th>
                <th>Category</th>
                <th>Risk</th>
                <th>Mandatory</th>
              </tr>
            </thead>
            <tbody>
              {reg.requirements.map((req: any) => (
                <tr key={req.id}>
                  <td>{req.requirement_text}</td>
                  <td>{req.category || '-'}</td>
                  <td>
                    <span
                      className={`badge badge-${
                        req.risk_level === 'critical' ? 'critical' :
                        req.risk_level === 'high' ? 'danger' :
                        req.risk_level === 'medium' ? 'warn' : 'gray'
                      }`}
                    >
                      {req.risk_level}
                    </span>
                  </td>
                  <td>
                    {req.is_mandatory
                      ? <span className="badge badge-danger">Required</span>
                      : <span className="badge badge-gray">Optional</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {reg.full_text && (
        <div className="card">
          <h2 className="h2">Full Text</h2>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.6 }}>{reg.full_text}</pre>
        </div>
      )}
    </div>
  );
}
