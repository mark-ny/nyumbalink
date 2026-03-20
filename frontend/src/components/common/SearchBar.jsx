import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, Home, ChevronDown } from 'lucide-react';
import clsx from 'clsx';

const CATEGORIES = [
  { value: '', label: 'All Types' },
  { value: 'rent', label: 'For Rent' },
  { value: 'short_stay', label: 'Short Stay' },
  { value: 'plot_sale', label: 'Land & Plots' },
];

const KENYAN_COUNTIES = [
  'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika',
  'Malindi', 'Kitale', 'Garissa', 'Kakamega', 'Nyeri', 'Meru',
  'Kilifi', 'Kisii', 'Machakos', 'Embu', 'Lamu', 'Isiolo',
];

export default function SearchBar({ className, variant = 'default' }) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [location, setLocation] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    if (category) params.set('category', category);
    if (location) params.set('county', location);
    navigate(`/listings?${params.toString()}`);
  };

  if (variant === 'hero') {
    return (
      <form onSubmit={handleSearch}
        className={clsx('bg-white rounded-2xl shadow-floating p-2', className)}>
        <div className="flex flex-col md:flex-row gap-2">
          {/* Location */}
          <div className="flex items-center gap-2 flex-1 px-4 py-3 bg-gray-50 rounded-xl">
            <MapPin size={18} className="text-primary-500 flex-shrink-0" />
            <select
              value={location}
              onChange={e => setLocation(e.target.value)}
              className="bg-transparent text-sm text-gray-700 flex-1 outline-none"
            >
              <option value="">Any Location</option>
              {KENYAN_COUNTIES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Category */}
          <div className="flex items-center gap-2 flex-1 px-4 py-3 bg-gray-50 rounded-xl">
            <Home size={18} className="text-primary-500 flex-shrink-0" />
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="bg-transparent text-sm text-gray-700 flex-1 outline-none"
            >
              {CATEGORIES.map(c => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          {/* Keyword */}
          <div className="flex items-center gap-2 flex-1 px-4 py-3 bg-gray-50 rounded-xl">
            <Search size={18} className="text-gray-400 flex-shrink-0" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Keywords, area, estate..."
              className="bg-transparent text-sm text-gray-700 flex-1 outline-none placeholder-gray-400"
            />
          </div>

          <button
            type="submit"
            className="bg-primary-600 hover:bg-primary-700 text-white px-8 py-3 rounded-xl font-semibold text-sm transition-colors flex items-center gap-2 justify-center flex-shrink-0"
          >
            <Search size={16} />
            Search
          </button>
        </div>
      </form>
    );
  }

  // Compact variant for listings page
  return (
    <form onSubmit={handleSearch} className={clsx('flex gap-2', className)}>
      <div className="flex items-center gap-2 flex-1 px-4 py-2.5 bg-white border border-gray-200 rounded-xl">
        <Search size={16} className="text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search properties..."
          className="flex-1 text-sm outline-none text-gray-700"
        />
      </div>
      <button
        type="submit"
        className="bg-primary-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-primary-700 transition-colors"
      >
        Search
      </button>
    </form>
  );
}
