import React, { useEffect, useState } from 'react';
import { Package, Users, Mail, FileText, AlertCircle, Play, CheckCircle, RefreshCw } from 'lucide-react';
import { DashboardStats } from '../types';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/dashboard/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStats();
    // Subscribe to SSE stream for real-time live ETA & progress updates
    const eventSource = new EventSource('/api/dashboard/stream');
    eventSource.onmessage = (event) => {
      const liveProgress = JSON.parse(event.data);
      setStats((prev) => prev ? { ...prev, live_progress: liveProgress } : prev);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const handleStartSync = async () => {
    await fetch('/api/dashboard/start-sync', { method: 'POST' });
    fetchStats();
  };

  const progress = stats?.live_progress;
  const total = progress?.total_discovered || 1;
  const scanned = progress?.scanned_count || 0;
  const pct = Math.min(100, Math.round((scanned / total) * 100));

  return (
    <div className="page-container">
      {/* Top Overview Cards */}
      <div className="card-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span>Products</span>
            <Package size={20} color="#6366f1" />
          </div>
          <div className="stat-value">{stats?.cards.products ?? 0}</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Suppliers</span>
            <Users size={20} color="#06b6d4" />
          </div>
          <div className="stat-value">{stats?.cards.suppliers ?? 0}</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Emails Processed</span>
            <Mail size={20} color="#10b981" />
          </div>
          <div className="stat-value">{stats?.cards.emails_processed ?? 0}</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Catalogues</span>
            <FileText size={20} color="#3b82f6" />
          </div>
          <div className="stat-value">{stats?.cards.catalogues ?? 0}</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Needs Review</span>
            <AlertCircle size={20} color="#f59e0b" />
          </div>
          <div className="stat-value">{stats?.cards.needs_review ?? 0}</div>
        </div>
      </div>

      {/* Live Processing Panel */}
      <div className="progress-section">
        <div className="progress-header">
          <div>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>Mailbox Processing</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
              {progress?.current_status_label || 'Processing normally'}
            </p>
          </div>
          <button className="btn btn-primary" onClick={handleStartSync}>
            <Play size={16} /> Run Sync Now
          </button>
        </div>

        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${pct}%` }}></div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Discovered Mail</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>{progress?.total_discovered ?? 0}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Scanned & Filtered</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>{scanned}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Irrelevant Ignored</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text-muted)' }}>{progress?.irrelevant_count ?? 0}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Supplier Emails</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem', color: '#34d399' }}>{progress?.supplier_email_count ?? 0}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Processing Speed</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>{progress?.current_speed ?? 0} msgs/s</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Estimated Remaining</span>
            <div style={{ fontWeight: 600, fontSize: '1.1rem', color: '#818cf8' }}>{progress?.eta_seconds ?? 0}s</div>
          </div>
        </div>
      </div>
    </div>
  );
};
