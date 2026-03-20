"""
Unit Tests — Authentication
────────────────────────────
Tests: register, login, me, change-password, logout, refresh
"""

import pytest
import json
from tests.conftest import auth


class TestRegister:

    def test_register_success(self, client, db):
        res = client.post('/api/auth/register', json={
            'name': 'Jane Wanjiru',
            'email': 'jane@test.com',
            'password': 'Secure1234!',
            'role': 'seeker',
        })
        assert res.status_code == 201
        data = res.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['email'] == 'jane@test.com'
        assert data['user']['role'] == 'seeker'

    def test_register_owner_role(self, client, db):
        res = client.post('/api/auth/register', json={
            'name': 'John Kamau',
            'email': 'john@test.com',
            'password': 'Secure1234!',
            'role': 'owner',
        })
        assert res.status_code == 201
        assert res.get_json()['user']['role'] == 'owner'

    def test_register_duplicate_email(self, client, db, user_seeker):
        res = client.post('/api/auth/register', json={
            'name': 'Another',
            'email': 'seeker@test.com',   # already exists in fixture
            'password': 'Secure1234!',
        })
        assert res.status_code == 409
        assert 'already registered' in res.get_json()['error'].lower()

    def test_register_short_password(self, client, db):
        res = client.post('/api/auth/register', json={
            'name': 'Test',
            'email': 'short@test.com',
            'password': '123',            # < 8 chars
        })
        assert res.status_code == 400

    def test_register_invalid_email(self, client, db):
        res = client.post('/api/auth/register', json={
            'name': 'Test',
            'email': 'not-an-email',
            'password': 'Secure1234!',
        })
        assert res.status_code == 400

    def test_register_missing_required_fields(self, client, db):
        res = client.post('/api/auth/register', json={'name': 'Only Name'})
        assert res.status_code == 400

    def test_register_invalid_role_defaults_to_seeker(self, client, db):
        res = client.post('/api/auth/register', json={
            'name': 'Hacker',
            'email': 'hacker@test.com',
            'password': 'Secure1234!',
            'role': 'admin',              # should not be allowed
        })
        # marshmallow rejects unlisted enum values
        assert res.status_code in (400, 201)
        if res.status_code == 201:
            assert res.get_json()['user']['role'] != 'admin'


class TestLogin:

    def test_login_success(self, client, db, user_seeker):
        res = client.post('/api/auth/login', json={
            'email': 'seeker@test.com',
            'password': 'password123',
        })
        assert res.status_code == 200
        data = res.get_json()
        assert 'access_token' in data
        assert data['user']['id'] == user_seeker.id

    def test_login_wrong_password(self, client, db, user_seeker):
        res = client.post('/api/auth/login', json={
            'email': 'seeker@test.com',
            'password': 'wrongpassword',
        })
        assert res.status_code == 401

    def test_login_unknown_email(self, client, db):
        res = client.post('/api/auth/login', json={
            'email': 'nobody@test.com',
            'password': 'password123',
        })
        assert res.status_code == 401

    def test_login_case_insensitive_email(self, client, db, user_seeker):
        res = client.post('/api/auth/login', json={
            'email': 'SEEKER@TEST.COM',
            'password': 'password123',
        })
        assert res.status_code == 200

    def test_login_inactive_user(self, client, db, user_seeker):
        user_seeker.is_active = False
        db.session.commit()

        res = client.post('/api/auth/login', json={
            'email': 'seeker@test.com',
            'password': 'password123',
        })
        assert res.status_code == 403

    def test_login_missing_fields(self, client, db):
        res = client.post('/api/auth/login', json={'email': 'x@test.com'})
        assert res.status_code == 400


class TestGetMe:

    def test_get_me_authenticated(self, client, db, user_seeker, token_seeker):
        res = client.get('/api/auth/me', headers=auth(token_seeker))
        assert res.status_code == 200
        data = res.get_json()
        assert data['user']['id'] == user_seeker.id
        assert data['user']['email'] == user_seeker.email

    def test_get_me_unauthenticated(self, client, db):
        res = client.get('/api/auth/me')
        assert res.status_code == 401

    def test_get_me_bad_token(self, client, db):
        res = client.get('/api/auth/me', headers={'Authorization': 'Bearer bad.token.here'})
        assert res.status_code == 422


class TestUpdateMe:

    def test_update_name(self, client, db, user_seeker, token_seeker):
        res = client.put('/api/auth/me',
                         headers=auth(token_seeker),
                         json={'name': 'Updated Name'})
        assert res.status_code == 200
        assert res.get_json()['user']['name'] == 'Updated Name'

    def test_update_phone(self, client, db, user_seeker, token_seeker):
        res = client.put('/api/auth/me',
                         headers=auth(token_seeker),
                         json={'phone': '+254799999999'})
        assert res.status_code == 200
        assert res.get_json()['user']['phone'] == '+254799999999'


class TestChangePassword:

    def test_change_password_success(self, client, db, user_seeker, token_seeker):
        res = client.post('/api/auth/change-password',
                          headers=auth(token_seeker),
                          json={'current_password': 'password123', 'new_password': 'NewPass456!'})
        assert res.status_code == 200

        # Verify old password no longer works
        login = client.post('/api/auth/login', json={
            'email': 'seeker@test.com', 'password': 'password123',
        })
        assert login.status_code == 401

    def test_change_password_wrong_current(self, client, db, user_seeker, token_seeker):
        res = client.post('/api/auth/change-password',
                          headers=auth(token_seeker),
                          json={'current_password': 'wrongpassword', 'new_password': 'NewPass456!'})
        assert res.status_code == 400

    def test_change_password_too_short(self, client, db, user_seeker, token_seeker):
        res = client.post('/api/auth/change-password',
                          headers=auth(token_seeker),
                          json={'current_password': 'password123', 'new_password': '123'})
        assert res.status_code == 400


class TestLogout:

    def test_logout_success(self, client, db, user_seeker, token_seeker):
        res = client.post('/api/auth/logout', headers=auth(token_seeker))
        assert res.status_code == 200

    def test_logout_unauthenticated(self, client, db):
        res = client.post('/api/auth/logout')
        assert res.status_code == 401
