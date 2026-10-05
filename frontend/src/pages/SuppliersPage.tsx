import React, { useEffect, useState } from 'react';
import { SupplierItem } from '../types';

export const SuppliersPage: React.FC = () => {
  const [suppliers, setSuppliers] = useState<SupplierItem[]>([]);

  useEffect(() => {
    fetch('/api/suppliers')
      .then((res) => res.json())
      .then((data) => setSuppliers(data))
      .catch((e) => console.error(e));
  }, []);

  return (
    <div className="page-container">
      <div className="data-table-container">
        <table>
          <thead>
            <tr>
              <th>Supplier Name</th>
              <th>Domain</th>
              <th>Primary Email</th>
              <th>Products</th>
              <th>Emails Received</th>
              <th>Catalogues</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((s) => (
              <tr key={s.id}>
                <td style={{ fontWeight: 600 }}>{s.name}</td>
                <td style={{ color: 'var(--text-muted)' }}>{s.domain}</td>
                <td>{s.primary_email || '—'}</td>
                <td style={{ fontWeight: 600, color: '#818cf8' }}>{s.product_count}</td>
                <td>{s.email_count}</td>
                <td>{s.catalogue_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
