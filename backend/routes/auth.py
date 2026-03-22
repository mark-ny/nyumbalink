from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from marshmallow import Schema, fields, validate, ValidationError
from models import db, User, RefreshToken
from middleware.auth import admin_required
from datetime import datetime, timedelta
import uuid

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# Schemas
class RegisterSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    phone = fields.Str(validate=validate.Length(max=20))
    role = fields.Str(validate=validate.OneOf(['seeker', 'owner']), missing='seeker')


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


@auth_bp.route('/register', methods=['POST'])
def register():
    schema = RegisterSchema()
    try:
        data = schema.load(request.json or {})
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400

    # Check existing
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(
        id=str(uuid.uuid4()),
        name=data['name'],
        email=data['email'].lower(),
        phone=data.get('phone'),
        role=data.get('role', 'seeker'),
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    try:
    except Exception:
        pass

    access_token = create_access_token(identity=user.id, additional_claims={'role': user.role})
    refresh_token = create_refresh_token(identity=user.id)

    # Save refresh token
    _save_refresh_token(user.id, refresh_token)

    return jsonify({
        'message': 'Registration successful',
        'user': user.to_private_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    schema = LoginSchema()
    try:
        data = schema.load(request.json or {})
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400

    user = User.query.filter_by(email=data['email'].lower()).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    access_token = create_access_token(identity=user.id, additional_claims={'role': user.role})
    refresh_token = create_refresh_token(identity=user.id)

    _save_refresh_token(user.id, refresh_token)

    return jsonify({
        'message': 'Login successful',
        'user': user.to_private_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 401

    access_token = create_access_token(identity=user.id, additional_claims={'role': user.role})
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_private_dict()}), 200


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.json or {}
    allowed = ['name', 'phone']
    for field in allowed:
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return jsonify({'user': user.to_private_dict()}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.json or {}

    if not user.check_password(data.get('current_password', '')):
        return jsonify({'error': 'Current password is incorrect'}), 400

    new_pass = data.get('new_password', '')
    if len(new_pass) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    user.set_password(new_pass)
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    # Revoke refresh tokens for this user
    RefreshToken.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({'message': 'Logged out successfully'}), 200


def _save_refresh_token(user_id: str, token: str):
    rt = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.session.add(rt)
    db.session.commit()
