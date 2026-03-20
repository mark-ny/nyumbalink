"""
NyumbaLink Test Configuration
──────────────────────────────
Shared pytest fixtures:
  • app       — Flask test app with SQLite in-memory DB
  • client    — Flask test client
  • db_session — SQLAlchemy session, rolled back after each test
  • user_*     — pre-created user fixtures (seeker, owner, admin)
  • tokens_*   — JWT tokens for each role
  • sample_property — verified property fixture
"""

import pytest
import uuid
from flask_jwt_extended import create_access_token

# ── Import app factory ────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app
from models import db as _db, User, Property, PropertyImage


# ── App fixture ───────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def app():
    """Create a Flask application configured for testing."""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'SECRET_KEY': 'test-secret',
        'REDIS_URL': None,          # disable Redis in tests
        'ELASTICSEARCH_URL': None,  # disable ES in tests
        'MAIL_SUPPRESS_SEND': True,
        'CLOUDINARY_CLOUD_NAME': 'test',
        'CLOUDINARY_API_KEY': 'test',
        'CLOUDINARY_API_SECRET': 'test',
        'MPESA_CONSUMER_KEY': 'test',
        'MPESA_CONSUMER_SECRET': 'test',
        'MPESA_SHORTCODE': '174379',
        'MPESA_PASSKEY': 'test',
        'MPESA_CALLBACK_URL': 'http://localhost/callback',
        'LISTING_FEE_KES': 500,
        'WTF_CSRF_ENABLED': False,
    }
    flask_app = create_app('testing')
    flask_app.config.update(test_config)

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Yield db; rollback after each test for isolation."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        yield _db
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


# ── User fixtures ─────────────────────────────────────────────────────

def _make_user(role='seeker', email=None, name='Test User'):
    user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=email or f'{role}-{uuid.uuid4().hex[:6]}@test.com',
        phone='+254712345678',
        role=role,
        is_active=True,
        email_verified=True,
    )
    user.set_password('password123')
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture()
def user_seeker(db):
    return _make_user('seeker', 'seeker@test.com', 'Test Seeker')


@pytest.fixture()
def user_owner(db):
    return _make_user('owner', 'owner@test.com', 'Test Owner')


@pytest.fixture()
def user_admin(db):
    return _make_user('admin', 'admin@test.com', 'Test Admin')


# ── Token fixtures ────────────────────────────────────────────────────

def _make_token(user, app):
    with app.app_context():
        return create_access_token(
            identity=user.id,
            additional_claims={'role': user.role}
        )


@pytest.fixture()
def token_seeker(user_seeker, app):
    return _make_token(user_seeker, app)


@pytest.fixture()
def token_owner(user_owner, app):
    return _make_token(user_owner, app)


@pytest.fixture()
def token_admin(user_admin, app):
    return _make_token(user_admin, app)


# ── Auth header helper ────────────────────────────────────────────────

def auth(token):
    return {'Authorization': f'Bearer {token}'}


# ── Property fixture ──────────────────────────────────────────────────

@pytest.fixture()
def sample_property(db, user_owner):
    prop = Property(
        id=str(uuid.uuid4()),
        title='3 Bedroom Apartment Westlands',
        description='A beautiful apartment in the heart of Westlands.',
        category='rent',
        price=45000,
        price_period='monthly',
        location='Westlands, Nairobi',
        county='Nairobi',
        town='Westlands',
        latitude=-1.2641,
        longitude=36.8069,
        bedrooms=3,
        bathrooms=2,
        floor_area=120.0,
        amenities=['WiFi', 'Parking', 'Security'],
        owner_id=user_owner.id,
        verification_status='verified',
        status='active',
    )
    _db.session.add(prop)

    img = PropertyImage(
        id=str(uuid.uuid4()),
        property_id=prop.id,
        image_url='https://res.cloudinary.com/test/image/upload/sample.jpg',
        public_id='nyumbalink/properties/sample',
        is_primary=True,
    )
    _db.session.add(img)
    _db.session.commit()
    return prop


@pytest.fixture()
def pending_property(db, user_owner):
    prop = Property(
        id=str(uuid.uuid4()),
        title='Studio Apartment Kilimani',
        category='rent',
        price=20000,
        price_period='monthly',
        location='Kilimani, Nairobi',
        county='Nairobi',
        town='Kilimani',
        owner_id=user_owner.id,
        verification_status='pending',
        status='active',
    )
    _db.session.add(prop)
    _db.session.commit()
    return prop
