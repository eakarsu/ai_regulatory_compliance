import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { calendar } from '../services/api';

export default function CalendarPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    calendar.get(year, month)
      .then((r: any) => setEvents(r.events || []))
      .finally(() => setLoading(false));
  }, [year, month]);

  const prevMonth = () => {
    if (month === 1) { setYear(y => y - 1); setMonth(12); }
    else setMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (month === 12) { setYear(y => y + 1); setMonth(1); }
    else setMonth(m => m + 1);
  };

  const monthName = new Date(year, month - 1).toLocaleString('default', { month: 'long' });

  // Group events by date
  const byDate: Record<string, any[]> = {};
  for (const e of events) {
    byDate[e.date] = [...(byDate[e.date] || []), e];
  }

  return (
    <div className="container">
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 className="h1" style={{ marginBottom: 0 }}>Compliance Calendar</h1>
        <div className="row">
          <button className="secondary" onClick={prevMonth}>‹ Prev</button>
          <span style={{ fontWeight: 600, minWidth: 140, textAlign: 'center' }}>
            {monthName} {year}
          </span>
          <button className="secondary" onClick={nextMonth}>Next ›</button>
        </div>
      </div>

      {loading ? (
        <p style={{ color: '#64748b' }}>Loading...</p>
      ) : events.length === 0 ? (
        <div className="card">
          <p style={{ color: '#64748b' }}>
            No compliance events in {monthName} {year}. Add review dates to your assessments.
          </p>
        </div>
      ) : (
        Object.entries(byDate)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([date, dayEvents]) => (
            <div className="card" key={date} style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8, color: '#1e293b' }}>
                {new Date(date + 'T00:00:00').toLocaleDateString('default', {
                  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
                })}
              </div>
              <ul style={{ listStyle: 'none' }}>
                {dayEvents.map((ev: any, i: number) => (
                  <li key={i} style={{ padding: '8px 0', borderBottom: i < dayEvents.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                    <div className="row">
                      <span
                        className={`badge badge-${
                          ev.severity === 'critical' ? 'critical' :
                          ev.severity === 'warning' ? 'warn' :
                          ev.type === 'effective_date' ? 'info' : 'gray'
                        }`}
                      >
                        {ev.type.replace(/_/g, ' ')}
                      </span>
                      <Link to={ev.link} style={{ fontWeight: 500 }}>
                        {ev.title}
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))
      )}

      {events.length > 0 && (
        <div className="card" style={{ background: '#f8fafc' }}>
          <strong>Legend: </strong>
          <span className="badge badge-critical" style={{ marginRight: 8 }}>overdue</span>
          <span className="badge badge-warn" style={{ marginRight: 8 }}>review due</span>
          <span className="badge badge-info">effective date</span>
        </div>
      )}
    </div>
  );
}
