import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../hooks/useAuthStore';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '' });
  const { login, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await login(form);
    if (result.success) {
      toast.success('Welcome back!');
      navigate('/dashboard');
    } else {
      toast.error(result.error);
    }
  };

  return (
    <div style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ width: '100%', maxWidth: 400, background: '#fff', borderRadius: 20, padding: 32, boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Sign In</h1>
        <p style={{ color: '#6b7280', marginBottom: 28 }}>Welcome back to NyumbaLink</p>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <input type="email" placeholder="Email" value={form.email}
            onChange={e => setForm(p => ({...p, email: e.target.value}))}
            style={{ border: '1px solid #e5e7eb', borderRadius: 10, padding: '12px 16px', fontSize: 14 }} />
          <input type="password" placeholder="Password" value={form.password}
            onChange={e => setForm(p => ({...p, password: e.target.value}))}
            style={{ border: '1px solid #e5e7eb', borderRadius: 10, padding: '12px 16px', fontSize: 14 }} />
          <button type="submit" disabled={isLoading}
            style={{ background: '#16a34a', color: '#fff', border: 'none', borderRadius: 12, padding: 14, fontSize: 16, fontWeight: 700, cursor: 'pointer' }}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p style={{ textAlign: 'center', marginTop: 20, color: '#6b7280' }}>
          No account? <Link to="/register" style={{ color: '#16a34a', fontWeight: 600 }}>Register</Link>
        </p>
      </div>
    </div>
  );
}
