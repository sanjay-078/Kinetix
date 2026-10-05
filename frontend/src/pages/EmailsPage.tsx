import React, { useEffect, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { EmailItem } from '../types';

export const EmailsPage: React.FC = () => {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const loadEmails = async () => {
    try {
      const url = statusFilter !== 'all' ? `/api/emails?status=${statusFilter}` : '/api/emails';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setEmails(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadEmails();
  }, [statusFilter]);

  return (
    <div className="page-container">
      <div className="data-table-container">
        <div className="table-toolbar">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {['all', 'relevant', 'ignored', 'processed', 'review_required'].map((filter) => (
              <button
                key={filter}
                className={`btn ${statusFilter === filter ? 'btn-primary' : 'btn-secondary'}`}
                style={{ textTransform: 'capitalize', fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                onClick={() => setStatusFilter(filter)}
              >
                {filter.replace('_', ' ')}
              </button>
            ))}
          </div>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginLeft: 'auto' }}>
            {emails.length} Traceability Records
          </span>
        </div>

        <table>
          <thead>
            <tr>
              <th>Sender</th>
              <th>Subject</th>
              <th>Received Date</th>
              <th>Classification</th>
              <th>Products Found</th>
              <th>PDFs</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {emails.map((e) => (
              <tr key={e.id}>
                <td>
                  <div style={{ fontWeight: 600 }}>{e.sender_domain}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{e.sender}</div>
                </td>
                <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {e.subject}
                </td>
                <td style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                  {e.received_at ? new Date(e.received_at).toLocaleDateString() : '—'}
                </td>
                <td>
                  <span className={`status-tag status-${e.classification}`}>
                    {e.classification}
                  </span>
                </td>
                <td style={{ fontWeight: 600, textAlign: 'center' }}>{e.product_count}</td>
                <td style={{ textAlign: 'center' }}>{e.pdf_count}</td>
                <td>
                  <a href={e.source_email_link} target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}>
                    <ExternalLink size={14} /> Open Email
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
