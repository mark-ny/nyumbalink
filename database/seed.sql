-- ════════════════════════════════════════════════════════════
--  NyumbaLink — Supabase Seed Data
--  Run AFTER schema.sql has been applied
--  Run in: Supabase Dashboard → SQL Editor
-- ════════════════════════════════════════════════════════════

-- ── Sample Counties / Locations for autocomplete ─────────────
-- (These are used by the frontend search dropdowns)

-- ── Seed admin user ──────────────────────────────────────────
-- Password: NyumbaAdmin2024!
-- Change immediately after first login via /api/auth/change-password
--
-- Hash generated with:
--   python -c "import bcrypt; print(bcrypt.hashpw(b'NyumbaAdmin2024!', bcrypt.gensalt(12)).decode())"
--
-- IMPORTANT: Run scripts/seed.py instead — it hashes securely at deploy time
-- This SQL is for reference only

/*
INSERT INTO users (
    id, name, email, phone, password_hash,
    role, is_active, email_verified, created_at
) VALUES (
    uuid_generate_v4(),
    'NyumbaLink Admin',
    'admin@nyumbalink.co.ke',
    '+254700000000',
    '$2b$12$REPLACE_WITH_REAL_HASH',
    'admin',
    TRUE,
    TRUE,
    NOW()
) ON CONFLICT (email) DO NOTHING;
*/

-- ── Sample featured properties (for testing / demo) ──────────
-- Uncomment to seed demo data

/*
-- Owner user for demo properties
INSERT INTO users (id, name, email, phone, password_hash, role, is_active, email_verified)
VALUES (
    'aaaaaaaa-0000-0000-0000-000000000001',
    'Demo Owner',
    'owner@demo.nyumbalink.co.ke',
    '+254712000000',
    '$2b$12$REPLACE_WITH_REAL_HASH',
    'owner', TRUE, TRUE
) ON CONFLICT (email) DO NOTHING;

-- Property 1: 3-bed apartment Westlands
INSERT INTO properties (
    id, title, description, category, price, price_period,
    location, county, town, latitude, longitude,
    bedrooms, bathrooms, floor_area,
    amenities, owner_id,
    verification_status, status, featured
) VALUES (
    uuid_generate_v4(),
    '3 Bedroom Apartment – Westlands, Nairobi',
    'Spacious 3-bedroom apartment in the heart of Westlands. Modern finishes, secure parking, 24/7 security and backup generator.',
    'rent', 75000, 'monthly',
    'Westlands, Nairobi', 'Nairobi', 'Westlands',
    -1.2641, 36.8069,
    3, 2, 130,
    ARRAY['WiFi', 'Parking', 'Security', 'Generator', 'Swimming Pool'],
    'aaaaaaaa-0000-0000-0000-000000000001',
    'verified', 'active', TRUE
);

-- Property 2: Studio Karen
INSERT INTO properties (
    id, title, description, category, price, price_period,
    location, county, town, latitude, longitude,
    bedrooms, bathrooms, floor_area,
    amenities, owner_id,
    verification_status, status, featured
) VALUES (
    uuid_generate_v4(),
    'Modern Studio – Karen, Nairobi',
    'Cozy furnished studio in the leafy suburbs of Karen. Ideal for young professionals.',
    'rent', 35000, 'monthly',
    'Karen, Nairobi', 'Nairobi', 'Karen',
    -1.3167, 36.7167,
    1, 1, 45,
    ARRAY['WiFi', 'Furnished', 'Security', 'Garden'],
    'aaaaaaaa-0000-0000-0000-000000000001',
    'verified', 'active', FALSE
);

-- Property 3: Plot Thika Road
INSERT INTO properties (
    id, title, description, category, price, price_period,
    location, county, town, latitude, longitude,
    plot_size, plot_size_unit,
    amenities, owner_id,
    verification_status, status, featured
) VALUES (
    uuid_generate_v4(),
    '1/8 Acre Plot – Ruiru, Kiambu',
    'Prime 1/8 acre plot along Thika Superhighway in Ruiru. Ready title deed. Ideal for residential development.',
    'plot_sale', 2800000, 'total',
    'Ruiru, Kiambu', 'Kiambu', 'Ruiru',
    -1.1450, 36.9620,
    0.125, 'acres',
    ARRAY['Title Deed', 'Road Access', 'Water Available'],
    'aaaaaaaa-0000-0000-0000-000000000001',
    'verified', 'active', TRUE
);

-- Property 4: Short stay Diani
INSERT INTO properties (
    id, title, description, category, price, price_period,
    location, county, town, latitude, longitude,
    bedrooms, bathrooms, floor_area,
    amenities, owner_id,
    verification_status, status, featured
) VALUES (
    uuid_generate_v4(),
    'Beachfront Villa – Diani, Mombasa',
    'Stunning 4-bedroom villa steps from Diani Beach. Private pool, ocean views, fully staffed. Perfect for family holidays.',
    'short_stay', 25000, 'per_night',
    'Diani Beach, Kwale', 'Kwale', 'Diani',
    -4.3172, 39.5673,
    4, 3, 280,
    ARRAY['Swimming Pool', 'Beach Access', 'WiFi', 'Air Conditioning', 'Chef', 'Security'],
    'aaaaaaaa-0000-0000-0000-000000000001',
    'verified', 'active', TRUE
);
*/

-- ── Verification: count seeded rows ──────────────────────────
SELECT
    'users'            AS tbl, COUNT(*) AS rows FROM users
UNION ALL
SELECT 'properties',    COUNT(*) FROM properties
UNION ALL
SELECT 'property_images', COUNT(*) FROM property_images
UNION ALL
SELECT 'payments',      COUNT(*) FROM payments;
