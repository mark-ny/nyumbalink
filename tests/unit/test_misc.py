"""
Unit Tests — Inquiries, Viewings, Admin, Pagination, SEO
─────────────────────────────────────────────────────────
"""

import pytest
import uuid
from tests.conftest import auth
from models import db as _db, Property, Inquiry, ViewingRequest, Lead


# ──────────────────────────────────────────────────────────────────────
#  Inquiries
# ──────────────────────────────────────────────────────────────────────

class TestInquiries:

    def _inquiry_payload(self, property_id):
        return {
            'property_id': property_id,
            'name':        'Kamau Njoroge',
            'email':       'kamau@test.com',
            'phone':       '+254712000000',
            'message':     'I am very interested in this property. Is it still available?',
        }

    def test_create_inquiry_success(self, client, db, sample_property):
        res = client.post('/api/inquiries',
                          json=self._inquiry_payload(sample_property.id))
        assert res.status_code == 201
        data = res.get_json()
        assert 'inquiry' in data
        assert data['inquiry']['name'] == 'Kamau Njoroge'

    def test_inquiry_creates_lead(self, client, db, sample_property):
        client.post('/api/inquiries',
                    json=self._inquiry_payload(sample_property.id))
        lead = Lead.query.filter_by(
            property_id=sample_property.id, source='inquiry'
        ).first()
        assert lead is not None
        assert lead.name == 'Kamau Njoroge'
        assert lead.status == 'new'

    def test_inquiry_missing_message(self, client, db, sample_property):
        payload = self._inquiry_payload(sample_property.id)
        del payload['message']
        res = client.post('/api/inquiries', json=payload)
        assert res.status_code == 400

    def test_inquiry_short_message(self, client, db, sample_property):
        payload = self._inquiry_payload(sample_property.id)
        payload['message'] = 'Hi'   # < 10 chars
        res = client.post('/api/inquiries', json=payload)
        assert res.status_code == 400

    def test_inquiry_nonexistent_property(self, client, db):
        payload = {
            'property_id': str(uuid.uuid4()),
            'name':        'Test',
            'message':     'I am interested in this property listing.',
        }
        res = client.post('/api/inquiries', json=payload)
        assert res.status_code == 404

    def test_owner_can_view_inquiries(self, client, db, sample_property,
                                      user_owner, token_owner):
        # Create one inquiry first
        client.post('/api/inquiries',
                    json=self._inquiry_payload(sample_property.id))

        res = client.get('/api/inquiries/my', headers=auth(token_owner))
        assert res.status_code == 200
        data = res.get_json()
        assert 'inquiries' in data
        assert len(data['inquiries']) >= 1

    def test_seeker_can_view_own_inquiries(self, client, db, sample_property,
                                            token_seeker):
        client.post('/api/inquiries',
                    json=self._inquiry_payload(sample_property.id))
        res = client.get('/api/inquiries/my', headers=auth(token_seeker))
        assert res.status_code == 200

    def test_inquiry_unauthenticated_allowed(self, client, db, sample_property):
        """Inquiries can be submitted without auth."""
        res = client.post('/api/inquiries',
                          json=self._inquiry_payload(sample_property.id))
        assert res.status_code == 201


# ──────────────────────────────────────────────────────────────────────
#  Viewings
# ──────────────────────────────────────────────────────────────────────

class TestViewings:

    def _viewing_payload(self, property_id):
        return {
            'property_id':    property_id,
            'name':           'Amina Hassan',
            'phone':          '+254733000000',
            'email':          'amina@test.com',
            'preferred_date': '2026-04-01',
            'preferred_time': '10:00',
            'message':        'Please confirm availability.',
        }

    def test_create_viewing_success(self, client, db, sample_property):
        res = client.post('/api/viewings',
                          json=self._viewing_payload(sample_property.id))
        assert res.status_code == 201
        data = res.get_json()
        assert 'viewing' in data
        assert data['viewing']['status'] == 'pending'

    def test_viewing_creates_lead(self, client, db, sample_property):
        client.post('/api/viewings',
                    json=self._viewing_payload(sample_property.id))
        lead = Lead.query.filter_by(
            property_id=sample_property.id, source='viewing_request'
        ).first()
        assert lead is not None

    def test_viewing_missing_date(self, client, db, sample_property):
        payload = self._viewing_payload(sample_property.id)
        del payload['preferred_date']
        res = client.post('/api/viewings', json=payload)
        assert res.status_code == 400

    def test_viewing_nonexistent_property(self, client, db):
        payload = self._viewing_payload(str(uuid.uuid4()))
        res = client.post('/api/viewings', json=payload)
        assert res.status_code == 404

    def test_owner_can_see_viewing_requests(self, client, db, sample_property,
                                             token_owner):
        client.post('/api/viewings',
                    json=self._viewing_payload(sample_property.id))
        res = client.get('/api/viewings/my', headers=auth(token_owner))
        assert res.status_code == 200
        assert len(res.get_json()['viewings']) >= 1

    def test_owner_can_confirm_viewing(self, client, db, sample_property,
                                        token_owner):
        create_res = client.post('/api/viewings',
                                 json=self._viewing_payload(sample_property.id))
        viewing_id = create_res.get_json()['viewing']['id']

        res = client.put(f'/api/viewings/{viewing_id}/status',
                         headers=auth(token_owner),
                         json={'status': 'confirmed',
                               'confirmed_date': '2026-04-01',
                               'confirmed_time': '10:00'})
        assert res.status_code == 200
        assert res.get_json()['viewing']['status'] == 'confirmed'

    def test_owner_can_cancel_viewing(self, client, db, sample_property, token_owner):
        create_res = client.post('/api/viewings',
                                 json=self._viewing_payload(sample_property.id))
        vid = create_res.get_json()['viewing']['id']
        res = client.put(f'/api/viewings/{vid}/status',
                         headers=auth(token_owner),
                         json={'status': 'cancelled'})
        assert res.status_code == 200

    def test_invalid_status_rejected(self, client, db, sample_property, token_owner):
        create_res = client.post('/api/viewings',
                                 json=self._viewing_payload(sample_property.id))
        vid = create_res.get_json()['viewing']['id']
        res = client.put(f'/api/viewings/{vid}/status',
                         headers=auth(token_owner),
                         json={'status': 'ghost'})
        assert res.status_code == 400


# ──────────────────────────────────────────────────────────────────────
#  Admin
# ──────────────────────────────────────────────────────────────────────

class TestAdmin:

    def test_dashboard_as_admin(self, client, db, token_admin):
        res = client.get('/api/admin/dashboard', headers=auth(token_admin))
        assert res.status_code == 200
        data = res.get_json()
        assert 'users' in data
        assert 'properties' in data
        assert 'payments' in data

    def test_dashboard_as_seeker_forbidden(self, client, db, token_seeker):
        res = client.get('/api/admin/dashboard', headers=auth(token_seeker))
        assert res.status_code == 403

    def test_dashboard_unauthenticated(self, client, db):
        res = client.get('/api/admin/dashboard')
        assert res.status_code == 401

    def test_verify_property_approved(self, client, db, pending_property, token_admin):
        res = client.put(
            f'/api/admin/properties/{pending_property.id}/verify',
            headers=auth(token_admin),
            json={'verification_status': 'verified'},
        )
        assert res.status_code == 200
        assert res.get_json()['property']['verification_status'] == 'verified'

    def test_verify_property_rejected(self, client, db, pending_property, token_admin):
        res = client.put(
            f'/api/admin/properties/{pending_property.id}/verify',
            headers=auth(token_admin),
            json={'verification_status': 'rejected', 'reason': 'Fake photos'},
        )
        assert res.status_code == 200
        assert res.get_json()['property']['verification_status'] == 'rejected'

    def test_verify_invalid_status(self, client, db, pending_property, token_admin):
        res = client.put(
            f'/api/admin/properties/{pending_property.id}/verify',
            headers=auth(token_admin),
            json={'verification_status': 'super_approved'},
        )
        assert res.status_code == 400

    def test_owner_cannot_verify_properties(self, client, db, pending_property, token_owner):
        res = client.put(
            f'/api/admin/properties/{pending_property.id}/verify',
            headers=auth(token_owner),
            json={'verification_status': 'verified'},
        )
        assert res.status_code == 403

    def test_admin_list_users(self, client, db, user_seeker, token_admin):
        res = client.get('/api/admin/users', headers=auth(token_admin))
        assert res.status_code == 200
        data = res.get_json()
        assert 'users' in data
        assert 'pagination' in data

    def test_admin_list_users_filter_by_role(self, client, db, user_seeker, token_admin):
        res = client.get('/api/admin/users?role=seeker', headers=auth(token_admin))
        assert res.status_code == 200
        users = res.get_json()['users']
        for u in users:
            assert u['role'] == 'seeker'

    def test_admin_toggle_user_active(self, client, db, user_seeker, token_admin):
        initial = user_seeker.is_active
        res = client.put(f'/api/admin/users/{user_seeker.id}/toggle-active',
                         headers=auth(token_admin))
        assert res.status_code == 200
        assert res.get_json()['is_active'] != initial

    def test_admin_feature_property(self, client, db, sample_property, token_admin):
        initial = sample_property.featured
        res = client.put(f'/api/admin/properties/{sample_property.id}/feature',
                         headers=auth(token_admin))
        assert res.status_code == 200
        assert res.get_json()['featured'] != initial


# ──────────────────────────────────────────────────────────────────────
#  Pagination utility
# ──────────────────────────────────────────────────────────────────────

class TestPaginationUtility:

    def test_paginated_response_structure(self, client, db, sample_property):
        """Test the pagination envelope returned by list endpoints."""
        res = client.get('/api/properties?page=1&per_page=5&sort_by=price&sort_dir=asc')
        assert res.status_code == 200
        data = res.get_json()
        pg = data['pagination']
        required_keys = {'total', 'page', 'per_page', 'pages', 'has_prev', 'has_next',
                         'sort_by', 'sort_dir'}
        assert required_keys.issubset(pg.keys())

    def test_has_prev_false_on_first_page(self, client, db):
        res = client.get('/api/properties?page=1')
        assert res.get_json()['pagination']['has_prev'] is False

    def test_page_zero_treated_as_one(self, client, db):
        res = client.get('/api/properties?page=0')
        assert res.get_json()['pagination']['page'] == 1

    def test_invalid_page_treated_as_one(self, client, db):
        res = client.get('/api/properties?page=banana')
        assert res.get_json()['pagination']['page'] == 1


# ──────────────────────────────────────────────────────────────────────
#  SEO routes
# ──────────────────────────────────────────────────────────────────────

class TestSEO:

    def test_robots_txt(self, client, db):
        res = client.get('/api/seo/robots.txt')
        assert res.status_code == 200
        assert 'User-agent' in res.data.decode()
        assert 'Sitemap' in res.data.decode()

    def test_sitemap_xml(self, client, db, sample_property):
        res = client.get('/api/seo/sitemap.xml')
        assert res.status_code == 200
        assert res.content_type == 'application/xml'
        body = res.data.decode()
        assert '<urlset' in body
        assert '<url>' in body

    def test_sitemap_includes_property(self, client, db, sample_property):
        res = client.get('/api/seo/sitemap.xml')
        body = res.data.decode()
        # Property ID fragment should appear in sitemap
        assert sample_property.id[:8] in body

    def test_property_meta(self, client, db, sample_property):
        res = client.get(f'/api/seo/meta/property/{sample_property.id}')
        assert res.status_code == 200
        data = res.get_json()
        assert 'og:title' in data
        assert 'og:image' in data
        assert 'twitter:card' in data
        assert 'canonical' in data

    def test_resolve_slug(self, client, db, sample_property):
        # Build slug from known property
        fragment = sample_property.id[:8]
        slug = f'some-property-title-{fragment}'
        res = client.get(f'/api/seo/resolve/{slug}')
        assert res.status_code == 200
        assert res.get_json()['property_id'] == sample_property.id

    def test_resolve_invalid_slug(self, client, db):
        res = client.get('/api/seo/resolve/short')
        assert res.status_code == 400

    def test_resolve_unknown_slug(self, client, db):
        res = client.get('/api/seo/resolve/property-that-doesnt-exist-zzzzzzzz')
        assert res.status_code == 404

    def test_meta_nonexistent_property(self, client, db):
        res = client.get(f'/api/seo/meta/property/{uuid.uuid4()}')
        assert res.status_code == 404


# ──────────────────────────────────────────────────────────────────────
#  Health check
# ──────────────────────────────────────────────────────────────────────

class TestHealth:

    def test_health_endpoint(self, client, db):
        res = client.get('/api/health')
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'ok'
        assert 'service' in data
