import { useState } from 'react';
import { ai } from '../services/api';

export default function AIRiskAssessment() {
  const [orgType, setOrgType] = useState('');
  const [industry, setIndustry] = useState('');
  const [practicesText, setPracticesText] = useState('');
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    setResult(null);
    try {
      const practices = practicesText.split('\n').map((s) => s.trim()).filter(Boolean);
      const r: any = await ai.riskAssessment(orgType, industry, practices);
      setResult(r.result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <h1 className="h1">Organization Risk Assessment</h1>
      <p style={{ color: '#64748b', marginBottom: 16 }}>
        Profile your organization to identify applicable regulations and prioritized actions.
      </p>
      <div className="card">
        <form onSubmit={submit} className="col">
          <div className="grid grid-2">
            <div className="col">
              <label className="label">Organization Type</label>
              <input
                value={orgType}
                onChange={(e) => setOrgType(e.target.value)}
                placeholder="e.g. Public company, SMB, NGO"
                required
              />
            </div>
            <div className="col">
              <label className="label">Industry</label>
              <input
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="e.g. Healthcare, Finance, SaaS"
                required
              />
            </div>
          </div>
          <label className="label">Current Practices (one per line)</label>
          <textarea
            value={practicesText}
            onChange={(e) => setPracticesText(e.target.value)}
            placeholder="Encryption at rest&#10;Annual employee security training&#10;Quarterly access reviews"
            style={{ minHeight: 140 }}
          />
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy}>
            {busy ? 'Assessing...' : 'Run Risk Assessment'}
          </button>
        </form>
      </div>

      {result && (
        <div className="card">
          <h2 className="h2">Risk Assessment Result</h2>
          <div className="row">
            <span className="badge badge-info">Score: {result.overall_risk_score}/100</span>
            <span
              className={`badge badge-${
                result.risk_level === 'critical' ? 'critical' :
                result.risk_level === 'high' ? 'danger' :
                result.risk_level === 'medium' ? 'warn' : 'gray'
              }`}
            >
              {result.risk_level} risk
            </span>
            {result.estimated_compliance_cost && (
              <span className="badge badge-gray">Est. cost: {result.estimated_compliance_cost}</span>
            )}
          </div>
          {result.applicable_regulations && (
            <>
              <h3 className="h3">Applicable Regulations</h3>
              <ul>
                {result.applicable_regulations.map((r: string, i: number) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </>
          )}
          {result.compliance_gaps && (
            <>
              <h3 className="h3">Compliance Gaps</h3>
              <ul>
                {result.compliance_gaps.map((g: any, i: number) => (
                  <li key={i} style={{ marginBottom: 6 }}>
                    <span className={`badge badge-${g.priority === 'high' ? 'danger' : g.priority === 'medium' ? 'warn' : 'gray'}`}>
                      {g.priority}
                    </span>{' '}
                    <strong>{g.gap}</strong> ({g.regulation}) — {g.impact}
                  </li>
                ))}
              </ul>
            </>
          )}
          {result.immediate_actions && (
            <>
              <h3 className="h3">Immediate Actions</h3>
              <ol>
                {result.immediate_actions.map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
            </>
          )}
          {result.medium_term_roadmap && (
            <>
              <h3 className="h3">Medium-Term Roadmap (3-6 mo)</h3>
              <ol>
                {result.medium_term_roadmap.map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
            </>
          )}
          {result.top_risks && (
            <>
              <h3 className="h3">Top Risks</h3>
              <table>
                <thead>
                  <tr>
                    <th>Risk</th>
                    <th>Likelihood</th>
                    <th>Impact</th>
                  </tr>
                </thead>
                <tbody>
                  {result.top_risks.map((r: any, i: number) => (
                    <tr key={i}>
                      <td>{r.risk}</td>
                      <td>
                        <span
                          className={`badge badge-${r.likelihood === 'high' ? 'danger' : r.likelihood === 'medium' ? 'warn' : 'gray'}`}
                        >
                          {r.likelihood}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`badge badge-${r.impact === 'high' ? 'danger' : r.impact === 'medium' ? 'warn' : 'gray'}`}
                        >
                          {r.impact}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
