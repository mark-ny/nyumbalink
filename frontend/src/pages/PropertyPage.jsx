import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { propertiesAPI, inquiriesAPI, viewingsAPI } from '../services/api';
import {
  MapPin, Bed, Bath, Maximize2, CheckCircle, Eye, Star,
  Phone, Mail, Calendar, ChevronLeft, ChevronRight, X,
  Heart, Share2, ArrowLeft, Clock, User
} from 'lucide-react';
import toast from 'react-hot-toast';
import clsx from 'clsx';

const CATEGORY_LABELS = { rent: 'For Rent', short_stay: 'Short Stay', plot_sale: 'For Sale' };

function formatPrice(price, period) {
  const f = new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES', maximumFractionDigits: 0 }).format(price);
  if (period === 'monthly') return `${f} / month`;
  if (period === 'per_night') return `${f} / night`;
  return f;
}

function ImageGallery({ images }) {
  const [current, setCurrent] = useState(0);
  const [lightbox, setLightbox] = useState(false);

  if (!images?.length) return (
    <div className="aspect-video bg-gray-200 rounded-2xl flex items-center justify-center">
      <span className="text-gray-400">No images</span>
    </div>
  );

  return (
    <>
      <div className="relative rounded-2xl overflow-hidden bg-gray-100">
        <div className="aspect-video">
          <img
            src={images[current]?.image_url}
            alt={`Property ${current + 1}`}
            className="w-full h-full object-cover cursor-pointer"
            onClick={() => setLightbox(true)}
          />
        </div>

        {images.length > 1 && (
          <>
            <button onClick={() => setCurrent(c => (c - 1 + images.length) % images.length)}
              className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/80 rounded-full flex items-center justify-center shadow hover:bg-white">
              <ChevronLeft size={18} />
            </button>
            <button onClick={() => setCurrent(c => (c + 1) % images.length)}
              className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/80 rounded-full flex items-center justify-center shadow hover:bg-white">
              <ChevronRight size={18} />
            </button>
            <div className="absolute bottom-3 right-3 bg-black/50 text-white text-xs px-2.5 py-1 rounded-full">
              {current + 1} / {images.length}
            </div>
          </>
        )}
      </div>

      {images.length > 1 && (
        <div className="flex gap-2 mt-3 overflow-x-auto pb-1">
          {images.map((img, i) => (
            <button key={i} onClick={() => setCurrent(i)}
              className={clsx('w-16 h-16 flex-shrink-0 rounded-xl overflow-hidden border-2 transition-all',
                i === current ? 'border-primary-500' : 'border-transparent')}>
              <img src={img.image_url} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}

      {/* Lightbox */}
      {lightbox && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center">
          <button onClick={() => setLightbox(false)}
            className="absolute top-4 right-4 text-white w-10 h-10 flex items-center justify-center rounded-full bg-white/20 hover:bg-white/30">
            <X size={20} />
          </button>
          <img src={images[current]?.image_url} alt="" className="max-w-full max-h-full object-contain px-16" />
          {images.length > 1 && (
            <>
              <button onClick={() => setCurrent(c => (c - 1 + images.length) % images.length)}
                className="absolute left-4 text-white w-12 h-12 flex items-center justify-center rounded-full bg-white/20">
                <ChevronLeft size={22} />
              </button>
              <button onClick={() => setCurrent(c => (c + 1) % images.length)}
                className="absolute right-4 text-white w-12 h-12 flex items-center justify-center rounded-full bg-white/20">
                <ChevronRight size={22} />
              </button>
            </>
          )}
        </div>
      )}
    </>
  );
}

function InquiryForm({ propertyId }) {
  const [form, setForm] = useState({ name: '', email: '', phone: '', message: '' });
  const [sending, setSending] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);
    try {
      await inquiriesAPI.create({ ...form, property_id: propertyId });
      toast.success('Inquiry sent successfully!');
      setForm({ name: '', email: '', phone: '', message: '' });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to send inquiry');
    } finally {
      setSending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <input
        required value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
        placeholder="Your Name"
        className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary-400 transition-colors"
      />
      <input
        type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
        placeholder="Email Address"
        className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary-400 transition-colors"
      />
      <input
        value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))}
        placeholder="Phone Number"
        className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary-400 transition-colors"
      />
      <textarea
        required value={form.message} onChange={e => setForm(p => ({ ...p, message: e.target.value }))}
        placeholder="I am interested in this property..."
        rows={3}
        className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary-400 transition-colors resize-none"
      />
      <button
        type="submit" disabled={sending}
        className="w-full bg-primary-600 text-white py-3 rounded-xl font-semibold text-sm hover:bg-primary-700 disabled:opacity-60 transition-colors"
      >
        {sending ? 'Sending...' : 'Send Inquiry'}
      </button>
    </form>
  );
}

function ViewingForm({ propertyId }) {
  const [form, setForm] = useState({ name: '', phone: '', email: '', preferred_date: '', preferred_time: '', message: '' });
  const [sending, setSending] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);
    try {
      await viewingsAPI.create({ ...form, property_id: propertyId });
      toast.success('Viewing request sent!');
      setForm({ name: '', phone: '', email: '', preferred_date: '', preferred_time: '', message: '' });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to book viewing');
    } finally {
      setSending(false);
    }
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <input
        required value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
        placeholder="Your Name"
        className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary-400"
      />
      <input
        value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))}
        placeholder="Phone Number"
        className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary-400"
      />
      <div className="grid grid-cols-2 gap-3">
        <input
          type="date" required min={today}
          value={form.preferred_date} onChange={e => setForm(p => ({ ...p, preferred_date: e.target.value }))}
          className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary-400"
        />
        <input
          type="time"
          value={form.preferred_time} onChange={e => setForm(p => ({ ...p, preferred_time: e.target.value }))}
          className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary-400"
        />
      </div>
      <button
        type="submit" disabled={sending}
        className="w-full bg-dark-900 text-white py-3 rounded-xl font-semibold text-sm hover:bg-dark-800 disabled:opacity-60 transition-colors"
      >
        {sending ? 'Sending...' : 'Book Viewing'}
      </button>
    </form>
  );
}

export default function PropertyPage() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('inquiry');

  const { data, isLoading, error } = useQuery({
    queryKey: ['property', id],
    queryFn: () => propertiesAPI.get(id),
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-4 py-10 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-6" />
      <div className="aspect-video bg-gray-200 rounded-2xl mb-6" />
    </div>
  );

  if (error || !data?.data) return (
    <div className="max-w-7xl mx-auto px-4 py-20 text-center">
      <p className="text-gray-500">Property not found.</p>
      <Link to="/listings" className="text-primary-600 font-medium mt-4 inline-block">← Back to listings</Link>
    </div>
  );

  const p = data.data;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
          <Link to="/listings" className="flex items-center gap-1 hover:text-primary-600 transition-colors">
            <ArrowLeft size={14} /> Listings
          </Link>
          <span>/</span>
          <span className="text-gray-700 truncate max-w-xs">{p.title}</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left — main content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Gallery */}
            <ImageGallery images={p.images} />

            {/* Title + meta */}
            <div className="bg-white rounded-2xl p-6 shadow-card">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    <span className={clsx(
                      'px-3 py-1 rounded-full text-xs font-semibold',
                      p.category === 'rent' ? 'bg-blue-100 text-blue-700' :
                      p.category === 'short_stay' ? 'bg-amber-100 text-amber-700' :
                      'bg-green-100 text-green-700'
                    )}>
                      {CATEGORY_LABELS[p.category]}
                    </span>
                    {p.verification_status === 'verified' && (
                      <span className="flex items-center gap-1 text-xs text-primary-600 font-medium">
                        <CheckCircle size={13} /> Verified
                      </span>
                    )}
                    {p.featured && (
                      <span className="flex items-center gap-1 text-xs text-amber-600 font-medium">
                        <Star size={13} fill="currentColor" /> Featured
                      </span>
                    )}
                  </div>
                  <h1 className="font-display text-2xl font-bold text-dark-900 mb-2">{p.title}</h1>
                  <div className="flex items-center gap-1 text-gray-500 text-sm">
                    <MapPin size={14} className="text-primary-500" />
                    {p.location}
                  </div>
                </div>

                <div className="text-right">
                  <p className="text-2xl font-bold text-primary-600">
                    {formatPrice(p.price, p.price_period)}
                  </p>
                  <div className="flex items-center gap-1 justify-end text-gray-400 text-xs mt-1">
                    <Eye size={12} /> {p.views_count} views
                  </div>
                </div>
              </div>

              {/* Features */}
              <div className="flex flex-wrap gap-4 mt-5 pt-5 border-t border-gray-100">
                {p.bedrooms != null && (
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center">
                      <Bed size={16} className="text-blue-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-dark-900">{p.bedrooms}</p>
                      <p className="text-xs text-gray-500">Bedrooms</p>
                    </div>
                  </div>
                )}
                {p.bathrooms != null && (
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-9 h-9 bg-cyan-50 rounded-xl flex items-center justify-center">
                      <Bath size={16} className="text-cyan-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-dark-900">{p.bathrooms}</p>
                      <p className="text-xs text-gray-500">Bathrooms</p>
                    </div>
                  </div>
                )}
                {p.plot_size && (
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-9 h-9 bg-green-50 rounded-xl flex items-center justify-center">
                      <Maximize2 size={16} className="text-green-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-dark-900">{p.plot_size} {p.plot_size_unit}</p>
                      <p className="text-xs text-gray-500">Plot Size</p>
                    </div>
                  </div>
                )}
                {p.floor_area && (
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-9 h-9 bg-purple-50 rounded-xl flex items-center justify-center">
                      <Maximize2 size={16} className="text-purple-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-dark-900">{p.floor_area} sqm</p>
                      <p className="text-xs text-gray-500">Floor Area</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Description */}
            {p.description && (
              <div className="bg-white rounded-2xl p-6 shadow-card">
                <h2 className="font-semibold text-dark-900 mb-3">Description</h2>
                <p className="text-gray-600 text-sm leading-relaxed whitespace-pre-line">{p.description}</p>
              </div>
            )}

            {/* Amenities */}
            {p.amenities?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-card">
                <h2 className="font-semibold text-dark-900 mb-3">Amenities</h2>
                <div className="flex flex-wrap gap-2">
                  {p.amenities.map(a => (
                    <span key={a} className="flex items-center gap-1 bg-gray-50 border border-gray-200 text-gray-700 text-xs px-3 py-1.5 rounded-xl">
                      <CheckCircle size={12} className="text-primary-500" />
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Map placeholder */}
            {p.latitude && p.longitude && (
              <div className="bg-white rounded-2xl p-6 shadow-card">
                <h2 className="font-semibold text-dark-900 mb-3 flex items-center gap-2">
                  <MapPin size={16} className="text-primary-500" /> Location
                </h2>
                <div className="aspect-video bg-gray-100 rounded-xl overflow-hidden">
                  <iframe
                    title="Property Location"
                    width="100%"
                    height="100%"
                    style={{ border: 0 }}
                    loading="lazy"
                    src={`https://maps.google.com/maps?q=${p.latitude},${p.longitude}&z=15&output=embed`}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-2">{p.location}</p>
              </div>
            )}
          </div>

          {/* Right — contact sidebar */}
          <div className="space-y-5">
            {/* Owner info */}
            {p.owner && (
              <div className="bg-white rounded-2xl p-5 shadow-card">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                    {p.owner.avatar_url
                      ? <img src={p.owner.avatar_url} alt="" className="w-12 h-12 rounded-full object-cover" />
                      : <span className="text-primary-700 font-semibold text-lg">{p.owner.name?.[0]}</span>
                    }
                  </div>
                  <div>
                    <p className="font-semibold text-dark-900">{p.owner.name}</p>
                    <p className="text-xs text-gray-500">Property Owner</p>
                  </div>
                </div>
                {p.owner.phone && (
                  <a
                    href={`tel:${p.owner.phone}`}
                    className="flex items-center justify-center gap-2 w-full bg-primary-600 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-primary-700 transition-colors"
                  >
                    <Phone size={15} /> Call Owner
                  </a>
                )}
              </div>
            )}

            {/* Contact tabs */}
            <div className="bg-white rounded-2xl p-5 shadow-card">
              <div className="flex rounded-xl overflow-hidden border border-gray-200 mb-4">
                <button
                  onClick={() => setActiveTab('inquiry')}
                  className={clsx('flex-1 py-2.5 text-sm font-medium flex items-center justify-center gap-2 transition-colors',
                    activeTab === 'inquiry' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:bg-gray-50')}
                >
                  <Mail size={14} /> Inquire
                </button>
                <button
                  onClick={() => setActiveTab('viewing')}
                  className={clsx('flex-1 py-2.5 text-sm font-medium flex items-center justify-center gap-2 transition-colors',
                    activeTab === 'viewing' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:bg-gray-50')}
                >
                  <Calendar size={14} /> Book Viewing
                </button>
              </div>

              {activeTab === 'inquiry'
                ? <InquiryForm propertyId={id} />
                : <ViewingForm propertyId={id} />
              }
            </div>

            {/* Share */}
            <div className="bg-white rounded-2xl p-5 shadow-card">
              <div className="flex gap-3">
                <button
                  onClick={() => { navigator.clipboard.writeText(window.location.href); toast.success('Link copied!'); }}
                  className="flex-1 flex items-center justify-center gap-2 border border-gray-200 py-2.5 rounded-xl text-sm text-gray-600 hover:border-primary-400 transition-colors"
                >
                  <Share2 size={14} /> Share
                </button>
                <button
                  onClick={() => toast.success('Added to saved!')}
                  className="flex-1 flex items-center justify-center gap-2 border border-gray-200 py-2.5 rounded-xl text-sm text-gray-600 hover:border-red-400 hover:text-red-500 transition-colors"
                >
                  <Heart size={14} /> Save
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
