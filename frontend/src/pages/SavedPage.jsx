import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { propertiesAPI } from '../services/api';
import PropertyCard from '../components/property/PropertyCard';

export default function SavedPage() {
  const { data } = useQuery({ queryKey: ['saved'], queryFn: () => propertiesAPI.saved() });
  const properties = data?.data?.properties || [];
  return (
    <div style={{ maxWidth: 900, margin: '40px auto', padding: '0 20px' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32 }}>Saved Properties</h1>
      {properties.length === 0
        ? <p style={{ color: '#6b7280' }}>No saved properties yet.</p>
        : <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 20 }}>
            {properties.map(p => <PropertyCard key={p.id} property={p} />)}
          </div>
      }
    </div>
  );
}
