import { useEffect, useState } from 'react';

const empty = { control: '', owner: '', regulation: '', due_date: '', evidence: '', status: 'pending' };

export default function ControlAttestationQueue() {
  const [items, setItems] = useState<any[]>([]);
  const [summary, setSummary] = useState({ total: 0, blocked: 0, pending: 0 });
  const [form, setForm] = useState(empty);
  async function load() { const r = await fetch('/api/control-attestation-queue/'); const d = await r.json(); setItems(d.items || []); setSummary(d.summary || { total: 0, blocked: 0, pending: 0 }); }
  useEffect(() => { load(); }, []);
  async function submit(e: React.FormEvent) { e.preventDefault(); await fetch('/api/control-attestation-queue/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) }); setForm(empty); load(); }
  return <div className="container"><h1>Control Attestation Queue</h1><p>Evidence owners, due dates, and blocked attestations across regulations.</p>
    <div className="grid">{['total','blocked','pending'].map(k => <div className="card" key={k}><h3>{k}</h3><strong>{(summary as any)[k]}</strong></div>)}</div>
    <form className="card" onSubmit={submit}>{['control','owner','regulation','due_date','evidence'].map(f => <input key={f} placeholder={f} value={(form as any)[f]} onChange={e => setForm({ ...form, [f]: e.target.value })} />)}<select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}><option>pending</option><option>blocked</option><option>complete</option></select><button>Add Attestation</button></form>
    <table><thead><tr>{['Control','Owner','Regulation','Due','Evidence','Status'].map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{items.map(i => <tr key={i.id}><td>{i.control}</td><td>{i.owner}</td><td>{i.regulation}</td><td>{i.due_date}</td><td>{i.evidence}</td><td>{i.status}</td></tr>)}</tbody></table>
  </div>;
}
