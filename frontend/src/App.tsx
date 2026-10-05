import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { LayoutDashboard, Package, Users, Mail, FileText, CheckSquare, Layers, Settings } from 'lucide-react';

import { DashboardPage } from './pages/DashboardPage';
import { ProductsPage } from './pages/ProductsPage';
import { SuppliersPage } from './pages/SuppliersPage';
import { EmailsPage } from './pages/EmailsPage';
import { CataloguesPage } from './pages/CataloguesPage';
import { ReviewPage } from './pages/ReviewPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  const [reviewCount, setReviewCount] = useState(0);

  useEffect(() => {
    fetch('/api/dashboard/stats')
      .then((res) => res.json())
      .then((data) => {
        if (data?.cards?.needs_review) {
          setReviewCount(data.cards.needs_review);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <BrowserRouter>
      <div className="app-container">
        {/* Sidebar */}
        <aside className="sidebar">
          {/* Main Brand Position — ONLY place where word Kinetix appears */}
          <div className="brand-header">
            <div className="brand-logo">K</div>
            <div className="brand-name">Kinetix</div>
          </div>

          <nav className="nav-menu">
            <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <LayoutDashboard size={18} />
              <span>Dashboard</span>
            </NavLink>

            <NavLink to="/products" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Package size={18} />
              <span>Products</span>
            </NavLink>

            <NavLink to="/suppliers" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Users size={18} />
              <span>Suppliers</span>
            </NavLink>

            <NavLink to="/emails" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Mail size={18} />
              <span>Emails</span>
            </NavLink>

            <NavLink to="/catalogues" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <FileText size={18} />
              <span>Catalogues</span>
            </NavLink>

            <NavLink to="/review" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <CheckSquare size={18} />
              <span>Review</span>
              {reviewCount > 0 && <span className="badge">{reviewCount}</span>}
            </NavLink>

            <NavLink to="/integrations" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Layers size={18} />
              <span>Integrations</span>
            </NavLink>

            <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Settings size={18} />
              <span>Settings</span>
            </NavLink>
          </nav>
        </aside>

        {/* Main Content Area */}
        <div className="main-content">
          <header className="top-bar">
            <div className="page-title">Mailbox Ingestion & Product Extraction</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
              Connected: exportdtp@gmail.com
            </div>
          </header>

          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/suppliers" element={<SuppliersPage />} />
            <Route path="/emails" element={<EmailsPage />} />
            <Route path="/catalogues" element={<CataloguesPage />} />
            <Route path="/review" element={<ReviewPage />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
};
