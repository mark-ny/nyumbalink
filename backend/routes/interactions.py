from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields, validate, ValidationError
from models import db, Inquiry, Lead, ViewingRequest, Property, Notification
from services.notification_service import (
    notify_owner_new_inquiry, notify_owner_viewing_request,
    send_whatsapp_notification
)
import uuid, math

inquiries_bp = Blueprint('inquiries', __name__, url_prefix='/api/inquiries')
viewings_bp = Blueprint('viewings', __name__, url_prefix='/api/viewings')


class InquirySchema(Schema):
    property_id = fields.Str(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    email = fields.Email()
    phone = fields.Str(validate=validate.Length(max=20))
    message = fields.Str(required=True, validate=validate.Length(min=10, max=2000))


class ViewingSchema(Schema):
    property_id = fields.Str(required=True)
    name = fields.Str(validate=validate.Length(max=255))
    email = fields.Email()
    phone = fields.Str(validate=validate.Length(max=20))
    preferred_date = fields.Date(required=True)
    preferred_time = fields.Time()
    message = fields.Str(validate=validate.Length(max=1000))


# --- INQUIRIES ---

@inquiries_bp.route('', methods=['POST'])
def create_inquiry():
    schema = InquirySchema()
    try:
        data = schema.load(request.json or {})
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400

    prop = Property.query.get(data['property_id'])
    if not prop:
        return jsonify({'error': 'Property not found'}), 404

    # Get user_id if authenticated
    user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        pass

    inquiry = Inquiry(
        id=str(uuid.uuid4()),
        property_id=data['property_id'],
        user_id=user_id,
        name=data['name'],
        email=data.get('email'),
        phone=data.get('phone'),
        message=data['message'],
    )
    db.session.add(inquiry)

    # Create lead
    lead = Lead(
        id=str(uuid.uuid4()),
        property_id=data['property_id'],
        owner_id=prop.owner_id,
        name=data['name'],
        phone=data.get('phone'),
        email=data.get('email'),
        message=data['message'],
        source='inquiry',
        status='new',
    )
    db.session.add(lead)

    # Notify owner
    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=prop.owner_id,
        title='New Inquiry',
        message=f'{data["name"]} sent an inquiry about "{prop.title}"',
        type='inquiry',
        reference_id=inquiry.id,
    )
    db.session.add(notif)
    db.session.commit()

    # Send email/whatsapp async
    try:
        notify_owner_new_inquiry(prop, inquiry)
    except Exception:
        pass

    return jsonify({'message': 'Inquiry sent successfully', 'inquiry': inquiry.to_dict()}), 201


@inquiries_bp.route('/property/<property_id>', methods=['GET'])
@jwt_required()
def get_property_inquiries(property_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    prop = Property.query.get_or_404(property_id)

    if prop.owner_id != user_id and claims.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 50)

    query = Inquiry.query.filter_by(property_id=property_id).order_by(Inquiry.created_at.desc())
    total = query.count()
    inquiries = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'inquiries': [i.to_dict() for i in inquiries],
        'pagination': {'total': total, 'page': page, 'per_page': per_page, 'pages': math.ceil(total / per_page)}
    }), 200


@inquiries_bp.route('/my', methods=['GET'])
@jwt_required()
def my_inquiries():
    """Owner: Get all inquiries across all my properties"""
    user_id = get_jwt_identity()
    page = int(request.args.get('page', 1))
    per_page = 20

    my_properties = Property.query.filter_by(owner_id=user_id).with_entities(Property.id).all()
    prop_ids = [p.id for p in my_properties]

    query = Inquiry.query.filter(
        Inquiry.property_id.in_(prop_ids)
    ).order_by(Inquiry.created_at.desc())

    total = query.count()
    inquiries = query.offset((page - 1) * per_page).limit(per_page).all()

    # Mark as read
    for inq in inquiries:
        inq.is_read = True
    db.session.commit()

    return jsonify({
        'inquiries': [i.to_dict() for i in inquiries],
        'pagination': {'total': total, 'page': page, 'per_page': per_page, 'pages': math.ceil(total / per_page)}
    }), 200


# --- VIEWINGS ---

@viewings_bp.route('', methods=['POST'])
def create_viewing():
    schema = ViewingSchema()
    try:
        data = schema.load(request.json or {})
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400

    prop = Property.query.get(data['property_id'])
    if not prop:
        return jsonify({'error': 'Property not found'}), 404

    user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        pass

    viewing = ViewingRequest(
        id=str(uuid.uuid4()),
        property_id=data['property_id'],
        user_id=user_id,
        name=data.get('name'),
        phone=data.get('phone'),
        email=data.get('email'),
        preferred_date=data['preferred_date'],
        preferred_time=data.get('preferred_time'),
        message=data.get('message'),
    )
    db.session.add(viewing)

    # Create lead
    name = data.get('name', 'Unknown')
    lead = Lead(
        id=str(uuid.uuid4()),
        property_id=data['property_id'],
        owner_id=prop.owner_id,
        name=name,
        phone=data.get('phone'),
        email=data.get('email'),
        message=data.get('message', ''),
        source='viewing_request',
        status='new',
    )
    db.session.add(lead)

    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=prop.owner_id,
        title='Viewing Request',
        message=f'{name} requested a viewing of "{prop.title}"',
        type='viewing',
        reference_id=viewing.id,
    )
    db.session.add(notif)
    db.session.commit()

    try:
        notify_owner_viewing_request(prop, viewing)
    except Exception:
        pass

    return jsonify({'message': 'Viewing request sent', 'viewing': viewing.to_dict()}), 201


@viewings_bp.route('/my', methods=['GET'])
@jwt_required()
def my_viewings():
    """Owner: Get viewing requests for my properties"""
    user_id = get_jwt_identity()
    page = int(request.args.get('page', 1))
    per_page = 20

    my_properties = Property.query.filter_by(owner_id=user_id).with_entities(Property.id).all()
    prop_ids = [p.id for p in my_properties]

    query = ViewingRequest.query.filter(
        ViewingRequest.property_id.in_(prop_ids)
    ).order_by(ViewingRequest.created_at.desc())

    total = query.count()
    viewings = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'viewings': [v.to_dict() for v in viewings],
        'pagination': {'total': total, 'page': page, 'per_page': per_page, 'pages': math.ceil(total / per_page)}
    }), 200


@viewings_bp.route('/<viewing_id>/status', methods=['PUT'])
@jwt_required()
def update_viewing_status(viewing_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    viewing = ViewingRequest.query.get_or_404(viewing_id)
    prop = Property.query.get(viewing.property_id)

    if prop.owner_id != user_id and claims.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json or {}
    valid_statuses = ['pending', 'confirmed', 'cancelled', 'completed']
    status = data.get('status')

    if status not in valid_statuses:
        return jsonify({'error': f'Status must be one of {valid_statuses}'}), 400

    viewing.status = status
    if data.get('confirmed_date'):
        from datetime import date
        viewing.confirmed_date = date.fromisoformat(data['confirmed_date'])
    if data.get('confirmed_time'):
        from datetime import time
        t = data['confirmed_time'].split(':')
        viewing.confirmed_time = time(int(t[0]), int(t[1]))

    db.session.commit()
    return jsonify({'viewing': viewing.to_dict()}), 200
