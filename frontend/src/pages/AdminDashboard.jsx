import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminAPI } from '../services/api';

export default function AdminDashboard() {
  const { data } = useQuery({ queryKey: ['admin-stats'], queryFn: () => adminAPI.dashboard() });
  const stats = data?.data || {};
  return (
    <div style={{ maxWidth: 900, margin: '40px auto', padding: '0 20px' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32 }}>Admin Dashboard</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
        {[
          ['Total Users', stats.users?.total, '👥'],
          ['Total Properties', stats.properties?.total, '🏠'],
          ['Pending Review', stats.properties?.pending, '⏳'],
          ['Total Leads', stats.leads?.total, '📊'],
        ].map(([label, val, icon]) => (
          <div key={label} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, textAlign: 'center' }}>
            <div style={{ fontSize: 32 }}>{icon}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#16a34a', margin: '8px 0' }}>{val ?? '...'}</div>
            <div style={{ color: '#6b7280', fontSize: 14 }}>{label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
