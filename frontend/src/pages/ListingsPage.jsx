import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { propertiesAPI } from '../services/api';
import PropertyCard from '../components/property/PropertyCard';
import SearchBar from '../components/common/SearchBar';
import { SlidersHorizontal, ChevronLeft, ChevronRight, X, Grid3X3, List } from 'lucide-react';
import clsx from 'clsx';

const CATEGORIES = [
  { value: '', label: 'All' },
  { value: 'rent', label: 'For Rent' },
  { value: 'short_stay', label: 'Short Stay' },
  { value: 'plot_sale', label: 'Land & Plots' },
];

const COUNTIES = [
  'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret',
  'Thika', 'Malindi', 'Kitale', 'Garissa', 'Kakamega',
  'Nyeri', 'Meru', 'Kilifi', 'Kisii', 'Machakos',
];

function FilterPanel({ filters, onChange, onReset, isMobile, onClose }) {
  return (
    <div className={clsx(
      'bg-white rounded-2xl p-5 space-y-5',
      isMobile ? 'fixed inset-y-0 right-0 w-80 z-50 shadow-floating overflow-y-auto' : 'sticky top-24 shadow-card'
    )}>
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-dark-900">Filters</h3>
        <div className="flex gap-2">
          <button onClick={onReset} className="text-xs text-gray-400 hover:text-red-500">Reset all</button>
          {isMobile && (
            <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100"><X size={16} /></button>
          )}
        </div>
      </div>

      {/* Category */}
      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">Category</label>
        <div className="space-y-1">
          {CATEGORIES.map(cat => (
            <label key={cat.value} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="category"
                value={cat.value}
                checked={filters.category === cat.value}
                onChange={() => onChange('category', cat.value)}
                className="text-primary-600"
              />
              <span className="text-sm text-gray-700">{cat.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Location */}
      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">County</label>
        <select
          value={filters.county || ''}
          onChange={e => onChange('county', e.target.value)}
          className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-primary-400"
        >
          <option value="">All Counties</option>
          {COUNTIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Price range */}
      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">Price Range (KES)</label>
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="Min"
            value={filters.min_price || ''}
            onChange={e => onChange('min_price', e.target.value)}
            className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-primary-400"
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.max_price || ''}
            onChange={e => onChange('max_price', e.target.value)}
            className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-primary-400"
          />
        </div>
      </div>

      {/* Bedrooms */}
      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">Bedrooms (min)</label>
        <div className="flex gap-2">
          {[0, 1, 2, 3, 4].map(n => (
            <button
              key={n}
              onClick={() => onChange('bedrooms', filters.bedrooms === String(n) ? '' : String(n))}
              className={clsx(
                'flex-1 py-1.5 rounded-lg text-sm font-medium border transition-colors',
                filters.bedrooms === String(n)
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'border-gray-200 text-gray-700 hover:border-primary-400'
              )}
            >
              {n === 0 ? 'Any' : n === 4 ? '4+' : n}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-card animate-pulse">
      <div className="aspect-[4/3] bg-gray-200" />
      <div className="p-4 space-y-3">
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="h-3 bg-gray-200 rounded w-1/2" />
        <div className="h-4 bg-gray-200 rounded w-1/3" />
      </div>
    </div>
  );
}

export default function ListingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(false);
  const [gridView, setGridView] = useState(true);

  const [filters, setFilters] = useState({
    q: searchParams.get('q') || '',
    category: searchParams.get('category') || '',
    county: searchParams.get('county') || '',
    min_price: searchParams.get('min_price') || '',
    max_price: searchParams.get('max_price') || '',
    bedrooms: searchParams.get('bedrooms') || '',
    page: parseInt(searchParams.get('page') || '1'),
  });

  useEffect(() => {
    const params = {};
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
    setSearchParams(params);
  }, [filters]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  };

  const handleReset = () => {
    setFilters({ q: '', category: '', county: '', min_price: '', max_price: '', bedrooms: '', page: 1 });
  };

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['listings', filters],
    queryFn: () => propertiesAPI.list(filters),
    keepPreviousData: true,
  });

  const properties = data?.data?.properties || [];
  const pagination = data?.data?.pagination || {};
  const activeFilters = Object.entries(filters).filter(([k, v]) => v && k !== 'page' && k !== 'q').length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header bar */}
      <div className="bg-white border-b border-gray-100 sticky top-16 lg:top-20 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center gap-3">
            <SearchBar className="flex-1" />
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={clsx(
                'flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-colors',
                showFilters || activeFilters > 0
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-primary-400'
              )}
            >
              <SlidersHorizontal size={16} />
              Filters {activeFilters > 0 && `(${activeFilters})`}
            </button>
            <div className="hidden sm:flex border border-gray-200 rounded-xl overflow-hidden">
              <button onClick={() => setGridView(true)}
                className={clsx('p-2.5', gridView ? 'bg-primary-600 text-white' : 'bg-white text-gray-500')}>
                <Grid3X3 size={16} />
              </button>
              <button onClick={() => setGridView(false)}
                className={clsx('p-2.5', !gridView ? 'bg-primary-600 text-white' : 'bg-white text-gray-500')}>
                <List size={16} />
              </button>
            </div>
          </div>

          {/* Active filters */}
          {activeFilters > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {filters.category && (
                <span className="flex items-center gap-1 bg-primary-50 text-primary-700 px-3 py-1 rounded-full text-xs font-medium">
                  {filters.category.replace('_', ' ')}
                  <button onClick={() => handleFilterChange('category', '')}><X size={12} /></button>
                </span>
              )}
              {filters.county && (
                <span className="flex items-center gap-1 bg-primary-50 text-primary-700 px-3 py-1 rounded-full text-xs font-medium">
                  {filters.county}
                  <button onClick={() => handleFilterChange('county', '')}><X size={12} /></button>
                </span>
              )}
              {(filters.min_price || filters.max_price) && (
                <span className="flex items-center gap-1 bg-primary-50 text-primary-700 px-3 py-1 rounded-full text-xs font-medium">
                  KES {filters.min_price || '0'} – {filters.max_price || '∞'}
                  <button onClick={() => { handleFilterChange('min_price', ''); handleFilterChange('max_price', ''); }}>
                    <X size={12} />
                  </button>
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6">
          {/* Desktop sidebar */}
          <div className="hidden lg:block w-64 flex-shrink-0">
            <FilterPanel filters={filters} onChange={handleFilterChange} onReset={handleReset} />
          </div>

          {/* Results */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-gray-500">
                {isLoading ? 'Loading...' : `${pagination.total || 0} properties found`}
                {isFetching && !isLoading && ' · Updating...'}
              </p>
            </div>

            {isLoading ? (
              <div className={clsx(
                'grid gap-5',
                gridView ? 'grid-cols-1 sm:grid-cols-2 xl:grid-cols-3' : 'grid-cols-1'
              )}>
                {Array(9).fill(0).map((_, i) => <SkeletonCard key={i} />)}
              </div>
            ) : properties.length === 0 ? (
              <div className="text-center py-20 bg-white rounded-2xl shadow-card">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <SlidersHorizontal size={24} className="text-gray-400" />
                </div>
                <h3 className="font-semibold text-gray-700 mb-2">No properties found</h3>
                <p className="text-gray-500 text-sm mb-4">Try adjusting your filters</p>
                <button onClick={handleReset}
                  className="bg-primary-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium hover:bg-primary-700">
                  Clear Filters
                </button>
              </div>
            ) : (
              <div className={clsx(
                'grid gap-5',
                gridView ? 'grid-cols-1 sm:grid-cols-2 xl:grid-cols-3' : 'grid-cols-1'
              )}>
                {properties.map(p => <PropertyCard key={p.id} property={p} />)}
              </div>
            )}

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-10">
                <button
                  onClick={() => handleFilterChange('page', Math.max(1, filters.page - 1))}
                  disabled={filters.page <= 1}
                  className="w-10 h-10 flex items-center justify-center rounded-xl border border-gray-200 disabled:opacity-40 hover:border-primary-400 transition-colors"
                >
                  <ChevronLeft size={16} />
                </button>

                {Array.from({ length: Math.min(pagination.pages, 7) }, (_, i) => {
                  const p = i + 1;
                  return (
                    <button
                      key={p}
                      onClick={() => handleFilterChange('page', p)}
                      className={clsx(
                        'w-10 h-10 rounded-xl text-sm font-medium transition-colors',
                        filters.page === p
                          ? 'bg-primary-600 text-white'
                          : 'border border-gray-200 text-gray-700 hover:border-primary-400'
                      )}
                    >
                      {p}
                    </button>
                  );
                })}

                <button
                  onClick={() => handleFilterChange('page', Math.min(pagination.pages, filters.page + 1))}
                  disabled={filters.page >= pagination.pages}
                  className="w-10 h-10 flex items-center justify-center rounded-xl border border-gray-200 disabled:opacity-40 hover:border-primary-400 transition-colors"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile filter overlay */}
      {showFilters && (
        <>
          <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={() => setShowFilters(false)} />
          <div className="lg:hidden">
            <FilterPanel
              filters={filters}
              onChange={handleFilterChange}
              onReset={handleReset}
              isMobile
              onClose={() => setShowFilters(false)}
            />
          </div>
        </>
      )}
    </div>
  );
}
