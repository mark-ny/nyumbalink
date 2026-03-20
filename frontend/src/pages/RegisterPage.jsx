import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../hooks/useAuthStore';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'seeker' });
  const { register, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await register(form);
    if (result.success) {
      toast.success('Account created!');
      navigate('/dashboard');
    } else {
      toast.error(result.error);
    }
  };

  return (
    <div style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ width: '100%', maxWidth: 400, background: '#fff', borderRadius: 20, padding: 32, boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Create Account</h1>
        <p style={{ color: '#6b7280', marginBottom: 28 }}>Join NyumbaLink today</p>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[['text','Name','name'],['email','Email','email'],['password','Password','password']].map(([type, placeholder, key]) => (
            <input key={key} type={type} placeholder={placeholder} value={form[key]}
              onChange={e => setForm(p => ({...p, [key]: e.target.value}))}
              style={{ border: '1px solid #e5e7eb', borderRadius: 10, padding: '12px 16px', fontSize: 14 }} />
          ))}
          <select value={form.role} onChange={e => setForm(p => ({...p, role: e.target.value}))}
            style={{ border: '1px solid #e5e7eb', borderRadius: 10, padding: '12px 16px', fontSize: 14 }}>
            <option value="seeker">I want to find property</option>
            <option value="owner">I want to list property</option>
          </select>
          <button type="submit" disabled={isLoading}
            style={{ background: '#16a34a', color: '#fff', border: 'none', borderRadius: 12, padding: 14, fontSize: 16, fontWeight: 700, cursor: 'pointer' }}>
            {isLoading ? 'Creating...' : 'Create Account'}
          </button>
        </form>
        <p style={{ textAlign: 'center', marginTop: 20, color: '#6b7280' }}>
          Have account? <Link to="/login" style={{ color: '#16a34a', fontWeight: 600 }}>Sign In</Link>
        </p>
      </div>
    </div>
  );
}
