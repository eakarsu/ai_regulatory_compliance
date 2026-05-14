import { useEffect, useState } from 'react';
import { ai, regulations } from '../services/api';

export default function AIGapAnalysis() {
  const [regs, setRegs] = useState<any[]>([]);
  const [regulationId, setRegulationId] = useState('');
  const [controlsText, setControlsText] = useState('');
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
      const controls = controlsText.split('\n').map((s) => s.trim()).filter(Boolean);
      const r: any = await ai.gapAnalysis(regulationId, controls);
      setResult(r.result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <h1 className="h1">Gap Analysis</h1>
      <p style={{ color: '#64748b', marginBottom: 16 }}>
        Compare your stated controls to a regulation's requirements.
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
          <label className="label">Stated Controls (one per line)</label>
          <textarea
            value={controlsText}
            onChange={(e) => setControlsText(e.target.value)}
            placeholder="Data encryption at rest using AES-256&#10;Multi-factor authentication for admin accounts"
            style={{ minHeight: 160 }}
          />
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy}>
            {busy ? 'Analyzing...' : 'Run Gap Analysis'}
          </button>
        </form>
      </div>

      {result && (
        <div className="card">
          <h2 className="h2">Gap Analysis Result</h2>
          <div className="row">
            <span className="badge badge-info">Gap Score: {result.gap_score}/100</span>
          </div>
          {result.overall_gap_summary && <p style={{ marginTop: 12 }}>{result.overall_gap_summary}</p>}
          {result.covered_requirements && (
            <>
              <h3 className="h3">Covered Requirements</h3>
              <ul>
                {result.covered_requirements.map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </>
          )}
          {result.gaps && (
            <>
              <h3 className="h3">Gaps</h3>
              <table>
                <thead>
                  <tr>
                    <th>Requirement</th>
                    <th>Severity</th>
                    <th>Remediation</th>
                    <th>Effort (days)</th>
                  </tr>
                </thead>
                <tbody>
                  {result.gaps.map((g: any, i: number) => (
                    <tr key={i}>
                      <td>
                        <strong>{g.requirement}</strong>
                        <br />
                        <span style={{ fontSize: 12, color: '#64748b' }}>{g.gap_description}</span>
                      </td>
                      <td>
                        <span
                          className={`badge badge-${
                            g.severity === 'critical' ? 'critical' :
                            g.severity === 'high' ? 'danger' :
                            g.severity === 'medium' ? 'warn' : 'gray'
                          }`}
                        >
                          {g.severity}
                        </span>
                      </td>
                      <td style={{ fontSize: 13 }}>{g.remediation}</td>
                      <td>{g.estimated_effort_days}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          {result.partial_coverage && result.partial_coverage.length > 0 && (
            <>
              <h3 className="h3">Partial Coverage</h3>
              <ul>
                {result.partial_coverage.map((p: any, i: number) => (
                  <li key={i}>
                    <strong>{p.requirement}:</strong> missing {p.what_is_missing}
                  </li>
                ))}
              </ul>
            </>
          )}
          {result.prioritized_remediation_plan && (
            <>
              <h3 className="h3">Prioritized Remediation Plan</h3>
              <ol>
                {result.prioritized_remediation_plan.map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
            </>
          )}
          <details style={{ marginTop: 16 }}>
            <summary>Raw JSON</summary>
            <div className="code">{JSON.stringify(result, null, 2)}</div>
          </details>
        </div>
      )}
    </div>
  );
}
