import { useEffect, useRef, useState } from 'react';
import { ai, assessments, regulations } from '../services/api';

function generateSessionId() {
  return `session-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function AIChat() {
  const [messages, setMessages] = useState<{ role: string; content: string; id?: string }[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [sessionId] = useState(generateSessionId);
  const [regulationsList, setRegulationsList] = useState<any[]>([]);
  const [assessmentsList, setAssessmentsList] = useState<any[]>([]);
  const [contextRegId, setContextRegId] = useState('');
  const [contextAssId, setContextAssId] = useState('');
  const [error, setError] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    regulations.list({ limit: 50 }).then((r: any) => setRegulationsList(r.data || [])).catch(() => {});
    assessments.list({ limit: 50 }).then((r: any) => setAssessmentsList(r.data || [])).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || busy) return;
    const userMsg = input.trim();
    setInput('');
    setError('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setBusy(true);

    try {
      const res: any = await ai.chat(
        userMsg,
        sessionId,
        contextAssId || undefined,
        contextRegId || undefined,
      );
      setMessages(prev => [...prev, { role: 'assistant', content: res.content, id: res.id }]);
    } catch (err: any) {
      setError(err.message);
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
    } finally {
      setBusy(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="container">
      <h1 className="h1">Compliance Chat Assistant</h1>
      <p style={{ color: '#64748b', marginBottom: 16 }}>
        Ask any compliance question. Optionally select context for more targeted answers.
      </p>

      <div className="card" style={{ marginBottom: 12 }}>
        <div className="grid grid-2">
          <div className="col">
            <label className="label">Context Regulation (optional)</label>
            <select value={contextRegId} onChange={e => setContextRegId(e.target.value)}>
              <option value="">None</option>
              {regulationsList.map((r: any) => (
                <option key={r.id} value={r.id}>{r.title}</option>
              ))}
            </select>
          </div>
          <div className="col">
            <label className="label">Context Assessment (optional)</label>
            <select value={contextAssId} onChange={e => setContextAssId(e.target.value)}>
              <option value="">None</option>
              {assessmentsList.map((a: any) => (
                <option key={a.id} value={a.id}>
                  {a.regulation_title || a.id.slice(0, 8)} — {a.status} ({a.overall_score}/100)
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div
        className="card"
        style={{
          minHeight: 400,
          maxHeight: 500,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          padding: 16,
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: '#94a3b8', textAlign: 'center', marginTop: 'auto', marginBottom: 'auto' }}>
            Start the conversation. Ask about regulations, compliance requirements, or how to improve your score.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '75%',
                padding: '10px 14px',
                borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                background: msg.role === 'user' ? '#2563eb' : '#f1f5f9',
                color: msg.role === 'user' ? 'white' : '#0f172a',
                fontSize: 14,
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {busy && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ padding: '10px 14px', borderRadius: '18px 18px 18px 4px', background: '#f1f5f9', fontSize: 14, color: '#64748b' }}>
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <div className="error" style={{ marginBottom: 8 }}>{error}</div>}

      <div className="card" style={{ padding: 12 }}>
        <div className="row">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask a compliance question... (Enter to send, Shift+Enter for new line)"
            style={{ flex: 1, minHeight: 60, resize: 'vertical' }}
            disabled={busy}
          />
          <button onClick={send} disabled={busy || !input.trim()} style={{ alignSelf: 'flex-end', padding: '10px 20px' }}>
            Send
          </button>
        </div>
      </div>

      <div style={{ marginTop: 8 }}>
        <strong style={{ fontSize: 13 }}>Example questions:</strong>
        <div className="row" style={{ flexWrap: 'wrap', marginTop: 6, gap: 6 }}>
          {[
            'What are the top 3 things I need to do for GDPR compliance?',
            'How does HIPAA differ from GDPR for data handling?',
            'What is a Data Protection Impact Assessment?',
            'How often should I conduct security risk assessments for PCI DSS?',
          ].map(q => (
            <button
              key={q}
              className="secondary"
              style={{ fontSize: 12, padding: '4px 10px' }}
              onClick={() => setInput(q)}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
