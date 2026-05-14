import { useState } from 'react';
import { ai } from '../services/api';

type ToolKey = 'cross-mapper' | 'readiness' | 'evidence' | 'sec-edgar';

export default function AIBacklogTools() {
  const [tab, setTab] = useState<ToolKey>('cross-mapper');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  // Cross-mapper
  const [regIds, setRegIds] = useState('');
  // Readiness
  const [scenario, setScenario] = useState('');
  const [event, setEvent] = useState('');
  const [readinessRegId, setReadinessRegId] = useState('');
  const [controlsText, setControlsText] = useState('');
  // Evidence extract
  const [extractedText, setExtractedText] = useState('');
  const [docType, setDocType] = useState('');
  const [evidenceRegId, setEvidenceRegId] = useState('');
  // SEC EDGAR
  const [cik, setCik] = useState('');

  const reset = () => {
    setError('');
    setResult(null);
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    reset();
    setBusy(true);
    try {
      let r: any;
      if (tab === 'cross-mapper') {
        const ids = regIds.split(/[,\s]+/).map((x) => x.trim()).filter(Boolean);
        r = await ai.crossRegulationMapper(ids);
      } else if (tab === 'readiness') {
        const controls = controlsText.split('\n').map((s) => s.trim()).filter(Boolean);
        r = await ai.readinessSimulator({
          scenario: scenario || undefined,
          event: event || undefined,
          regulation_id: readinessRegId || undefined,
          controls_in_place: controls,
        });
      } else if (tab === 'evidence') {
        if (!extractedText.trim()) throw new Error('extracted_text is required');
        r = await ai.evidenceExtract({
          extracted_text: extractedText,
          document_type: docType || undefined,
          regulation_id: evidenceRegId || undefined,
        });
      } else if (tab === 'sec-edgar') {
        r = await ai.secEdgarFeed(cik || undefined);
      }
      setResult(r);
    } catch (err: any) {
      setError(err.message || 'Request failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <h1 className="h1">AI Backlog Tools</h1>
      <p style={{ color: '#64748b', marginBottom: 16 }}>
        Cross-regulation mapping, readiness simulation, OCR evidence structuring, and external feed connectors.
      </p>
      <div className="row" style={{ gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {[
          { id: 'cross-mapper', label: 'Cross-Reg Mapper' },
          { id: 'readiness', label: 'Readiness Simulator' },
          { id: 'evidence', label: 'Evidence Extract (OCR)' },
          { id: 'sec-edgar', label: 'SEC EDGAR Feed' },
        ].map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => {
              setTab(t.id as ToolKey);
              reset();
            }}
            style={{
              background: tab === t.id ? '#2563eb' : '#e2e8f0',
              color: tab === t.id ? 'white' : '#1e293b',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="card">
        <form onSubmit={onSubmit} className="col">
          {tab === 'cross-mapper' && (
            <>
              <label className="label">Regulation IDs (comma or whitespace separated, optional - defaults to 5 most recent)</label>
              <input value={regIds} onChange={(e) => setRegIds(e.target.value)} placeholder="reg-id-1, reg-id-2" />
            </>
          )}
          {tab === 'readiness' && (
            <>
              <label className="label">Scenario</label>
              <input value={scenario} onChange={(e) => setScenario(e.target.value)} placeholder="surprise external audit next quarter" />
              <label className="label">Event</label>
              <input value={event} onChange={(e) => setEvent(e.target.value)} placeholder="regulatory inspection" />
              <label className="label">Regulation ID (optional)</label>
              <input value={readinessRegId} onChange={(e) => setReadinessRegId(e.target.value)} />
              <label className="label">Controls in place (one per line)</label>
              <textarea value={controlsText} onChange={(e) => setControlsText(e.target.value)} style={{ minHeight: 100 }} />
            </>
          )}
          {tab === 'evidence' && (
            <>
              <label className="label">OCR-extracted text *</label>
              <textarea
                value={extractedText}
                onChange={(e) => setExtractedText(e.target.value)}
                required
                style={{ minHeight: 180 }}
                placeholder="Paste text already extracted via OCR (Tesseract / vision model)"
              />
              <label className="label">Document type</label>
              <input value={docType} onChange={(e) => setDocType(e.target.value)} placeholder="e.g. signed policy, audit log, training cert" />
              <label className="label">Regulation ID (optional)</label>
              <input value={evidenceRegId} onChange={(e) => setEvidenceRegId(e.target.value)} />
            </>
          )}
          {tab === 'sec-edgar' && (
            <>
              <label className="label">CIK (Central Index Key, optional)</label>
              <input value={cik} onChange={(e) => setCik(e.target.value)} placeholder="0000320193" />
              <p style={{ color: '#64748b', fontSize: 13 }}>
                Requires <code>SEC_EDGAR_USER_AGENT</code> env var. Returns 503 with <code>missing</code> field when unset.
              </p>
            </>
          )}
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy}>
            {busy ? 'Running...' : 'Run'}
          </button>
        </form>
      </div>

      {result && (
        <div className="card">
          <h2 className="h2">Result</h2>
          <div className="code" style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(result, null, 2)}</div>
        </div>
      )}
    </div>
  );
}
