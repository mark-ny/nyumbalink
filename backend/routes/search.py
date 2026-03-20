from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Property, Notification
from services.elasticsearch_service import search_properties
import math

search_bp = Blueprint('search', __name__, url_prefix='/api/search')
notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@search_bp.route('', methods=['GET'])
def advanced_search():
    """Elasticsearch-powered advanced search"""
    q = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 12)), 50)

    filters = {
        'category': request.args.get('category'),
        'county': request.args.get('county'),
        'min_price': request.args.get('min_price', type=float),
        'max_price': request.args.get('max_price', type=float),
        'bedrooms': request.args.get('bedrooms', type=int),
        'min_plot': request.args.get('min_plot', type=float),
    }
    filters = {k: v for k, v in filters.items() if v is not None}

    try:
        es_result = search_properties(q, filters, page, per_page)
        prop_ids = es_result['ids']
        total = es_result['total']

        if prop_ids:
            props = Property.query.filter(Property.id.in_(prop_ids)).all()
            # Maintain ES relevance order
            id_order = {pid: i for i, pid in enumerate(prop_ids)}
            props.sort(key=lambda p: id_order.get(p.id, 999))
        else:
            props = []

    except Exception:
        # Fallback to SQL search if ES is down
        query = Property.query.filter_by(verification_status='verified', status='active')
        if q:
            query = query.filter(
                db.or_(
                    Property.title.ilike(f'%{q}%'),
                    Property.location.ilike(f'%{q}%'),
                    Property.town.ilike(f'%{q}%'),
                )
            )
        if filters.get('category'):
            query = query.filter_by(category=filters['category'])
        if filters.get('county'):
            query = query.filter(Property.county.ilike(f'%{filters["county"]}%'))
        if filters.get('min_price'):
            query = query.filter(Property.price >= filters['min_price'])
        if filters.get('max_price'):
            query = query.filter(Property.price <= filters['max_price'])
        if filters.get('bedrooms'):
            query = query.filter(Property.bedrooms >= filters['bedrooms'])

        total = query.count()
        props = query.order_by(Property.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

    return jsonify({
        'properties': [p.to_dict(include_owner=True) for p in props],
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': math.ceil(total / per_page) if total else 0,
        },
        'query': q,
        'filters': filters,
    }), 200


# --- NOTIFICATIONS ---

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    page = int(request.args.get('page', 1))
    per_page = 20

    query = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc())
    total = query.count()
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    notifications = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count,
        'pagination': {'total': total, 'page': page, 'per_page': per_page, 'pages': math.ceil(total / per_page)},
    }), 200


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    user_id = get_jwt_identity()
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'}), 200


@notifications_bp.route('/<notif_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notif_id):
    user_id = get_jwt_identity()
    notif = Notification.query.filter_by(id=notif_id, user_id=user_id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Notification marked as read'}), 200
