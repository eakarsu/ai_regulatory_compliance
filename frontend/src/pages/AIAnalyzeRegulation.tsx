import { useState } from 'react';
import { ai } from '../services/api';

export default function AIAnalyzeRegulation() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    setResult(null);
    try {
      const r: any = await ai.analyzeRegulation(text);
      setResult(r.result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <h1 className="h1">Analyze Regulation Text</h1>
      <p style={{ color: '#64748b', marginBottom: 16 }}>
        Paste regulation text; Claude extracts requirements, risk areas, and compliance steps.
      </p>
      <div className="card">
        <form onSubmit={submit} className="col">
          <label className="label">Regulation Text</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            required
            style={{ minHeight: 200 }}
            placeholder="Paste the regulation text here..."
          />
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy}>
            {busy ? 'Analyzing...' : 'Analyze with Claude'}
          </button>
        </form>
      </div>

      {result && (
        <div className="card">
          <h2 className="h2">Analysis Result</h2>
          {result.summary && (
            <>
              <h3 className="h3">Summary</h3>
              <p>{result.summary}</p>
            </>
          )}
          {result.estimated_compliance_effort && (
            <div className="row" style={{ marginTop: 12 }}>
              <span
                className={`badge badge-${
                  result.estimated_compliance_effort === 'high' ? 'danger' :
                  result.estimated_compliance_effort === 'medium' ? 'warn' : 'gray'
                }`}
              >
                Effort: {result.estimated_compliance_effort}
              </span>
            </div>
          )}
          {result.key_requirements && (
            <>
              <h3 className="h3">Key Requirements</h3>
              <ul>
                {result.key_requirements.map((r: string, i: number) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </>
          )}
          {result.risk_areas && (
            <>
              <h3 className="h3">Risk Areas</h3>
              <ul>
                {result.risk_areas.map((ra: any, i: number) => (
                  <li key={i}>
                    <span
                      className={`badge badge-${
                        ra.risk_level === 'critical' ? 'critical' :
                        ra.risk_level === 'high' ? 'danger' :
                        ra.risk_level === 'medium' ? 'warn' : 'gray'
                      }`}
                    >
                      {ra.risk_level}
                    </span>{' '}
                    <strong>{ra.area}:</strong> {ra.description}
                  </li>
                ))}
              </ul>
            </>
          )}
          {result.compliance_steps && (
            <>
              <h3 className="h3">Compliance Steps</h3>
              <ol>
                {result.compliance_steps.map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
            </>
          )}
          {result.affected_business_functions && (
            <>
              <h3 className="h3">Affected Business Functions</h3>
              <p>{result.affected_business_functions.join(', ')}</p>
            </>
          )}
          {result.penalties_for_non_compliance && (
            <>
              <h3 className="h3">Penalties</h3>
              <p>{result.penalties_for_non_compliance}</p>
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
