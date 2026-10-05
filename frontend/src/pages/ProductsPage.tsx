import React, { useEffect, useState } from 'react';
import { Search, ExternalLink, FileText, X } from 'lucide-react';
import { ProductItem } from '../types';

export const ProductsPage: React.FC = () => {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [search, setSearch] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<any | null>(null);

  const loadProducts = async () => {
    try {
      const url = search ? `/api/products?q=${encodeURIComponent(search)}` : '/api/products';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [search]);

  const handleSelectProduct = async (id: string) => {
    try {
      const res = await fetch(`/api/products/${id}`);
      if (res.ok) {
        const detail = await res.json();
        setSelectedProduct(detail);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="page-container">
      <div className="data-table-container">
        <div className="table-toolbar">
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', color: 'var(--text-dim)' }} />
            <input
              type="text"
              className="search-input"
              style={{ paddingLeft: '2.2rem' }}
              placeholder="Search products by name, model, SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginLeft: 'auto' }}>
            Showing {products.length} products
          </span>
        </div>

        <table>
          <thead>
            <tr>
              <th>Product Name</th>
              <th>Model</th>
              <th>Supplier</th>
              <th>Price</th>
              <th>MOQ</th>
              <th>Lead Time</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} onClick={() => handleSelectProduct(p.id)} style={{ cursor: 'pointer' }}>
                <td style={{ fontWeight: 600 }}>{p.name}</td>
                <td>{p.model || '—'}</td>
                <td>{p.supplier}</td>
                <td style={{ fontWeight: 600, color: '#34d399' }}>
                  {p.price !== null ? `${p.currency} ${p.price}` : 'Not provided'}
                </td>
                <td>{p.moq || '—'}</td>
                <td>{p.lead_time || '—'}</td>
                <td>
                  <button className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}>
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Product Detail Modal */}
      {selectedProduct && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div style={{
            background: '#121826', border: '1px solid var(--border-color)', borderRadius: '16px',
            width: '640px', maxWidth: '90vw', maxHeight: '90vh', overflowY: 'auto', padding: '1.5rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.25rem' }}>{selectedProduct.name}</h2>
              <X size={20} style={{ cursor: 'pointer' }} onClick={() => setSelectedProduct(null)} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Supplier</span>
                <div style={{ fontWeight: 600 }}>{selectedProduct.supplier?.name}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Model Number</span>
                <div style={{ fontWeight: 600 }}>{selectedProduct.model || 'Not provided'}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Price</span>
                <div style={{ fontWeight: 600, color: '#34d399' }}>
                  {selectedProduct.price ? `${selectedProduct.currency} ${selectedProduct.price}` : 'Not provided'}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>MOQ</span>
                <div style={{ fontWeight: 600 }}>{selectedProduct.moq || 'Not provided'}</div>
              </div>
            </div>

            {/* Dynamic Attributes */}
            {selectedProduct.dynamic_attributes?.length > 0 && (
              <div style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>Additional Specifications</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '8px' }}>
                  {selectedProduct.dynamic_attributes.map((attr: any) => (
                    <div key={attr.id} style={{ fontSize: '0.85rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>{attr.name}: </span>
                      <span style={{ fontWeight: 500 }}>{attr.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions Links */}
            <div style={{ display: 'flex', gap: '1rem' }}>
              {selectedProduct.catalogue_link && (
                <a href={selectedProduct.catalogue_link} target="_blank" rel="noreferrer" className="btn btn-secondary">
                  <FileText size={16} /> Open Catalogue PDF
                </a>
              )}
              {selectedProduct.source_email_link && (
                <a href={selectedProduct.source_email_link} target="_blank" rel="noreferrer" className="btn btn-secondary">
                  <ExternalLink size={16} /> Open Source Email
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
