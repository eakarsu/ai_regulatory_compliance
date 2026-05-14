import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { assessments, evidence, reports, riskItems } from '../services/api';

export default function AssessmentDetail() {
  const { id } = useParams<{ id: string }>();
  const [a, setA] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [evidenceList, setEvidenceList] = useState<any[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'risks' | 'evidence' | 'history'>('overview');
  const [reportTemplate, setReportTemplate] = useState<'executive' | 'technical' | 'audit'>('executive');
  const [generatingReport, setGeneratingReport] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => {
    if (!id) return;
    assessments.get(id).then((r: any) => setA(r));
    assessments.history(id).then((h: any[]) => setHistory(h)).catch(() => {});
    evidence.byAssessment(id).then((e: any[]) => setEvidenceList(e)).catch(() => {});
  };
  useEffect(load, [id]);

  const runAI = async () => {
    setError('');
    setRunning(true);
    try {
      const r: any = await assessments.runAI(id!);
      setA(r);
      assessments.history(id!).then(setHistory).catch(() => {});
    } catch (err: any) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  const updateRiskItem = async (riId: string, status: string) => {
    await riskItems.update(riId, { status });
    load();
  };

  const downloadReport = async () => {
    setGeneratingReport(true);
    try {
      const text = await reports.assessment(id!, reportTemplate);
      const blob = new Blob([text], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `compliance-report-${id!.slice(0, 8)}-${reportTemplate}.md`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setGeneratingReport(false);
    }
  };

  const uploadEvidence = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !id) return;
    try {
      await evidence.upload(id, file);
      evidence.byAssessment(id).then(setEvidenceList).catch(() => {});
    } catch (err: any) {
      setError(err.message);
    }
    if (fileRef.current) fileRef.current.value = '';
  };

  if (!a) return <div className="container">Loading...</div>;

  const statusBadge = (status: string) => {
    if (status === 'compliant') return <span className="badge badge-success">Compliant</span>;
    if (status === 'partial') return <span className="badge badge-warn">Partial</span>;
    if (status === 'non_compliant') return <span className="badge badge-danger">Non-Compliant</span>;
    return <span className="badge badge-gray">{status}</span>;
  };

  const tabs = ['overview', 'risks', 'evidence', 'history'] as const;

  return (
    <div className="container">
      <Link to="/assessments">&larr; Back to assessments</Link>
      <div className="card" style={{ marginTop: 12 }}>
        <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
          <div>
            <h1 className="h1" style={{ marginBottom: 4 }}>
              {a.regulation_title || 'Assessment'}
            </h1>
            <div className="row">
              {statusBadge(a.status)}
              <span className="badge badge-info">Score: {a.overall_score}/100</span>
              {a.next_review_date && (
                <span className={`badge ${new Date(a.next_review_date) < new Date() ? 'badge-danger' : 'badge-gray'}`}>
                  Next Review: {new Date(a.next_review_date).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
          <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
            <select
              value={reportTemplate}
              onChange={e => setReportTemplate(e.target.value as any)}
              style={{ width: 130 }}
            >
              <option value="executive">Executive</option>
              <option value="technical">Technical</option>
              <option value="audit">Audit</option>
            </select>
            <button className="secondary" onClick={downloadReport} disabled={generatingReport}>
              {generatingReport ? 'Generating...' : 'Download Report'}
            </button>
            <button onClick={runAI} disabled={running}>
              {running ? 'Running AI...' : 'Run AI Assessment'}
            </button>
          </div>
        </div>
        {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
      </div>

      {/* Score bar */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ flex: 1, background: '#e2e8f0', borderRadius: 8, height: 16, overflow: 'hidden' }}>
            <div
              style={{
                height: '100%',
                width: `${a.overall_score}%`,
                background: a.overall_score >= 80 ? '#059669' : a.overall_score >= 50 ? '#d97706' : '#dc2626',
                transition: 'width 0.5s',
              }}
            />
          </div>
          <span style={{ fontWeight: 700, fontSize: 20 }}>{a.overall_score}/100</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="row" style={{ marginBottom: 0, gap: 0 }}>
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              borderRadius: 0,
              background: activeTab === tab ? '#1e40af' : '#e2e8f0',
              color: activeTab === tab ? 'white' : '#1e293b',
              padding: '8px 20px',
              fontWeight: activeTab === tab ? 600 : 400,
              borderRight: '1px solid #cbd5e1',
            }}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab === 'risks' && a.risk_items?.length ? ` (${a.risk_items.length})` : ''}
            {tab === 'evidence' ? ` (${evidenceList.length})` : ''}
            {tab === 'history' ? ` (${history.length})` : ''}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <>
          {a.findings && a.findings.length > 0 && (
            <div className="card">
              <h2 className="h2">Findings</h2>
              <ul>
                {a.findings.map((f: any, i: number) => (
                  <li key={i} style={{ padding: 8 }}>
                    <span className={`badge badge-${f.severity === 'critical' ? 'critical' : f.severity === 'high' ? 'danger' : f.severity === 'medium' ? 'warn' : 'gray'}`}>
                      {f.severity}
                    </span>{' '}
                    <strong>{f.area}:</strong> {f.observation}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {a.recommendations && a.recommendations.length > 0 && (
            <div className="card">
              <h2 className="h2">Recommendations</h2>
              <ul>
                {a.recommendations.map((r: any, i: number) => (
                  <li key={i} style={{ padding: 8 }}>
                    <span className={`badge badge-${r.priority === 'high' ? 'danger' : r.priority === 'medium' ? 'warn' : 'gray'}`}>
                      {r.priority}
                    </span>{' '}
                    {r.action} <em style={{ color: '#64748b' }}>({r.timeline})</em>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {activeTab === 'risks' && (
        <div className="card">
          <h2 className="h2">Risk Items</h2>
          {(!a.risk_items || a.risk_items.length === 0) ? (
            <p style={{ color: '#64748b' }}>No risk items. Run AI assessment to populate.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Risk Level</th>
                  <th>Status</th>
                  <th>Mitigation</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {a.risk_items.map((ri: any) => (
                  <tr key={ri.id}>
                    <td>
                      <strong>{ri.title}</strong>
                      <br />
                      <span style={{ fontSize: 12, color: '#64748b' }}>{ri.description}</span>
                    </td>
                    <td>
                      <span className={`badge badge-${ri.risk_level === 'critical' ? 'critical' : ri.risk_level === 'high' ? 'danger' : ri.risk_level === 'medium' ? 'warn' : 'gray'}`}>
                        {ri.risk_level}
                      </span>
                    </td>
                    <td>
                      <span className={`badge badge-${ri.status === 'mitigated' ? 'success' : ri.status === 'accepted' ? 'gray' : 'warn'}`}>
                        {ri.status}
                      </span>
                    </td>
                    <td style={{ fontSize: 13, maxWidth: 200 }}>{ri.mitigation_plan}</td>
                    <td>
                      <div className="row" style={{ gap: 4 }}>
                        {ri.status !== 'mitigated' && (
                          <button className="success" style={{ fontSize: 11, padding: '3px 8px' }} onClick={() => updateRiskItem(ri.id, 'mitigated')}>
                            Mitigate
                          </button>
                        )}
                        {ri.status !== 'accepted' && (
                          <button className="secondary" style={{ fontSize: 11, padding: '3px 8px' }} onClick={() => updateRiskItem(ri.id, 'accepted')}>
                            Accept
                          </button>
                        )}
                        {ri.status !== 'open' && (
                          <button style={{ fontSize: 11, padding: '3px 8px' }} onClick={() => updateRiskItem(ri.id, 'open')}>
                            Reopen
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'evidence' && (
        <div className="card">
          <div className="row" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
            <h2 className="h2" style={{ marginBottom: 0 }}>Evidence</h2>
            <label style={{ cursor: 'pointer' }}>
              <button className="secondary" onClick={() => fileRef.current?.click()}>
                Upload Evidence
              </button>
              <input ref={fileRef} type="file" style={{ display: 'none' }} onChange={uploadEvidence} />
            </label>
          </div>
          {evidenceList.length === 0 ? (
            <p style={{ color: '#64748b' }}>No evidence files attached. Upload screenshots, audit reports, or certificates.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>File</th>
                  <th>Size</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Uploaded</th>
                </tr>
              </thead>
              <tbody>
                {evidenceList.map((e: any) => (
                  <tr key={e.id}>
                    <td><strong>{e.file_name}</strong></td>
                    <td>{Math.round(e.file_size / 1024)} KB</td>
                    <td>{e.mime_type || '-'}</td>
                    <td style={{ fontSize: 13 }}>{e.description || '-'}</td>
                    <td>{new Date(e.uploaded_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="card">
          <h2 className="h2">Score History</h2>
          {history.length === 0 ? (
            <p style={{ color: '#64748b' }}>No history yet. Run AI assessment to start tracking.</p>
          ) : (
            <>
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Score</th>
                    <th>Status</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((snap: any) => (
                    <tr key={snap.id}>
                      <td>{new Date(snap.snapshot_at).toLocaleDateString()}</td>
                      <td>
                        <strong>{snap.score}</strong>/100
                        <div style={{ display: 'inline-block', marginLeft: 8, width: 60, height: 8, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden', verticalAlign: 'middle' }}>
                          <div style={{ height: '100%', width: `${snap.score}%`, background: snap.score >= 80 ? '#059669' : snap.score >= 50 ? '#d97706' : '#dc2626' }} />
                        </div>
                      </td>
                      <td>
                        <span className={`badge badge-${snap.status === 'compliant' ? 'success' : snap.status === 'partial' ? 'warn' : 'danger'}`}>
                          {snap.status}
                        </span>
                      </td>
                      <td style={{ fontSize: 13, color: '#64748b' }}>{snap.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {history.length >= 2 && (
                <div style={{ marginTop: 12, padding: 12, background: '#f8fafc', borderRadius: 8 }}>
                  <strong>Trend: </strong>
                  {(() => {
                    const first = history[0].score;
                    const last = history[history.length - 1].score;
                    const diff = last - first;
                    return diff > 0
                      ? <span style={{ color: '#059669' }}>+{diff} points improvement since first assessment</span>
                      : diff < 0
                      ? <span style={{ color: '#dc2626' }}>{diff} points decline since first assessment</span>
                      : <span style={{ color: '#64748b' }}>No change</span>;
                  })()}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
