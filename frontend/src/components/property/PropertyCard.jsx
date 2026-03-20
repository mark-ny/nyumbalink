import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Bed, Bath, Maximize2, Heart, Star, Eye, CheckCircle } from 'lucide-react';
import { propertiesAPI } from '../../services/api';
import useAuthStore from '../../hooks/useAuthStore';
import toast from 'react-hot-toast';
import clsx from 'clsx';

const CATEGORY_LABELS = {
  rent: 'For Rent',
  short_stay: 'Short Stay',
  plot_sale: 'For Sale',
};

const CATEGORY_COLORS = {
  rent: 'bg-blue-100 text-blue-700',
  short_stay: 'bg-amber-100 text-amber-700',
  plot_sale: 'bg-green-100 text-green-700',
};

function formatPrice(price, period) {
  const formatted = new Intl.NumberFormat('en-KE', {
    style: 'currency', currency: 'KES', maximumFractionDigits: 0
  }).format(price);
  if (period === 'monthly') return `${formatted}/mo`;
  if (period === 'per_night') return `${formatted}/night`;
  if (period === 'yearly') return `${formatted}/yr`;
  return formatted;
}

export default function PropertyCard({ property, compact = false }) {
  const [saved, setSaved] = useState(false);
  const { isAuthenticated } = useAuthStore();

  const handleSave = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      toast.error('Please sign in to save properties');
      return;
    }
    try {
      const res = await propertiesAPI.save(property.id);
      setSaved(res.data.saved);
      toast.success(res.data.message);
    } catch {
      toast.error('Failed to save property');
    }
  };

  const image = property.primary_image?.image_url
    || property.images?.[0]?.image_url
    || '/placeholder-property.jpg';

  return (
    <Link
      to={`/properties/${property.id}`}
      className={clsx(
        'group bg-white rounded-2xl overflow-hidden shadow-card hover:shadow-card-hover transition-all duration-300 hover:-translate-y-1 flex flex-col',
        compact ? 'h-64' : ''
      )}
    >
      {/* Image */}
      <div className="relative overflow-hidden aspect-[4/3] bg-gray-100">
        <img
          src={image}
          alt={property.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />

        {/* Badges */}
        <div className="absolute top-3 left-3 flex gap-2">
          <span className={clsx('px-2.5 py-1 rounded-lg text-xs font-semibold', CATEGORY_COLORS[property.category])}>
            {CATEGORY_LABELS[property.category]}
          </span>
          {property.featured && (
            <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-500 text-white flex items-center gap-1">
              <Star size={10} fill="currentColor" /> Featured
            </span>
          )}
        </div>

        {/* Save button */}
        <button
          onClick={handleSave}
          className={clsx(
            'absolute top-3 right-3 w-8 h-8 rounded-full flex items-center justify-center transition-all',
            saved
              ? 'bg-red-500 text-white'
              : 'bg-white/80 text-gray-600 hover:bg-white hover:text-red-500'
          )}
        >
          <Heart size={15} fill={saved ? 'currentColor' : 'none'} />
        </button>

        {/* Views */}
        <div className="absolute bottom-3 left-3 flex items-center gap-1 bg-black/40 text-white px-2 py-0.5 rounded-md text-xs">
          <Eye size={11} />
          {property.views_count || 0}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 flex flex-col flex-1">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="font-semibold text-dark-900 text-sm leading-snug line-clamp-2 flex-1">
            {property.title}
          </h3>
          {property.verification_status === 'verified' && (
            <CheckCircle size={15} className="text-primary-500 flex-shrink-0 mt-0.5" />
          )}
        </div>

        <div className="flex items-center gap-1 text-gray-500 text-xs mb-3">
          <MapPin size={12} className="text-primary-500 flex-shrink-0" />
          <span className="truncate">{property.town || property.county || property.location}</span>
        </div>

        {/* Features */}
        {!compact && (
          <div className="flex items-center gap-3 text-xs text-gray-600 mb-3">
            {property.bedrooms != null && (
              <span className="flex items-center gap-1">
                <Bed size={13} className="text-gray-400" />
                {property.bedrooms} {property.bedrooms === 1 ? 'Bed' : 'Beds'}
              </span>
            )}
            {property.bathrooms != null && (
              <span className="flex items-center gap-1">
                <Bath size={13} className="text-gray-400" />
                {property.bathrooms} Bath
              </span>
            )}
            {property.plot_size && (
              <span className="flex items-center gap-1">
                <Maximize2 size={13} className="text-gray-400" />
                {property.plot_size} {property.plot_size_unit || 'sqm'}
              </span>
            )}
          </div>
        )}

        {/* Price */}
        <div className="mt-auto pt-3 border-t border-gray-50">
          <p className="text-primary-600 font-bold text-base">
            {formatPrice(property.price, property.price_period)}
          </p>
        </div>
      </div>
    </Link>
  );
}
