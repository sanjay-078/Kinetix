import React, { useEffect, useState } from 'react';
import { Mail, Sheet, RefreshCw, ExternalLink, AlertCircle, CheckCircle2, ShieldAlert, LogOut } from 'lucide-react';

export const IntegrationsPage: React.FC = () => {
  const [integrations, setIntegrations] = useState<any | null>(null);
  const [authStatus, setAuthStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncingSheets, setSyncingSheets] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadStatus = async () => {
    try {
      const [resInt, resAuth] = await Promise.all([
        fetch('/api/integrations/status'),
        fetch('/api/auth/status')
      ]);
      if (resInt.ok) {
        const data = await resInt.json();
        setIntegrations(data);
      }
      if (resAuth.ok) {
        const aData = await resAuth.json();
        setAuthStatus(aData);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadStatus();
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('status') === 'connected') {
      setSuccessMessage('Successfully authorized and connected Gmail account.');
    }
  }, []);

  const handleConnectGmail = async () => {
    setErrorMessage(null);
    setLoading(true);
    try {
      const res = await fetch('/api/auth/login');
      const data = await res.json();
      if (res.ok && data.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        setErrorMessage(data.detail || 'Failed to initialize Google OAuth connection.');
      }
    } catch (err: any) {
      setErrorMessage(err?.message || 'Network error connecting to OAuth server.');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await fetch('/api/auth/disconnect', { method: 'POST' });
      setSuccessMessage('Gmail account disconnected.');
      loadStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSyncSheets = async () => {
    setSyncingSheets(true);
    try {
      await fetch('/api/integrations/sheets/sync', { method: 'POST' });
      setSuccessMessage('Google Sheets synchronization complete.');
      loadStatus();
    } catch (e) {
      console.error(e);
    } finally {
      setSyncingSheets(false);
    }
  };

  const isConnected = authStatus?.connected || integrations?.gmail?.connected;
  const isOAuthConfigured = authStatus?.oauth_configured !== false;

  return (
    <div className="page-container">
      {errorMessage && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444',
          borderRadius: '12px', padding: '1rem', marginBottom: '1.5rem',
          display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#fca5a5'
        }}>
          <AlertCircle size={20} color="#ef4444" />
          <div style={{ fontSize: '0.9rem' }}>{errorMessage}</div>
        </div>
      )}

      {successMessage && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981',
          borderRadius: '12px', padding: '1rem', marginBottom: '1.5rem',
          display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#6ee7b7'
        }}>
          <CheckCircle2 size={20} color="#10b981" />
          <div style={{ fontSize: '0.9rem' }}>{successMessage}</div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
        {/* Gmail Integration Card */}
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: '16px', padding: '1.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <Mail size={24} color="#ea4335" />
            <div>
              <h3 style={{ fontSize: '1.1rem' }}>Gmail Mailbox Ingestion</h3>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                {integrations?.gmail?.account || 'exportdtp@gmail.com'}
              </span>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <span className={`status-tag ${isConnected ? 'status-relevant' : 'status-review'}`}>
              {isConnected ? 'Connected (Google OAuth 2.0)' : 'Awaiting OAuth Connection'}
            </span>
          </div>

          {!isConnected ? (
            <button
              className="btn btn-primary"
              style={{ width: '100%' }}
              onClick={handleConnectGmail}
              disabled={loading}
            >
              <Mail size={16} /> {loading ? 'Connecting...' : 'Connect Email'}
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                className="btn btn-secondary"
                style={{ flex: 1 }}
                onClick={() => fetch('/api/integrations/gmail/sync', { method: 'POST' }).then(() => loadStatus())}
              >
                <RefreshCw size={16} /> Scan Mailbox
              </button>
              <button
                className="btn btn-secondary"
                style={{ color: '#f87171' }}
                onClick={handleDisconnect}
              >
                <LogOut size={16} /> Disconnect
              </button>
            </div>
          )}
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
                {integrations?.google_sheets?.rows_synced ?? 0} Products & Catalogues Synced
              </span>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <span className="status-tag status-relevant">Idempotent Batch Sync Ready</span>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              className="btn btn-primary"
              style={{ flex: 1 }}
              onClick={handleSyncSheets}
              disabled={syncingSheets}
            >
              <RefreshCw size={16} /> {syncingSheets ? 'Syncing...' : 'Sync Now'}
            </button>
            <a
              href={integrations?.google_sheets?.sheet_url || '#'}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary"
            >
              <ExternalLink size={16} /> Open Sheet
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

