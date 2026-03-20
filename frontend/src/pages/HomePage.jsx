import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { propertiesAPI } from '../services/api';
import SearchBar from '../components/common/SearchBar';
import PropertyCard from '../components/property/PropertyCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import {
  Home, Building2, TreePine, Star, ArrowRight,
  Shield, Clock, Phone, TrendingUp, Users, MapPin
} from 'lucide-react';

const CATEGORIES = [
  {
    id: 'rent',
    label: 'For Rent',
    icon: Home,
    description: 'Apartments, bedsitters & houses',
    color: 'bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white',
    border: 'border-blue-100 group-hover:border-blue-600',
  },
  {
    id: 'short_stay',
    label: 'Short Stay',
    icon: Star,
    description: 'Holiday homes & Airbnb-style',
    color: 'bg-amber-50 text-amber-600 group-hover:bg-amber-500 group-hover:text-white',
    border: 'border-amber-100 group-hover:border-amber-500',
  },
  {
    id: 'plot_sale',
    label: 'Land & Plots',
    icon: TreePine,
    description: 'Residential, commercial & farm land',
    color: 'bg-green-50 text-green-600 group-hover:bg-green-600 group-hover:text-white',
    border: 'border-green-100 group-hover:border-green-600',
  },
];

const STATS = [
  { icon: Building2, value: '10,000+', label: 'Active Listings' },
  { icon: Users, value: '50,000+', label: 'Happy Users' },
  { icon: MapPin, value: '47', label: 'Counties Covered' },
  { icon: Shield, value: '100%', label: 'Verified Listings' },
];

const WHY_US = [
  {
    icon: Shield,
    title: 'Verified Properties',
    desc: 'Every listing reviewed & approved by our team before going live.',
  },
  {
    icon: Clock,
    title: 'Fast Responses',
    desc: 'Connect with property owners and agents within minutes.',
  },
  {
    icon: Phone,
    title: 'M-Pesa Payments',
    desc: 'Secure listing fees and deposits through M-Pesa STK Push.',
  },
  {
    icon: TrendingUp,
    title: 'Best Deals',
    desc: 'Thousands of listings updated daily across all price ranges.',
  },
];

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-card">
      <div className="aspect-[4/3] bg-gray-200 animate-pulse" />
      <div className="p-4 space-y-3">
        <div className="h-4 bg-gray-200 rounded animate-pulse" />
        <div className="h-3 bg-gray-200 rounded w-2/3 animate-pulse" />
        <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse" />
      </div>
    </div>
  );
}

export default function HomePage() {
  const { data: featuredData, isLoading: featuredLoading } = useQuery({
    queryKey: ['featured-properties'],
    queryFn: () => propertiesAPI.list({ featured: true, per_page: 6 }),
  });

  const { data: recentData, isLoading: recentLoading } = useQuery({
    queryKey: ['recent-properties'],
    queryFn: () => propertiesAPI.list({ per_page: 8 }),
  });

  const featured = featuredData?.data?.properties || [];
  const recent = recentData?.data?.properties || [];

  return (
    <div className="min-h-screen">
      {/* ── HERO ───────────────────────────────────────────── */}
      <section className="relative min-h-[620px] flex items-center bg-gradient-to-br from-dark-900 via-dark-800 to-dark-700 overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 w-full">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 bg-primary-500/20 text-primary-300 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <span className="w-2 h-2 bg-primary-400 rounded-full animate-pulse" />
              Kenya's #1 Property Marketplace
            </div>

            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
              Find Your Perfect{' '}
              <span className="text-primary-400">Home</span>{' '}
              in Kenya
            </h1>

            <p className="text-lg text-gray-300 mb-10 max-w-xl leading-relaxed">
              Browse thousands of verified properties for rent, short stay and sale
              across all 47 counties. Connect directly with owners and agents.
            </p>

            <SearchBar variant="hero" className="max-w-3xl" />

            <div className="flex flex-wrap gap-6 mt-8">
              {STATS.map(({ icon: Icon, value, label }) => (
                <div key={label} className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                    <Icon size={18} className="text-primary-400" />
                  </div>
                  <div>
                    <p className="text-white font-bold text-lg leading-none">{value}</p>
                    <p className="text-gray-400 text-xs">{label}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── CATEGORIES ─────────────────────────────────────── */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="font-display text-3xl font-bold text-dark-900 mb-3">
              What are you looking for?
            </h2>
            <p className="text-gray-500">Find properties that match your needs</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {CATEGORIES.map(cat => (
              <Link
                key={cat.id}
                to={`/listings?category=${cat.id}`}
                className={`group p-6 rounded-2xl border-2 transition-all duration-300 cursor-pointer ${cat.border} bg-white hover:shadow-card-hover`}
              >
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-all duration-300 ${cat.color}`}>
                  <cat.icon size={26} />
                </div>
                <h3 className="font-semibold text-dark-900 text-lg mb-1">{cat.label}</h3>
                <p className="text-gray-500 text-sm">{cat.description}</p>
                <div className="flex items-center gap-1 mt-4 text-primary-600 text-sm font-medium group-hover:gap-2 transition-all">
                  Browse listings <ArrowRight size={14} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURED PROPERTIES ────────────────────────────── */}
      {(featured.length > 0 || featuredLoading) && (
        <section className="py-16 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-end justify-between mb-8">
              <div>
                <h2 className="font-display text-3xl font-bold text-dark-900 mb-2">
                  Featured Properties
                </h2>
                <p className="text-gray-500">Handpicked premium listings</p>
              </div>
              <Link to="/listings?featured=true"
                className="hidden sm:flex items-center gap-1 text-primary-600 font-medium text-sm hover:gap-2 transition-all">
                View all <ArrowRight size={15} />
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredLoading
                ? Array(6).fill(0).map((_, i) => <SkeletonCard key={i} />)
                : featured.map(p => <PropertyCard key={p.id} property={p} />)
              }
            </div>
          </div>
        </section>
      )}

      {/* ── RECENT LISTINGS ────────────────────────────────── */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-end justify-between mb-8">
            <div>
              <h2 className="font-display text-3xl font-bold text-dark-900 mb-2">
                Latest Listings
              </h2>
              <p className="text-gray-500">Fresh properties added recently</p>
            </div>
            <Link to="/listings"
              className="hidden sm:flex items-center gap-1 text-primary-600 font-medium text-sm hover:gap-2 transition-all">
              View all <ArrowRight size={15} />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {recentLoading
              ? Array(8).fill(0).map((_, i) => <SkeletonCard key={i} />)
              : recent.map(p => <PropertyCard key={p.id} property={p} />)
            }
          </div>

          <div className="text-center mt-10">
            <Link
              to="/listings"
              className="inline-flex items-center gap-2 bg-dark-900 text-white px-8 py-3.5 rounded-xl font-semibold hover:bg-dark-800 transition-colors"
            >
              Browse All Properties <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── WHY NYUMBALINK ─────────────────────────────────── */}
      <section className="py-16 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl font-bold text-white mb-3">
              Why Choose NyumbaLink?
            </h2>
            <p className="text-primary-100">Built for Kenya, trusted by Kenyans</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {WHY_US.map(item => (
              <div key={item.title} className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 text-center">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <item.icon size={22} className="text-white" />
                </div>
                <h3 className="font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-primary-100 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link
              to="/register"
              className="inline-flex items-center gap-2 bg-white text-primary-700 px-8 py-3.5 rounded-xl font-semibold hover:bg-primary-50 transition-colors"
            >
              Start Listing for Free <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
