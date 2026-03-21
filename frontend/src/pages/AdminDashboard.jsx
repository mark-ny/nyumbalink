import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminAPI } from '../services/api';
import toast from 'react-hot-toast';

const TABS = ['Overview', 'Properties', 'Users', 'Inquiries', 'Leads'];

function StatCard({ icon, label, value, color }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, textAlign: 'center' }}>
      <div style={{ fontSize: 28, marginBottom: 6 }}>{icon}</div>
      <div style={{ fontSize: 26, fontWeight: 800, color: color || '#16a34a' }}>{value ?? '...'}</div>
      <div style={{ color: '#6b7280', fontSize: 13, marginTop: 2 }}>{label}</div>
    </div>
  );
}

function OverviewTab() {
  const { data } = useQuery({ queryKey: ['admin-stats'], queryFn: () => adminAPI.dashboard() });
  const s = data?.data || {};
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
      <StatCard icon="👥" label="Total Users" value={s.users?.total} />
      <StatCard icon="🏠" label="Total Properties" value={s.properties?.total} />
      <StatCard icon="⏳" label="Pending Review" value={s.properties?.pending} color="#f59e0b" />
      <StatCard icon="✅" label="Verified" value={s.properties?.verified} color="#16a34a" />
      <StatCard icon="📬" label="Inquiries" value={s.inquiries?.total} color="#3b82f6" />
      <StatCard icon="🔴" label="Unread" value={s.inquiries?.unread} color="#ef4444" />
      <StatCard icon="📊" label="Total Leads" value={s.leads?.total} color="#8b5cf6" />
      <StatCard icon="💳" label="Payments" value={s.payments?.total} color="#f59e0b" />
    </div>
  );
}

function PropertiesTab() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState('pending');

  const { data, isLoading } = useQuery({
    queryKey: ['admin-properties', filter],
    queryFn: () => adminAPI.properties({ verification_status: filter, per_page: 50 }),
  });

  const verify = useMutation({
    mutationFn: ({ id, status }) => adminAPI.verifyProperty(id, { verification_status: status }),
    onSuccess: (_, { status }) => {
      toast.success(`Property ${status}!`);
      queryClient.invalidateQueries(['admin-properties']);
    },
    onError: () => toast.error('Failed to update property'),
  });

  const feature = useMutation({
    mutationFn: (id) => adminAPI.featureProperty(id),
    onSuccess: () => {
      toast.success('Featured status updated!');
      queryClient.invalidateQueries(['admin-properties']);
    },
  });

  const properties = data?.data?.properties || [];

  return (
    <div>
      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, overflowX: 'auto', paddingBottom: 4 }}>
        {['pending', 'verified', 'rejected'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            style={{
              padding: '6px 16px', borderRadius: 20, border: 'none', cursor: 'pointer',
              background: filter === s ? '#16a34a' : '#f3f4f6',
              color: filter === s ? '#fff' : '#374151',
              fontWeight: 600, fontSize: 13, whiteSpace: 'nowrap',
            }}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {isLoading && <p style={{ color: '#6b7280', textAlign: 'center', padding: 40 }}>Loading...</p>}

      {!isLoading && properties.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: '#6b7280' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🎉</div>
          <p>No {filter} properties</p>
        </div>
      )}

      {properties.map(p => (
        <div key={p.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, padding: 16, marginBottom: 12 }}>
          {/* Image */}
          {p.primary_image && (
            <img src={p.primary_image.image_url} alt={p.title}
              style={{ width: '100%', height: 160, objectFit: 'cover', borderRadius: 10, marginBottom: 12 }} />
          )}

          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{p.title}</div>
          <div style={{ color: '#6b7280', fontSize: 13, marginBottom: 4 }}>📍 {p.location}</div>
          <div style={{ color: '#16a34a', fontWeight: 700, fontSize: 14, marginBottom: 4 }}>
            KES {Number(p.price).toLocaleString()}
          </div>
          <div style={{ color: '#6b7280', fontSize: 12, marginBottom: 12 }}>
            Owner: {p.owner?.name} · {p.category} · {p.verification_status}
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {p.verification_status !== 'verified' && (
              <button
                onClick={() => verify.mutate({ id: p.id, status: 'verified' })}
                disabled={verify.isLoading}
                style={{ flex: 1, background: '#16a34a', color: '#fff', border: 'none', borderRadius: 10, padding: '10px 8px', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
                ✅ Approve
              </button>
            )}
            {p.verification_status !== 'rejected' && (
              <button
                onClick={() => verify.mutate({ id: p.id, status: 'rejected' })}
                disabled={verify.isLoading}
                style={{ flex: 1, background: '#ef4444', color: '#fff', border: 'none', borderRadius: 10, padding: '10px 8px', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
                ❌ Reject
              </button>
            )}
            <button
              onClick={() => feature.mutate(p.id)}
              style={{ flex: 1, background: p.featured ? '#f59e0b' : '#f3f4f6', color: p.featured ? '#fff' : '#374151', border: 'none', borderRadius: 10, padding: '10px 8px', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
              {p.featured ? '⭐ Unfeature' : '☆ Feature'}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function UsersTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminAPI.users({ per_page: 50 }),
  });
  const queryClient = useQueryClient();

  const toggle = useMutation({
    mutationFn: (id) => adminAPI.toggleUserActive(id),
    onSuccess: () => { toast.success('User updated!'); queryClient.invalidateQueries(['admin-users']); },
  });

  const users = data?.data?.users || [];

  return (
    <div>
      {isLoading && <p style={{ color: '#6b7280', textAlign: 'center', padding: 40 }}>Loading...</p>}
      {users.map(u => (
        <div key={u.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, padding: 16, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 44, height: 44, borderRadius: '50%', background: '#f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 700, color: '#16a34a', flexShrink: 0 }}>
            {u.name?.[0]?.toUpperCase()}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: 14 }}>{u.name}</div>
            <div style={{ color: '#6b7280', fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{u.email}</div>
            <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
              <span style={{ background: '#f3f4f6', borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>{u.role}</span>
              <span style={{ background: u.is_active ? '#dcfce7' : '#fee2e2', color: u.is_active ? '#16a34a' : '#ef4444', borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>
                {u.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
          <button
            onClick={() => toggle.mutate(u.id)}
            style={{ background: u.is_active ? '#fee2e2' : '#dcfce7', color: u.is_active ? '#ef4444' : '#16a34a', border: 'none', borderRadius: 10, padding: '8px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer', flexShrink: 0 }}>
            {u.is_active ? 'Disable' : 'Enable'}
          </button>
        </div>
      ))}
    </div>
  );
}

function InquiriesTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-inquiries'],
    queryFn: () => adminAPI.leads({ per_page: 50 }),
  });
  const leads = data?.data?.leads || [];

  return (
    <div>
      {isLoading && <p style={{ color: '#6b7280', textAlign: 'center', padding: 40 }}>Loading...</p>}
      {leads.length === 0 && !isLoading && (
        <div style={{ textAlign: 'center', padding: 40, color: '#6b7280' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📬</div>
          <p>No inquiries yet</p>
        </div>
      )}
      {leads.map(lead => (
        <div key={lead.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, padding: 16, marginBottom: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <div style={{ fontWeight: 700, fontSize: 14 }}>{lead.name}</div>
            <span style={{
              background: lead.status === 'new' ? '#dbeafe' : '#f3f4f6',
              color: lead.status === 'new' ? '#3b82f6' : '#6b7280',
              borderRadius: 6, padding: '2px 10px', fontSize: 12, fontWeight: 600,
            }}>{lead.status}</span>
          </div>
          {lead.phone && <div style={{ color: '#6b7280', fontSize: 13, marginBottom: 4 }}>📞 {lead.phone}</div>}
          {lead.email && <div style={{ color: '#6b7280', fontSize: 13, marginBottom: 4 }}>✉️ {lead.email}</div>}
          {lead.message && <div style={{ color: '#374151', fontSize: 13, marginBottom: 4 }}>💬 {lead.message}</div>}
          <div style={{ color: '#9ca3af', fontSize: 11, marginTop: 8 }}>
            Source: {lead.source} · {new Date(lead.created_at).toLocaleDateString()}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('Overview');

  return (
    <div style={{ maxWidth: 680, margin: '0 auto', padding: '24px 16px 60px' }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4 }}>⚙️ Admin Dashboard</h1>
      <p style={{ color: '#6b7280', marginBottom: 24, fontSize: 14 }}>Manage NyumbaLink platform</p>

      {/* Tab navigation */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 24, overflowX: 'auto', paddingBottom: 4 }}>
        {TABS.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            style={{
              padding: '8px 16px', borderRadius: 20, border: 'none', cursor: 'pointer',
              background: activeTab === tab ? '#16a34a' : '#f3f4f6',
              color: activeTab === tab ? '#fff' : '#374151',
              fontWeight: 600, fontSize: 13, whiteSpace: 'nowrap',
            }}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Overview'    && <OverviewTab />}
      {activeTab === 'Properties'  && <PropertiesTab />}
      {activeTab === 'Users'       && <UsersTab />}
      {activeTab === 'Inquiries'   && <InquiriesTab />}
      {activeTab === 'Leads'       && <InquiriesTab />}
    </div>
  );
}
