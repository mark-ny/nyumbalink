from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity
from models import User


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


def owner_or_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') not in ['owner', 'admin', 'agent']:
            return jsonify({'error': 'Owner access required'}), 403
        return f(*args, **kwargs)
    return decorated


def verified_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.email_verified:
            return jsonify({'error': 'Email verification required'}), 403
        return f(*args, **kwargs)
    return decorated
