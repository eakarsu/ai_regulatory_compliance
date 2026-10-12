import { useEffect, useState } from 'react';
import AIReport from '../components/AIReport';
import NativeAIPresets from '../components/NativeAIPresets';
import { ai, regulations } from '../services/api';

const controlExamples = [
  { label: 'Security baseline', controls: 'AES-256 encryption for stored regulated data\nMulti-factor authentication for privileged accounts\nQuarterly user-access certification\nAnnual incident-response tabletop exercise' },
  { label: 'Privacy program', controls: 'Documented records of processing activities\nData-subject request intake and identity verification\nRetention schedule with quarterly deletion review\nVendor data-processing agreements reviewed annually' },
  { label: 'Audit readiness', controls: 'Control owners attest quarterly\nEvidence is retained in an immutable audit repository\nExceptions require risk-owner approval and an expiry date\nInternal audit tests critical controls annually' },
];

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
          <NativeAIPresets
            presets={controlExamples.map((example, index) => ({
              label: example.label,
              apply: () => {
                setRegulationId(String(regs[index % regs.length].id));
                setControlsText(example.controls);
                setResult(null);
                setError('');
              },
            }))}
            disabled={busy || regs.length === 0}
            note={regs.length ? 'Each example uses an existing regulation and fills the controls field.' : 'Examples become available after existing regulations load.'}
          />
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

      <AIReport response={result} title="Gap analysis result" />
    </div>
  );
}
