import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../hooks/useAuthStore';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const [step, setStep] = useState('register'); // register | verify
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'seeker' });
  const [code, setCode] = useState('');
  const [sending, setSending] = useState(false);
  const { register, isLoading, accessToken } = useAuthStore();
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    if (form.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    const result = await register(form);
    if (result.success) {
      // Send verification code
      try {
        setSending(true);
        const res = await api.post('/verification/send');
        const data = res.data;
        if (data.dev_code) {
          toast.success(`Dev mode - your code is: ${data.dev_code}`, { duration: 30000 });
        } else {
          toast.success(`Verification code sent to ${form.email}`);
        }
        setStep('verify');
      } catch (err) {
        toast.error('Could not send verification email');
        setStep('verify');
      } finally {
        setSending(false);
      }
    } else {
      toast.error(result.error);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    try {
      await api.post('/verification/verify', { code });
      toast.success('Email verified! Welcome to NyumbaLink 🎉');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Invalid code');
    }
  };

  const resendCode = async () => {
    try {
      setSending(true);
      const res = await api.post('/verification/send');
      if (res.data.dev_code) {
        toast.success(`New code: ${res.data.dev_code}`, { duration: 30000 });
      } else {
        toast.success('New code sent!');
      }
    } catch {
      toast.error('Failed to resend code');
    } finally {
      setSending(false);
    }
  };

  const cardStyle = {
    width: '100%', maxWidth: 400, background: '#fff',
    borderRadius: 20, padding: 32,
    boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
  };
  const inputStyle = {
    width: '100%', border: '1px solid #e5e7eb',
    borderRadius: 10, padding: '12px 16px', fontSize: 14,
    outline: 'none', fontFamily: 'inherit',
  };
  const btnStyle = {
    width: '100%', background: '#16a34a', color: '#fff',
    border: 'none', borderRadius: 12, padding: 14,
    fontSize: 16, fontWeight: 700, cursor: 'pointer',
  };

  // ── Verification screen ─────────────────────────────────
  if (step === 'verify') {
    return (
      <div style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
        <div style={cardStyle}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>📧</div>
            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Verify Your Email</h1>
            <p style={{ color: '#6b7280', fontSize: 14 }}>
              We sent a 6-digit code to<br />
              <strong>{form.email}</strong>
            </p>
          </div>

          <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <input
              type="text"
              value={code}
              onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="Enter 6-digit code"
              maxLength={6}
              style={{
                ...inputStyle,
                textAlign: 'center',
                fontSize: 28,
                fontWeight: 800,
                letterSpacing: 8,
              }}
            />
            <button type="submit" style={btnStyle}>
              ✅ Verify Email
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <button
              onClick={resendCode}
              disabled={sending}
              style={{ background: 'none', border: 'none', color: '#16a34a', fontWeight: 600, cursor: 'pointer', fontSize: 14 }}
            >
              {sending ? 'Sending...' : "Didn't receive code? Resend"}
            </button>
          </div>

          <div style={{ textAlign: 'center', marginTop: 12 }}>
            <button
              onClick={() => navigate('/dashboard')}
              style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: 13 }}
            >
              Skip for now →
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Register screen ──────────────────────────────────────
  return (
    <div style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={cardStyle}>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Create Account</h1>
        <p style={{ color: '#6b7280', marginBottom: 28 }}>Join NyumbaLink today</p>

        <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <input
            type="text" placeholder="Full Name" required value={form.name}
            onChange={e => setForm(p => ({...p, name: e.target.value}))}
            style={inputStyle}
          />
          <input
            type="email" placeholder="Email Address" required value={form.email}
            onChange={e => setForm(p => ({...p, email: e.target.value}))}
            style={inputStyle}
          />
          <input
            type="password" placeholder="Password (min 8 chars)" required value={form.password}
            onChange={e => setForm(p => ({...p, password: e.target.value}))}
            style={inputStyle}
          />
          <select value={form.role} onChange={e => setForm(p => ({...p, role: e.target.value}))} style={inputStyle}>
            <option value="seeker">🔍 I want to find property</option>
            <option value="owner">🏠 I want to list property</option>
          </select>

          <button type="submit" disabled={isLoading || sending} style={{ ...btnStyle, opacity: isLoading ? 0.7 : 1 }}>
            {isLoading || sending ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, color: '#6b7280' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: '#16a34a', fontWeight: 600 }}>Sign In</Link>
        </p>
      </div>
    </div>
  );
}
