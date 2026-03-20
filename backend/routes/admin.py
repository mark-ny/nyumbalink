from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Property, Payment, Lead, Inquiry, ViewingRequest
from middleware.auth import admin_required
import math

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def dashboard():
    """Admin dashboard stats"""
    stats = {
        'users': {
            'total': User.query.count(),
            'owners': User.query.filter_by(role='owner').count(),
            'seekers': User.query.filter_by(role='seeker').count(),
        },
        'properties': {
            'total': Property.query.count(),
            'pending': Property.query.filter_by(verification_status='pending').count(),
            'verified': Property.query.filter_by(verification_status='verified').count(),
            'rejected': Property.query.filter_by(verification_status='rejected').count(),
            'by_category': {
                'rent': Property.query.filter_by(category='rent').count(),
                'short_stay': Property.query.filter_by(category='short_stay').count(),
                'plot_sale': Property.query.filter_by(category='plot_sale').count(),
            }
        },
        'inquiries': {
            'total': Inquiry.query.count(),
            'unread': Inquiry.query.filter_by(is_read=False).count(),
        },
        'viewings': {
            'total': ViewingRequest.query.count(),
            'pending': ViewingRequest.query.filter_by(status='pending').count(),
        },
        'leads': {
            'total': Lead.query.count(),
            'new': Lead.query.filter_by(status='new').count(),
        },
        'payments': {
            'total': Payment.query.count(),
            'completed': Payment.query.filter_by(status='completed').count(),
            'pending': Payment.query.filter_by(status='pending').count(),
        }
    }
    return jsonify(stats), 200


@admin_bp.route('/properties', methods=['GET'])
@jwt_required()
@admin_required
def list_all_properties():
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 50)
    status_filter = request.args.get('verification_status')
    category = request.args.get('category')

    query = Property.query
    if status_filter:
        query = query.filter_by(verification_status=status_filter)
    if category:
        query = query.filter_by(category=category)

    query = query.order_by(Property.created_at.desc())
    total = query.count()
    properties = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'properties': [p.to_dict(include_owner=True) for p in properties],
        'pagination': {'total': total, 'page': page, 'per_page': per_page, 'pages': math.ceil(total / per_page)}
    }), 200


@admin_bp.route('/properties/<property_id>/verify', methods=['PUT'])
@jwt_required()
@admin_required
def verify_property(property_id):
    prop = Property.query.get_or_404(property_id)
    data = request.json or {}
    status = data.get('verification_status')

    if status not in ['verified', 'rejected', 'pending']:
        return jsonify({'error': 'Invalid verification status'}), 400

    prop.verification_status = status
    if status == 'verified':
        prop.status = 'active'

    db.session.commit()

    # Notify owner
    from models.other_models import Notification
    import uuid
    notif_msg = f'Your property "{prop.title}" has been {status}.'
    if data.get('reason'):
        notif_msg += f' Reason: {data["reason"]}'

    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=prop.owner_id,
        title=f'Property {status.capitalize()}',
        message=notif_msg,
        type='system',
        reference_id=prop.id,
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({'property': prop.to_dict(), 'message': f'Property {status}'}), 200


@admin_bp.route('/properties/<property_id>/feature', methods=['PUT'])
@jwt_required()
@admin_required
def toggle_feature(property_id):
    prop = Property.query.get_or_404(property_id)
    prop.featured = not prop.featured
    db.session.commit()
    return jsonify({'featured': prop.featured}), 200


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def list_users():
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 50)
    role = request.args.get('role')
    q = request.args.get('q', '').strip()

    query = User.query
    if role:
        query = query.filter_by(role=role)
    if q:
        query = query.filter(
            db.or_(User.name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%'))
        )

    query = query.order_by(User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'users': [u.to_private_dict() for u in users],
        'pagination': {'total': total, 'page': page, 'per_page': per_page, 'pages': math.ceil(total / per_page)}
    }), 200


@admin_bp.route('/users/<user_id>/toggle-active', methods=['PUT'])
@jwt_required()
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'is_active': user.is_active}), 200


@admin_bp.route('/users/<user_id>/role', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json or {}
    new_role = data.get('role')

    if new_role not in ['admin', 'owner', 'seeker', 'agent']:
        return jsonify({'error': 'Invalid role'}), 400

    user.role = new_role
    db.session.commit()
    return jsonify({'role': user.role}), 200


@admin_bp.route('/leads', methods=['GET'])
@jwt_required()
@admin_required
def list_leads():
    page = int(request.args.get('page', 1))
    per_page = 20
    status = request.args.get('status')

    query = Lead.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Lead.created_at.desc())

    total = query.count()
    leads = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'leads': [l.to_dict() for l in leads],
        'pagination': {'total': total, 'page': page, 'per_page': per_page, 'pages': math.ceil(total / per_page)}
    }), 200


@admin_bp.route('/payments', methods=['GET'])
@jwt_required()
@admin_required
def list_payments():
    page = int(request.args.get('page', 1))
    per_page = 20
    status = request.args.get('status')

    query = Payment.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Payment.created_at.desc())

    total = query.count()
    payments = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'payments': [p.to_dict() for p in payments],
        'pagination': {'total': total, 'page': page, 'per_page': per_page, 'pages': math.ceil(total / per_page)}
    }), 200
