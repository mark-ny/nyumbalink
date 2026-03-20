"""
NyumbaLink — SEO Routes
────────────────────────
• /api/seo/robots.txt       - search engine crawl rules
• /api/seo/sitemap.xml      - dynamic XML sitemap (properties + static pages)
• /api/seo/meta/<id>        - Open Graph / Twitter Card metadata per property
• slug utility              - human-readable URL slugs
"""

import re
import unicodedata
from datetime import datetime
from flask import Blueprint, Response, jsonify, request, current_app
from models import Property

seo_bp = Blueprint('seo', __name__, url_prefix='/api/seo')

SITE_URL = 'https://nyumbalink.co.ke'


# ── Slug generator ────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert a property title + id fragment into a URL-safe slug.

    Example:
        '3 Bedroom Apartment – Westlands, Nairobi'
        → '3-bedroom-apartment-westlands-nairobi'
    """
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text[:80]  # cap length


def property_slug_url(prop) -> str:
    """Build the canonical SEO-friendly URL for a property."""
    slug = slugify(prop.title)
    # Include location tokens for keyword richness
    location_part = slugify(prop.town or prop.county or '')
    if location_part and location_part not in slug:
        slug = f'{slug}-{location_part}'
    return f'{SITE_URL}/properties/{slug}-{prop.id[:8]}'


# ── robots.txt ────────────────────────────────────────────────────────

@seo_bp.route('/robots.txt')
def robots():
    content = f"""User-agent: *
Allow: /
Allow: /listings
Allow: /properties/

Disallow: /dashboard
Disallow: /admin
Disallow: /api/
Disallow: /login
Disallow: /register

Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(content.strip(), mimetype='text/plain')


# ── sitemap.xml ───────────────────────────────────────────────────────

@seo_bp.route('/sitemap.xml')
def sitemap():
    """
    Dynamic XML sitemap.
    - Static pages (homepage, listings, categories)
    - All published & verified properties
    Cached by nginx for 1 hour in production.
    """
    now = datetime.utcnow().strftime('%Y-%m-%d')

    urls = []

    # Static pages
    static_pages = [
        ('/', '1.0', 'daily'),
        ('/listings', '0.9', 'hourly'),
        ('/listings?category=rent', '0.8', 'hourly'),
        ('/listings?category=short_stay', '0.8', 'hourly'),
        ('/listings?category=plot_sale', '0.8', 'hourly'),
        ('/register', '0.5', 'monthly'),
        ('/login', '0.3', 'monthly'),
    ]
    for path, priority, changefreq in static_pages:
        urls.append({
            'loc':        f'{SITE_URL}{path}',
            'lastmod':    now,
            'changefreq': changefreq,
            'priority':   priority,
        })

    # Property pages — only verified+active
    try:
        properties = (
            Property.query
            .filter_by(verification_status='verified', status='active')
            .with_entities(Property.id, Property.title, Property.town,
                           Property.county, Property.updated_at)
            .order_by(Property.updated_at.desc())
            .limit(50_000)          # sitemap limit
            .all()
        )
        for p in properties:
            slug = slugify(p.title)
            loc  = f'{SITE_URL}/properties/{slug}-{p.id[:8]}'
            urls.append({
                'loc':        loc,
                'lastmod':    p.updated_at.strftime('%Y-%m-%d') if p.updated_at else now,
                'changefreq': 'weekly',
                'priority':   '0.7',
            })
    except Exception as e:
        current_app.logger.warning('Sitemap property fetch failed: %s', e)

    # Build XML
    xml_items = []
    for u in urls:
        xml_items.append(
            f'  <url>\n'
            f'    <loc>{u["loc"]}</loc>\n'
            f'    <lastmod>{u["lastmod"]}</lastmod>\n'
            f'    <changefreq>{u["changefreq"]}</changefreq>\n'
            f'    <priority>{u["priority"]}</priority>\n'
            f'  </url>'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(xml_items) +
        '\n</urlset>'
    )

    resp = Response(xml, mimetype='application/xml')
    resp.headers['Cache-Control'] = 'public, max-age=3600'
    return resp


# ── Open Graph / Twitter Card meta ────────────────────────────────────

@seo_bp.route('/meta/property/<property_id>')
def property_meta(property_id):
    """
    Return Open Graph + Twitter Card metadata for a property.
    Used by the React frontend for server-side meta injection or
    by a link-preview proxy.
    """
    prop = Property.query.get_or_404(property_id)
    image = prop.primary_image.image_url if prop.primary_image else f'{SITE_URL}/og-default.jpg'
    url   = property_slug_url(prop)
    price = f'KES {prop.price:,.0f}' if prop.price else ''

    desc = (prop.description or '')[:160].strip()
    if not desc:
        parts = []
        if prop.bedrooms: parts.append(f'{prop.bedrooms} bed')
        if prop.bathrooms: parts.append(f'{prop.bathrooms} bath')
        parts.append(prop.location)
        if price: parts.append(price)
        desc = ' · '.join(parts)

    meta = {
        # Standard
        'title':       f'{prop.title} | NyumbaLink',
        'description': desc,
        'url':         url,
        'canonical':   url,

        # Open Graph
        'og:type':        'article',
        'og:title':       prop.title,
        'og:description': desc,
        'og:image':       image,
        'og:url':         url,
        'og:site_name':   'NyumbaLink',
        'og:locale':      'en_KE',

        # Twitter Card
        'twitter:card':        'summary_large_image',
        'twitter:title':       prop.title,
        'twitter:description': desc,
        'twitter:image':       image,
        'twitter:site':        '@NyumbaLink',

        # Structured data (JSON-LD hint)
        'schema_type':  'RealEstateListing',
        'price':        str(prop.price) if prop.price else None,
        'currency':     'KES',
        'location':     prop.location,
        'category':     prop.category,
    }
    return jsonify(meta), 200


# ── Slug-based property lookup ────────────────────────────────────────

@seo_bp.route('/resolve/<slug>')
def resolve_slug(slug):
    """
    Resolve a slug like 'three-bedroom-apartment-westlands-abc12345'
    → returns the canonical property_id so the SPA can fetch details.

    The last 8 chars of the slug are the property ID fragment.
    """
    if len(slug) < 8:
        return jsonify({'error': 'Invalid slug'}), 400

    id_fragment = slug[-8:]
    prop = Property.query.filter(Property.id.like(f'{id_fragment}%')).first()
    if not prop:
        return jsonify({'error': 'Property not found'}), 404

    return jsonify({
        'property_id':  prop.id,
        'canonical_url': property_slug_url(prop),
    }), 200
