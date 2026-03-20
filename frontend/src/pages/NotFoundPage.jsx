import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div style={{ textAlign: 'center', padding: '80px 20px' }}>
      <h1 style={{ fontSize: 72, fontWeight: 800, color: '#16a34a' }}>404</h1>
      <h2 style={{ fontSize: 24, marginBottom: 16 }}>Page Not Found</h2>
      <p style={{ color: '#6b7280', marginBottom: 32 }}>The page you are looking for does not exist.</p>
      <Link to="/" style={{ background: '#16a34a', color: '#fff', padding: '12px 32px', borderRadius: 12, textDecoration: 'none', fontWeight: 600 }}>
        Go Home
      </Link>
    </div>
  );
}
