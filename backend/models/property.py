from datetime import datetime
from . import db


class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(20), nullable=False)  # rent, short_stay, plot_sale
    price = db.Column(db.Numeric(15, 2), nullable=False)
    price_period = db.Column(db.String(50))  # monthly, per_night, total
    location = db.Column(db.String(500), nullable=False)
    county = db.Column(db.String(100))
    town = db.Column(db.String(100))
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    plot_size = db.Column(db.Numeric(10, 2))
    plot_size_unit = db.Column(db.String(20), default='sqm')
    floor_area = db.Column(db.Numeric(10, 2))
    amenities = db.Column(db.ARRAY(db.String))
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    status = db.Column(db.String(20), default='active')  # active, inactive, sold, rented
    featured = db.Column(db.Boolean, default=False)
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    images = db.relationship('PropertyImage', backref='property', lazy='joined', cascade='all, delete-orphan')
    inquiries = db.relationship('Inquiry', backref='property', lazy='dynamic', cascade='all, delete-orphan')
    viewing_requests = db.relationship('ViewingRequest', backref='property', lazy='dynamic', cascade='all, delete-orphan')
    leads = db.relationship('Lead', backref='property', lazy='dynamic')
    saved_by = db.relationship('SavedProperty', backref='property', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='property', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def primary_image(self):
        primary = next((img for img in self.images if img.is_primary), None)
        return primary or (self.images[0] if self.images else None)

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return None
        return sum(r.rating for r in reviews) / len(reviews)

    def to_dict(self, include_owner=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'price': float(self.price) if self.price else None,
            'price_period': self.price_period,
            'location': self.location,
            'county': self.county,
            'town': self.town,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'plot_size': float(self.plot_size) if self.plot_size else None,
            'plot_size_unit': self.plot_size_unit,
            'floor_area': float(self.floor_area) if self.floor_area else None,
            'amenities': self.amenities or [],
            'owner_id': self.owner_id,
            'verification_status': self.verification_status,
            'status': self.status,
            'featured': self.featured,
            'views_count': self.views_count,
            'images': [img.to_dict() for img in self.images],
            'primary_image': self.primary_image.to_dict() if self.primary_image else None,
            'avg_rating': self.avg_rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_owner and self.owner:
            data['owner'] = {
                'id': self.owner.id,
                'name': self.owner.name,
                'phone': self.owner.phone,
                'avatar_url': self.owner.avatar_url,
            }
        return data

    def __repr__(self):
        return f'<Property {self.title}>'


class PropertyImage(db.Model):
    __tablename__ = 'property_images'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    public_id = db.Column(db.String(255))
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'image_url': self.image_url,
            'is_primary': self.is_primary,
            'sort_order': self.sort_order,
        }
