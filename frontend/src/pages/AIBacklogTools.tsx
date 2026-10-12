import { useEffect, useState } from 'react';
import AIReport from '../components/AIReport';
import NativeAIPresets, { type NativePreset } from '../components/NativeAIPresets';
import { ai, regulations } from '../services/api';

type ToolKey = 'cross-mapper' | 'readiness' | 'evidence' | 'sec-edgar';

const readinessExamples = [
  { label: 'External audit', scenario: 'Surprise external audit scheduled for the next quarter', event: 'Regulatory inspection and evidence sampling', controls: 'Quarterly control-owner attestations\nCentral evidence repository\nAnnual internal audit testing\nDocumented exception approvals' },
  { label: 'Acquisition review', scenario: 'Compliance readiness review before acquiring a regulated software vendor', event: 'Pre-close due-diligence committee review', controls: 'Vendor risk tiering\nSecurity questionnaire and evidence review\nContractual audit rights\nRemediation tracking with accountable owners' },
  { label: 'Incident follow-up', scenario: 'Regulator requests proof of corrective actions after a reportable security incident', event: 'Thirty-day remediation evidence submission', controls: 'Incident response plan\nForensic evidence retention\nRoot-cause review\nExecutive remediation approval' },
];

const evidenceExamples = [
  { label: 'Access review', documentType: 'Quarterly access review certification', text: 'Review period: Q3 2026. System: Customer Data Platform. Reviewer: Jordan Lee, Control Owner. 47 active accounts reviewed; 3 access removals approved; tickets IAM-2041, IAM-2042, and IAM-2047. Review completed 2026-09-28. Evidence owner confirmed completeness.' },
  { label: 'Training record', documentType: 'Annual compliance training completion report', text: 'Course: 2026 Privacy and Security Fundamentals. Assigned employees: 186. Completed: 181. Exceptions: 5 employees on approved leave with completion due 2026-10-21. Report approved by the Compliance Director on 2026-10-02.' },
  { label: 'Change approval', documentType: 'Production change approval record', text: 'Change CHG-8821 updates encryption key rotation from 180 to 90 days. Security review passed 2026-09-14. Testing evidence attached under TEST-441. Approved by Engineering and Compliance. Production deployment window: 2026-09-20 02:00 UTC.' },
];

const cikExamples = [
  { label: 'Apple filing feed', cik: '0000320193' },
  { label: 'Microsoft filing feed', cik: '0000789019' },
  { label: 'Alphabet filing feed', cik: '0001652044' },
];

export default function AIBacklogTools() {
  const [tab, setTab] = useState<ToolKey>('cross-mapper');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);
  const [regulationsList, setRegulationsList] = useState<any[]>([]);

  useEffect(() => {
    regulations.list({ limit: 100 }).then((response: any) => setRegulationsList(response.data || [])).catch(() => setRegulationsList([]));
  }, []);

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

  const presets: NativePreset[] = tab === 'cross-mapper'
    ? ['Compare primary pair', 'Compare alternate pair', 'Compare three frameworks'].map((label, index) => ({
        label,
        apply: () => {
          const count = index === 2 ? Math.min(3, regulationsList.length) : 2;
          const ids = Array.from({ length: count }, (_, offset) => regulationsList[(index + offset) % regulationsList.length].id);
          setRegIds(ids.join(', '));
          reset();
        },
      }))
    : tab === 'readiness'
      ? readinessExamples.map((example, index) => ({
          label: example.label,
          apply: () => {
            setScenario(example.scenario);
            setEvent(example.event);
            setReadinessRegId(String(regulationsList[index % regulationsList.length].id));
            setControlsText(example.controls);
            reset();
          },
        }))
      : tab === 'evidence'
        ? evidenceExamples.map((example, index) => ({
            label: example.label,
            apply: () => {
              setExtractedText(example.text);
              setDocType(example.documentType);
              setEvidenceRegId(String(regulationsList[index % regulationsList.length].id));
              reset();
            },
          }))
        : cikExamples.map((example) => ({
            label: example.label,
            apply: () => { setCik(example.cik); reset(); },
          }));
  const needsRegulations = tab !== 'sec-edgar';
  const presetsDisabled = busy || (tab === 'cross-mapper' ? regulationsList.length < 2 : needsRegulations && regulationsList.length === 0);

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
          <NativeAIPresets
            presets={presets}
            disabled={presetsDisabled}
            note={needsRegulations && presetsDisabled && !busy ? 'Examples become available after the required existing regulation records load.' : 'Each example fills every field shown for the selected tool, including optional fields.'}
          />
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

      <AIReport response={result} title={`${[
        ['cross-mapper', 'Cross-regulation mapping'],
        ['readiness', 'Readiness simulation'],
        ['evidence', 'Evidence extraction'],
        ['sec-edgar', 'SEC EDGAR feed'],
      ].find(([key]) => key === tab)?.[1]} result`} />
    </div>
  );
}
