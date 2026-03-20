import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { propertiesAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function CreateListingPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: '', category: 'rent', price: '', location: '', description: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await propertiesAPI.create(form);
      toast.success('Property created!');
      navigate(`/properties/${res.data.property.id}`);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create property');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '40px auto', padding: '0 20px' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32 }}>Create Listing</h1>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {[['title','Title'],['location','Location'],['price','Price (KES)'],['description','Description']].map(([key, label]) => (
          <div key={key}>
            <label style={{ display: 'block', fontWeight: 600, marginBottom: 6 }}>{label}</label>
            <input value={form[key]} onChange={e => setForm(p => ({...p, [key]: e.target.value}))}
              style={{ width: '100%', border: '1px solid #e5e7eb', borderRadius: 10, padding: '10px 14px', fontSize: 14 }} />
          </div>
        ))}
        <div>
          <label style={{ display: 'block', fontWeight: 600, marginBottom: 6 }}>Category</label>
          <select value={form.category} onChange={e => setForm(p => ({...p, category: e.target.value}))}
            style={{ width: '100%', border: '1px solid #e5e7eb', borderRadius: 10, padding: '10px 14px', fontSize: 14 }}>
            <option value="rent">For Rent</option>
            <option value="short_stay">Short Stay</option>
            <option value="plot_sale">Plot Sale</option>
          </select>
        </div>
        <button type="submit" disabled={loading}
          style={{ background: '#16a34a', color: '#fff', border: 'none', borderRadius: 12, padding: '14px', fontSize: 16, fontWeight: 700, cursor: 'pointer' }}>
          {loading ? 'Creating...' : 'Create Listing'}
        </button>
      </form>
    </div>
  );
}
