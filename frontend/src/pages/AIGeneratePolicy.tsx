import { useEffect, useState } from 'react';
import { ai, regulations } from '../services/api';

export default function AIGeneratePolicy() {
  const [regs, setRegs] = useState<any[]>([]);
  const [regulationId, setRegulationId] = useState('');
  const [orgName, setOrgName] = useState('');
  const [orgContext, setOrgContext] = useState('');
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    regulations.list({ limit: 100 }).then((r: any) => setRegs(r.data || []));
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    setResult(null);
    try {
      const r: any = await ai.generatePolicy(regulationId, orgName, orgContext || undefined);
      setResult(r.result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const downloadJSON = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `policy-${(result.policy_title || 'document').replace(/\s+/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container">
      <h1 className="h1">Generate Policy Document</h1>
      <p style={{ color: '#64748b', marginBottom: 16 }}>
        Generate a structured policy document tailored to your organization and a chosen regulation.
      </p>
      <div className="card">
        <form onSubmit={submit} className="col">
          <label className="label">Regulation</label>
          <select value={regulationId} onChange={(e) => setRegulationId(e.target.value)} required>
            <option value="">Select regulation...</option>
            {regs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.title} ({r.jurisdiction})
              </option>
            ))}
          </select>
          <label className="label">Organization Name</label>
          <input value={orgName} onChange={(e) => setOrgName(e.target.value)} required />
          <label className="label">Organization Context (optional)</label>
          <textarea
            value={orgContext}
            onChange={(e) => setOrgContext(e.target.value)}
            placeholder="Industry, size, geographies, special considerations..."
          />
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy}>
            {busy ? 'Generating...' : 'Generate Policy'}
          </button>
        </form>
      </div>

      {result && (
        <div className="card">
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <h2 className="h2">{result.policy_title}</h2>
            <button onClick={downloadJSON}>Download JSON</button>
          </div>
          <div className="row">
            {result.version && <span className="badge badge-gray">v{result.version}</span>}
            {result.effective_date && <span className="badge badge-info">Effective: {result.effective_date}</span>}
          </div>
          {result.scope && (
            <>
              <h3 className="h3">Scope</h3>
              <p>{result.scope}</p>
            </>
          )}
          {result.purpose && (
            <>
              <h3 className="h3">Purpose</h3>
              <p>{result.purpose}</p>
            </>
          )}
          {result.policy_sections && (
            <>
              <h3 className="h3">Policy Sections</h3>
              {result.policy_sections.map((s: any, i: number) => (
                <div key={i} style={{ marginBottom: 16, padding: 12, background: '#f8fafc', borderRadius: 6 }}>
                  <strong>
                    {s.section_number}. {s.title}
                  </strong>
                  <p style={{ marginTop: 6 }}>{s.content}</p>
                </div>
              ))}
            </>
          )}
          {result.roles_and_responsibilities && (
            <>
              <h3 className="h3">Roles and Responsibilities</h3>
              {result.roles_and_responsibilities.map((r: any, i: number) => (
                <div key={i}>
                  <strong>{r.role}:</strong>
                  <ul>
                    {(r.responsibilities || []).map((rs: string, j: number) => (
                      <li key={j}>{rs}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </>
          )}
          {result.enforcement && (
            <>
              <h3 className="h3">Enforcement</h3>
              <p>{result.enforcement}</p>
            </>
          )}
          {result.review_cycle && (
            <p style={{ marginTop: 12, color: '#64748b', fontSize: 13 }}>
              <strong>Review cycle:</strong> {result.review_cycle}
              {result.document_owner && ` · Owner: ${result.document_owner}`}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
