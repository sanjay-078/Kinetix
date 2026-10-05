import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';
import { ReviewItem } from '../types';

export const ReviewPage: React.FC = () => {
  const [items, setItems] = useState<ReviewItem[]>([]);

  const loadItems = async () => {
    try {
      const res = await fetch('/api/review');
      if (res.ok) {
        const data = await res.json();
        setItems(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadItems();
  }, []);

  const handleConfirm = async (id: string) => {
    await fetch(`/api/review/${id}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'confirmed' })
    });
    loadItems();
  };

  return (
    <div className="page-container">
      {items.length === 0 ? (
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: '16px', padding: '3rem', textAlign: 'center'
        }}>
          <CheckCircle size={48} color="#10b981" style={{ marginBottom: '1rem' }} />
          <h3>All Extractions Confirmed</h3>
          <p style={{ color: 'var(--text-dim)', marginTop: '0.5rem' }}>
            There are no uncertain extraction cases requiring manual review.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {items.map((item) => (
            <div key={item.id} style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '12px', padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <AlertCircle size={18} color="#f59e0b" />
                  <span style={{ fontWeight: 600 }}>{item.email?.subject || 'Uncertain Extraction'}</span>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                  Reason: {item.uncertainty_reason} (Confidence: {Math.round(item.confidence * 100)}%)
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button className="btn btn-primary" onClick={() => handleConfirm(item.id)}>
                  Confirm & Save
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
