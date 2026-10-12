import { useState } from 'react';
import AIReport from '../components/AIReport';
import NativeAIPresets from '../components/NativeAIPresets';
import { ai } from '../services/api';

const examples = [
  {
    label: 'Healthcare SaaS',
    organizationType: 'Private mid-market company processing patient support data',
    industry: 'Healthcare software as a service',
    practices: 'Encryption at rest and in transit\nQuarterly privileged-access reviews\nAnnual HIPAA workforce training\nDocumented incident-response exercises',
  },
  {
    label: 'Public fintech',
    organizationType: 'Public company with regulated payment operations',
    industry: 'Financial technology and payment processing',
    practices: 'Multi-factor authentication for all administrators\nPCI DSS quarterly vulnerability scans\nSOX change approvals retained for seven years\nAnnual vendor due-diligence reviews',
  },
  {
    label: 'EU marketplace',
    organizationType: 'Private small business serving consumers in the European Union',
    industry: 'E-commerce marketplace',
    practices: 'Data processing inventory reviewed semiannually\nConsent and deletion-request workflow\nMonthly cloud access review\nSupplier privacy clauses and breach notification terms',
  },
];

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
          <NativeAIPresets
            presets={examples.map((example) => ({
              label: example.label,
              apply: () => {
                setOrgType(example.organizationType);
                setIndustry(example.industry);
                setPracticesText(example.practices);
                setResult(null);
                setError('');
              },
            }))}
            disabled={busy}
          />
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

      <AIReport response={result} title="Risk assessment result" />
    </div>
  );
}
