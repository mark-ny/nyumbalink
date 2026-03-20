import React from 'react';
import useAuthStore from '../hooks/useAuthStore';

export default function ProfilePage() {
  const { user } = useAuthStore();
  return (
    <div style={{ maxWidth: 600, margin: '40px auto', padding: '0 20px' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 24 }}>My Profile</h1>
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
        <p><strong>Name:</strong> {user?.name}</p>
        <p style={{ marginTop: 12 }}><strong>Email:</strong> {user?.email}</p>
        <p style={{ marginTop: 12 }}><strong>Role:</strong> {user?.role}</p>
      </div>
    </div>
  );
}
