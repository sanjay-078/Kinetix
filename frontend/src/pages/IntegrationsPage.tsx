import React, { useEffect, useState } from 'react';
import { Mail, Sheet, RefreshCw, ExternalLink } from 'lucide-react';

export const IntegrationsPage: React.FC = () => {
  const [integrations, setIntegrations] = useState<any | null>(null);

  const loadIntegrations = async () => {
    try {
      const res = await fetch('/api/integrations/status');
      if (res.ok) {
        const data = await res.json();
        setIntegrations(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadIntegrations();
  }, []);

  const handleConnectGmail = async () => {
    const res = await fetch('/api/auth/login');
    if (res.ok) {
      const data = await res.json();
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      }
    }
  };

  const handleSyncSheets = async () => {
    await fetch('/api/integrations/sheets/sync', { method: 'POST' });
    loadIntegrations();
  };

  return (
    <div className="page-container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
      {/* Gmail Integration Card */}
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
        borderRadius: '16px', padding: '1.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <Mail size={24} color="#ea4335" />
          <div>
            <h3 style={{ fontSize: '1.1rem' }}>Gmail Account</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
              {integrations?.gmail.account || 'exportdtp@gmail.com'}
            </span>
          </div>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <span className={`status-tag ${integrations?.gmail.connected ? 'status-relevant' : 'status-review'}`}>
            {integrations?.gmail.connected ? 'Connected (Google OAuth)' : 'Awaiting OAuth Connect'}
          </span>
        </div>

        <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleConnectGmail}>
          <Mail size={16} /> Connect Email
        </button>
      </div>

      {/* Google Sheets Integration Card */}
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
        borderRadius: '16px', padding: '1.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <Sheet size={24} color="#34a853" />
          <div>
            <h3 style={{ fontSize: '1.1rem' }}>Google Sheets Batch Sync</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
              {integrations?.google_sheets.rows_synced ?? 0} Rows Synchronized
            </span>
          </div>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <span className="status-tag status-relevant">Active (Batch Sync Ready)</span>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleSyncSheets}>
            <RefreshCw size={16} /> Sync Now
          </button>
          <a href={integrations?.google_sheets.sheet_url || '#'} target="_blank" rel="noreferrer" className="btn btn-secondary">
            <ExternalLink size={16} /> Open Sheet
          </a>
        </div>
      </div>
    </div>
  );
};
