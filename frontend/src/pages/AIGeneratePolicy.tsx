import { useEffect, useState } from 'react';
import AIReport from '../components/AIReport';
import NativeAIPresets from '../components/NativeAIPresets';
import { ai, regulations } from '../services/api';

const policyExamples = [
  {
    label: 'Healthcare policy',
    organizationName: 'Northstar Health Services',
    context: 'A 450-person healthcare software company operating in the United States and European Union. The policy applies to employees, contractors, cloud systems, and subprocessors handling patient or customer data.',
  },
  {
    label: 'Fintech policy',
    organizationName: 'Ledgerline Payments',
    context: 'A public payment processor with PCI DSS and SOX obligations. The company uses cloud infrastructure, outsourced customer support, and a formal three-lines-of-defense governance model.',
  },
  {
    label: 'Marketplace policy',
    organizationName: 'Harbor Market Europe',
    context: 'A 90-person online marketplace serving EU consumers. The policy must address privacy, supplier oversight, incident escalation, annual training, evidence retention, and executive approval.',
  },
];

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
          <NativeAIPresets
            presets={policyExamples.map((example, index) => ({
              label: example.label,
              apply: () => {
                setRegulationId(String(regs[index % regs.length].id));
                setOrgName(example.organizationName);
                setOrgContext(example.context);
                setResult(null);
                setError('');
              },
            }))}
            disabled={busy || regs.length === 0}
            note={regs.length ? 'Each example uses an existing regulation and fills the required and optional policy fields.' : 'Examples become available after existing regulations load.'}
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
        <>
          <div className="row" style={{ justifyContent: 'flex-end', marginBottom: 12 }}>
            <button type="button" onClick={downloadJSON}>Download JSON</button>
          </div>
          <AIReport response={result} title={result.policy_title || 'Generated policy'} />
        </>
      )}
    </div>
  );
}
