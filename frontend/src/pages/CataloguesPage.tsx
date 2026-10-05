import React, { useEffect, useState } from 'react';
import { FileText, Download } from 'lucide-react';
import { CatalogueItem } from '../types';

export const CataloguesPage: React.FC = () => {
  const [catalogues, setCatalogues] = useState<CatalogueItem[]>([]);

  useEffect(() => {
    fetch('/api/catalogues')
      .then((res) => res.json())
      .then((data) => setCatalogues(data))
      .catch((e) => console.error(e));
  }, []);

  return (
    <div className="page-container">
      <div className="data-table-container">
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Supplier</th>
              <th>File Size</th>
              <th>Saved Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {catalogues.map((cat) => (
              <tr key={cat.id}>
                <td style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileText size={18} color="#f43f5e" />
                  {cat.filename}
                </td>
                <td>{cat.supplier}</td>
                <td style={{ color: 'var(--text-dim)' }}>
                  {Math.round((cat.file_size || 1024) / 1024)} KB
                </td>
                <td style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                  {cat.created_at ? new Date(cat.created_at).toLocaleDateString() : '—'}
                </td>
                <td>
                  <a href={cat.web_view_link} target="_blank" rel="noreferrer" className="btn btn-primary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}>
                    <Download size={14} /> Open PDF
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
