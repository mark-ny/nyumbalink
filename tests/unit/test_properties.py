"""
Unit Tests — Properties
────────────────────────
Tests: list, get, create, update, delete, pagination, sorting, filtering
"""

import pytest
import uuid
from tests.conftest import auth
from models import db as _db, Property


class TestListProperties:

    def test_list_returns_only_verified(self, client, db, sample_property, pending_property):
        res = client.get('/api/properties')
        assert res.status_code == 200
        data = res.get_json()
        ids = [p['id'] for p in data['properties']]
        assert sample_property.id in ids
        assert pending_property.id not in ids

    def test_list_pagination_defaults(self, client, db, sample_property):
        res = client.get('/api/properties')
        assert res.status_code == 200
        data = res.get_json()
        assert 'pagination' in data
        pg = data['pagination']
        assert pg['page'] == 1
        assert pg['per_page'] == 12

    def test_list_custom_page_size(self, client, db, sample_property):
        res = client.get('/api/properties?per_page=3&page=1')
        assert res.status_code == 200
        pg = res.get_json()['pagination']
        assert pg['per_page'] == 3

    def test_list_per_page_max_capped(self, client, db):
        res = client.get('/api/properties?per_page=999')
        pg = res.get_json()['pagination']
        assert pg['per_page'] <= 50

    def test_list_filter_by_category(self, client, db, sample_property):
        res = client.get('/api/properties?category=rent')
        assert res.status_code == 200
        props = res.get_json()['properties']
        for p in props:
            assert p['category'] == 'rent'

    def test_list_filter_by_county(self, client, db, sample_property):
        res = client.get('/api/properties?county=Nairobi')
        assert res.status_code == 200
        props = res.get_json()['properties']
        for p in props:
            assert 'Nairobi' in (p.get('county') or '')

    def test_list_filter_by_price_range(self, client, db, sample_property):
        res = client.get('/api/properties?min_price=10000&max_price=50000')
        assert res.status_code == 200
        props = res.get_json()['properties']
        for p in props:
            assert 10000 <= p['price'] <= 50000

    def test_list_filter_by_bedrooms(self, client, db, sample_property):
        res = client.get('/api/properties?bedrooms=3')
        assert res.status_code == 200
        props = res.get_json()['properties']
        for p in props:
            assert (p.get('bedrooms') or 0) >= 3

    def test_list_keyword_search(self, client, db, sample_property):
        res = client.get('/api/properties?q=Westlands')
        assert res.status_code == 200
        props = res.get_json()['properties']
        # At minimum our fixture should appear
        assert any('Westlands' in p['title'] or 'Westlands' in (p.get('town') or '')
                   for p in props)

    def test_list_sort_by_price_asc(self, client, db, sample_property):
        res = client.get('/api/properties?sort_by=price&sort_dir=asc')
        assert res.status_code == 200
        props = res.get_json()['properties']
        prices = [p['price'] for p in props]
        assert prices == sorted(prices)

    def test_list_sort_by_price_desc(self, client, db, sample_property):
        res = client.get('/api/properties?sort_by=price&sort_dir=desc')
        assert res.status_code == 200
        props = res.get_json()['properties']
        prices = [p['price'] for p in props]
        assert prices == sorted(prices, reverse=True)

    def test_list_invalid_sort_column_ignored(self, client, db):
        """Should not raise 500; falls back to default sort."""
        res = client.get('/api/properties?sort_by=password_hash')
        assert res.status_code == 200

    def test_list_pagination_structure(self, client, db):
        res = client.get('/api/properties')
        data = res.get_json()
        pg = data['pagination']
        assert all(k in pg for k in ['total', 'page', 'per_page', 'pages'])


class TestGetProperty:

    def test_get_existing_property(self, client, db, sample_property):
        res = client.get(f'/api/properties/{sample_property.id}')
        assert res.status_code == 200
        data = res.get_json()
        assert data['id'] == sample_property.id
        assert data['title'] == sample_property.title

    def test_get_increments_view_count(self, client, db, sample_property):
        initial_views = sample_property.views_count or 0
        client.get(f'/api/properties/{sample_property.id}')
        _db.session.refresh(sample_property)
        assert (sample_property.views_count or 0) == initial_views + 1

    def test_get_nonexistent_property(self, client, db):
        res = client.get(f'/api/properties/{uuid.uuid4()}')
        assert res.status_code == 404

    def test_get_includes_owner(self, client, db, sample_property):
        res = client.get(f'/api/properties/{sample_property.id}')
        data = res.get_json()
        assert 'owner' in data
        assert 'name' in data['owner']

    def test_get_includes_images(self, client, db, sample_property):
        res = client.get(f'/api/properties/{sample_property.id}')
        data = res.get_json()
        assert isinstance(data['images'], list)
        assert len(data['images']) > 0


class TestCreateProperty:

    def _payload(self):
        return {
            'title': 'New Bedsitter Lavington',
            'description': 'A nice bedsitter in Lavington with all amenities.',
            'category': 'rent',
            'price': 15000,
            'price_period': 'monthly',
            'location': 'Lavington, Nairobi',
            'county': 'Nairobi',
            'town': 'Lavington',
            'bedrooms': 0,
            'bathrooms': 1,
        }

    def test_create_as_owner(self, client, db, user_owner, token_owner):
        res = client.post('/api/properties',
                          headers=auth(token_owner),
                          json=self._payload())
        assert res.status_code == 201
        data = res.get_json()
        assert data['property']['title'] == 'New Bedsitter Lavington'
        assert data['property']['verification_status'] == 'pending'

    def test_create_as_seeker_forbidden(self, client, db, user_seeker, token_seeker):
        res = client.post('/api/properties',
                          headers=auth(token_seeker),
                          json=self._payload())
        assert res.status_code == 403

    def test_create_unauthenticated(self, client, db):
        res = client.post('/api/properties', json=self._payload())
        assert res.status_code == 401

    def test_create_missing_required_field(self, client, db, token_owner):
        payload = self._payload()
        del payload['category']
        res = client.post('/api/properties',
                          headers=auth(token_owner),
                          json=payload)
        assert res.status_code == 400

    def test_create_invalid_category(self, client, db, token_owner):
        payload = self._payload()
        payload['category'] = 'invalid_cat'
        res = client.post('/api/properties',
                          headers=auth(token_owner),
                          json=payload)
        assert res.status_code == 400

    def test_create_negative_price(self, client, db, token_owner):
        payload = self._payload()
        payload['price'] = -1000
        res = client.post('/api/properties',
                          headers=auth(token_owner),
                          json=payload)
        assert res.status_code == 400

    def test_create_sets_owner_id(self, client, db, user_owner, token_owner):
        res = client.post('/api/properties',
                          headers=auth(token_owner),
                          json=self._payload())
        assert res.status_code == 201
        assert res.get_json()['property']['owner_id'] == user_owner.id

    def test_create_as_admin(self, client, db, user_admin, token_admin):
        res = client.post('/api/properties',
                          headers=auth(token_admin),
                          json=self._payload())
        assert res.status_code == 201


class TestUpdateProperty:

    def test_owner_can_update_own_property(self, client, db, sample_property, token_owner):
        res = client.put(f'/api/properties/{sample_property.id}',
                         headers=auth(token_owner),
                         json={'title': 'Updated Title Here'})
        assert res.status_code == 200
        assert res.get_json()['property']['title'] == 'Updated Title Here'

    def test_other_owner_cannot_update(self, client, db, sample_property, db_session=None):
        """A different owner should get 403."""
        # Create a second owner
        other_owner = _make_other_owner(db)
        from flask_jwt_extended import create_access_token
        with _db.session.no_autoflush:
            token = _create_token_for(other_owner)

        res = client.put(f'/api/properties/{sample_property.id}',
                         headers=auth(token),
                         json={'title': 'Hijacked Title'})
        assert res.status_code == 403

    def test_admin_can_update_any_property(self, client, db, sample_property, token_admin):
        res = client.put(f'/api/properties/{sample_property.id}',
                         headers=auth(token_admin),
                         json={'price': 55000})
        assert res.status_code == 200
        assert res.get_json()['property']['price'] == 55000

    def test_update_nonexistent(self, client, db, token_owner):
        res = client.put(f'/api/properties/{uuid.uuid4()}',
                         headers=auth(token_owner),
                         json={'title': 'Ghost'})
        assert res.status_code == 404

    def test_significant_update_resets_verification(self, client, db, sample_property, token_owner):
        """Changing price should reset verification_status to pending."""
        assert sample_property.verification_status == 'verified'
        res = client.put(f'/api/properties/{sample_property.id}',
                         headers=auth(token_owner),
                         json={'price': 99999})
        assert res.status_code == 200
        assert res.get_json()['property']['verification_status'] == 'pending'


class TestDeleteProperty:

    def test_owner_can_delete(self, client, db, sample_property, token_owner):
        res = client.delete(f'/api/properties/{sample_property.id}',
                            headers=auth(token_owner))
        assert res.status_code == 200
        # Verify it's gone
        get = client.get(f'/api/properties/{sample_property.id}')
        assert get.status_code == 404

    def test_seeker_cannot_delete(self, client, db, sample_property, token_seeker):
        res = client.delete(f'/api/properties/{sample_property.id}',
                            headers=auth(token_seeker))
        assert res.status_code == 403

    def test_admin_can_delete_any(self, client, db, sample_property, token_admin):
        res = client.delete(f'/api/properties/{sample_property.id}',
                            headers=auth(token_admin))
        assert res.status_code == 200


class TestMyListings:

    def test_owner_sees_own_listings(self, client, db, sample_property, token_owner):
        res = client.get('/api/properties/my/listings', headers=auth(token_owner))
        assert res.status_code == 200
        ids = [p['id'] for p in res.get_json()['properties']]
        assert sample_property.id in ids

    def test_unauthenticated_cannot_access(self, client, db):
        res = client.get('/api/properties/my/listings')
        assert res.status_code == 401

    def test_my_listings_pagination(self, client, db, sample_property, token_owner):
        res = client.get('/api/properties/my/listings?page=1&per_page=5',
                         headers=auth(token_owner))
        assert res.status_code == 200
        pg = res.get_json()['pagination']
        assert 'total' in pg


# ── Helpers ────────────────────────────────────────────────────────────

def _make_other_owner(db):
    other = Property.__table__  # just ensure db is used
    u = __import__('models', fromlist=['User']).User(
        id=str(uuid.uuid4()),
        name='Other Owner',
        email=f'other-{uuid.uuid4().hex[:6]}@test.com',
        role='owner',
        is_active=True,
    )
    u.set_password('password123')
    _db.session.add(u)
    _db.session.commit()
    return u


def _create_token_for(user):
    from flask_jwt_extended import create_access_token
    return create_access_token(identity=user.id, additional_claims={'role': user.role})
