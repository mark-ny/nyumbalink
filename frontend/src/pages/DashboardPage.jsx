import React from 'react';
import { Link } from 'react-router-dom';
import useAuthStore from '../hooks/useAuthStore';

export default function DashboardPage() {
  const { user } = useAuthStore();
  return (
    <div style={{ maxWidth: 900, margin: '40px auto', padding: '0 20px' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Dashboard</h1>
      <p style={{ color: '#6b7280', marginBottom: 32 }}>Welcome back, {user?.name}</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        {[
          { label: 'My Listings', to: '/dashboard/create', icon: '🏠' },
          { label: 'Inquiries', to: '/dashboard', icon: '📬' },
          { label: 'Viewings', to: '/dashboard', icon: '📅' },
          { label: 'Saved', to: '/saved', icon: '❤️' },
        ].map(item => (
          <Link key={item.label} to={item.to} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, textDecoration: 'none', color: '#111' }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>{item.icon}</div>
            <div style={{ fontWeight: 600 }}>{item.label}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
