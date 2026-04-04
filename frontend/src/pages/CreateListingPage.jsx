import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { propertiesAPI } from '../services/api';
import api from '../services/api';
import toast from 'react-hot-toast';

const CLOUD_NAME = process.env.REACT_APP_CLOUDINARY_CLOUD_NAME || 'dxxghgi46';
const UPLOAD_PRESET = 'nyumbalink_properties';

export default function CreateListingPage() {
  const navigate = useNavigate();
  const fileRef = useRef();
  const [form, setForm] = useState({
    title: '', category: 'rent', price: '',
    price_period: 'monthly', location: '', county: '',
    town: '', bedrooms: '', bathrooms: '', description: '',
  });
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);

  const uploadToCloudinary = async (file) => {
    const data = new FormData();
    data.append('file', file);
    data.append('upload_preset', UPLOAD_PRESET);
    data.append('folder', 'nyumbalink/properties');
    const res = await fetch(
      `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/image/upload`,
      { method: 'POST', body: data }
    );
    const json = await res.json();
    if (json.error) throw new Error(json.error.message);
    return { url: json.secure_url, public_id: json.public_id };
  };

  const handleImageSelect = async (e) => {
    const files = Array.from(e.target.files);
    if (images.length + files.length > 10) {
      toast.error('Maximum 10 images allowed');
      return;
    }
    setUploading(true);
    try {
      const uploaded = await Promise.all(files.map(uploadToCloudinary));
      setImages(prev => [...prev, ...uploaded]);
      toast.success(`${uploaded.length} image(s) uploaded!`);
    } catch (err) {
      toast.error('Image upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const removeImage = (index) => {
    setImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (images.length === 0) {
      toast.error('Please upload at least one image');
      return;
    }
    setLoading(true);
    try {
      // Step 1: Create the property
      const res = await propertiesAPI.create({
        ...form,
        price: parseFloat(form.price),
        bedrooms: form.bedrooms ? parseInt(form.bedrooms) : undefined,
        bathrooms: form.bathrooms ? parseInt(form.bathrooms) : undefined,
      });
      const propertyId = res.data.property.id;

      // Step 2: Save Cloudinary URLs directly to backend
      // No re-uploading — just send the URLs we already have
      await api.post(`/properties/${propertyId}/images/urls`, {
        images: images.map((img, i) => ({
          image_url: img.url,
          public_id: img.public_id,
          is_primary: i === 0,
          sort_order: i,
        }))
      });

      toast.success('Property created successfully!');
      navigate(`/properties/${propertyId}`);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create property');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: '100%', border: '1px solid #e5e7eb',
    borderRadius: 10, padding: '10px 14px', fontSize: 14,
    outline: 'none', fontFamily: 'inherit',
  };
  const labelStyle = { display: 'block', fontWeight: 600, marginBottom: 6, fontSize: 14 };

  return (
    <div style={{ maxWidth: 680, margin: '40px auto', padding: '0 20px 60px' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Create Listing</h1>
      <p style={{ color: '#6b7280', marginBottom: 32 }}>Fill in your property details</p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

        {/* Images */}
        <div>
          <label style={labelStyle}>Property Photos *</label>
          <div
            onClick={() => !uploading && fileRef.current.click()}
            style={{
              border: '2px dashed #d1d5db', borderRadius: 12, padding: 24,
              textAlign: 'center', cursor: uploading ? 'wait' : 'pointer',
              background: '#f9fafb',
            }}
          >
            <div style={{ fontSize: 32, marginBottom: 8 }}>📸</div>
            <p style={{ fontWeight: 600, color: '#374151' }}>
              {uploading ? 'Uploading...' : 'Tap to upload photos'}
            </p>
            <p style={{ color: '#9ca3af', fontSize: 13, marginTop: 4 }}>
              JPG, PNG or WEBP · Max 10 photos
            </p>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              multiple
              style={{ display: 'none' }}
              onChange={handleImageSelect}
            />
          </div>

          {images.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 12 }}>
              {images.map((img, i) => (
                <div key={i} style={{ position: 'relative', aspectRatio: '1', borderRadius: 10, overflow: 'hidden' }}>
                  <img src={img.url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  {i === 0 && (
                    <span style={{
                      position: 'absolute', top: 4, left: 4,
                      background: '#16a34a', color: '#fff',
                      fontSize: 10, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                    }}>MAIN</span>
                  )}
                  <button
                    type="button"
                    onClick={() => removeImage(i)}
                    style={{
                      position: 'absolute', top: 4, right: 4,
                      background: 'rgba(0,0,0,0.6)', color: '#fff',
                      border: 'none', borderRadius: '50%',
                      width: 22, height: 22, cursor: 'pointer', fontSize: 12,
                    }}
                  >✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <label style={labelStyle}>Property Title *</label>
          <input
            required value={form.title}
            onChange={e => setForm(p => ({...p, title: e.target.value}))}
            placeholder="e.g. 3 Bedroom Apartment in Westlands"
            style={inputStyle}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div>
            <label style={labelStyle}>Category *</label>
            <select value={form.category} onChange={e => setForm(p => ({...p, category: e.target.value}))} style={inputStyle}>
              <option value="rent">For Rent</option>
              <option value="short_stay">Short Stay</option>
              <option value="plot_sale">Plot Sale</option>
            </select>
          </div>
          <div>
            <label style={labelStyle}>Price Period</label>
            <select value={form.price_period} onChange={e => setForm(p => ({...p, price_period: e.target.value}))} style={inputStyle}>
              <option value="monthly">Per Month</option>
              <option value="per_night">Per Night</option>
              <option value="yearly">Per Year</option>
              <option value="total">Total Price</option>
            </select>
          </div>
        </div>

        <div>
          <label style={labelStyle}>Price (KES) *</label>
          <input
            required type="number" value={form.price}
            onChange={e => setForm(p => ({...p, price: e.target.value}))}
            placeholder="e.g. 45000"
            style={inputStyle}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div>
            <label style={labelStyle}>Bedrooms</label>
            <select value={form.bedrooms} onChange={e => setForm(p => ({...p, bedrooms: e.target.value}))} style={inputStyle}>
              <option value="">Select</option>
              {[0,1,2,3,4,5,6].map(n => (
                <option key={n} value={n}>{n === 0 ? 'Bedsitter' : `${n} Bed${n>1?'s':''}`}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Bathrooms</label>
            <select value={form.bathrooms} onChange={e => setForm(p => ({...p, bathrooms: e.target.value}))} style={inputStyle}>
              <option value="">Select</option>
              {[1,2,3,4,5].map(n => (
                <option key={n} value={n}>{n} Bath{n>1?'s':''}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label style={labelStyle}>Full Address / Estate *</label>
          <input
            required value={form.location}
            onChange={e => setForm(p => ({...p, location: e.target.value}))}
            placeholder="e.g. Westlands, off Waiyaki Way"
            style={inputStyle}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div>
            <label style={labelStyle}>County</label>
            <select value={form.county} onChange={e => setForm(p => ({...p, county: e.target.value}))} style={inputStyle}>
              <option value="">Select County</option>
              {['Nairobi','Mombasa','Kisumu','Nakuru','Kiambu','Machakos','Kajiado',
                'Eldoret','Nyeri','Meru','Kilifi','Kwale','Lamu','Kisii','Kakamega'].map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Town / Area</label>
            <input
              value={form.town}
              onChange={e => setForm(p => ({...p, town: e.target.value}))}
              placeholder="e.g. Westlands"
              style={inputStyle}
            />
          </div>
        </div>

        <div>
          <label style={labelStyle}>Description</label>
          <textarea
            value={form.description}
            onChange={e => setForm(p => ({...p, description: e.target.value}))}
            placeholder="Describe the property..."
            rows={4}
            style={{ ...inputStyle, resize: 'vertical' }}
          />
        </div>

        <button
          type="submit"
          disabled={loading || uploading}
          style={{
            background: loading || uploading ? '#9ca3af' : '#16a34a',
            color: '#fff', border: 'none', borderRadius: 12,
            padding: '16px', fontSize: 16, fontWeight: 700,
            cursor: loading || uploading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Creating...' : uploading ? 'Uploading Images...' : '🏠 Create Listing'}
        </button>
      </form>
    </div>
  );
}
