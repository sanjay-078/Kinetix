import React, { useEffect, useState } from 'react';
import { Activity, Server } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [diagnostics, setDiagnostics] = useState<any | null>(null);

  useEffect(() => {
    fetch('/api/diagnostics')
      .then((res) => res.json())
      .then((data) => setDiagnostics(data))
      .catch((e) => console.error(e));
  }, []);

  return (
    <div className="page-container">
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Application Settings</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-dim)', display: 'block', marginBottom: '0.4rem' }}>Target Mailbox Account</label>
            <input type="text" className="search-input" value="exportdtp@gmail.com" readOnly style={{ width: '100%' }} />
          </div>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-dim)', display: 'block', marginBottom: '0.4rem' }}>Extraction Strategy</label>
            <input type="text" className="search-input" value="Python Deterministic + Structured AI Fallback" readOnly style={{ width: '100%' }} />
          </div>
        </div>
      </div>

      {/* Admin Diagnostics Section */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Activity size={20} color="#6366f1" />
          <h3 style={{ fontSize: '1.1rem' }}>Admin Diagnostics</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Queue Depth</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>{diagnostics?.queue_depth ?? 0}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Active Workers</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>{diagnostics?.active_workers ?? 0}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Extraction Latency</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>{diagnostics?.extraction_latency_ms ?? 0} ms</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Database Latency</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>{diagnostics?.db_latency_ms ?? 0} ms</div>
          </div>
        </div>
      </div>
    </div>
  );
};
