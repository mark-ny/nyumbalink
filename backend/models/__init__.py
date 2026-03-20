from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .property import Property, PropertyImage
from .other_models import (
    Inquiry, Lead, Payment, ViewingRequest,
    Review, SavedProperty, Notification, RefreshToken
)

__all__ = [
    'db', 'User', 'Property', 'PropertyImage',
    'Inquiry', 'Lead', 'Payment', 'ViewingRequest',
    'Review', 'SavedProperty', 'Notification', 'RefreshToken'
]
