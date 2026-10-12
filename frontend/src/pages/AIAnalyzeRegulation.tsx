import { useState } from 'react';
import AIReport from '../components/AIReport';
import NativeAIPresets from '../components/NativeAIPresets';
import { ai } from '../services/api';

const examples = [
  {
    label: 'EU AI Act example',
    text: 'Article 9 — Risk management system. A risk management system shall be established, implemented, documented and maintained in relation to high-risk AI systems. It shall be a continuous iterative process planned and run throughout the entire lifecycle of the system, requiring regular systematic review and updating.',
  },
  {
    label: 'GDPR example',
    text: 'Article 32 — Security of processing. Taking into account the state of the art, implementation costs, and the nature, scope, context and purposes of processing, the controller and processor shall implement appropriate technical and organisational measures to ensure a level of security appropriate to the risk.',
  },
  {
    label: 'Vendor-control example',
    text: 'The organization must review critical service providers annually, document security and privacy controls, retain approval evidence, assign remediation owners, and notify the compliance lead of material control failures within five business days.',
  },
];

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
          <NativeAIPresets
            presets={examples.map((example) => ({
              label: example.label,
              apply: () => { setText(example.text); setResult(null); setError(''); },
            }))}
            disabled={busy}
          />
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

      <AIReport response={result} title="Regulation analysis result" />
    </div>
  );
}
