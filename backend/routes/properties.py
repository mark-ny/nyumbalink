from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields, validate, ValidationError
from models import db, Property, PropertyImage, User, SavedProperty
from services.cloudinary_service import upload_image, delete_image
from services.cache_service import get_cached, set_cached, invalidate_pattern
from services.elasticsearch_service import index_property, delete_property_index
import uuid, math

properties_bp = Blueprint('properties', __name__, url_prefix='/api/properties')

VALID_CATEGORIES = ['rent', 'short_stay', 'plot_sale']
ALLOWED_MIMETYPES = {'image/png', 'image/jpeg', 'image/jpg', 'image/webp'}
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


class PropertyCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=5, max=500))
    description = fields.Str(validate=validate.Length(max=5000))
    category = fields.Str(required=True, validate=validate.OneOf(VALID_CATEGORIES))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    price_period = fields.Str(validate=validate.OneOf(['monthly', 'per_night', 'total', 'yearly']))
    location = fields.Str(required=True)
    county = fields.Str()
    town = fields.Str()
    latitude = fields.Float(validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(validate=validate.Range(min=-180, max=180))
    bedrooms = fields.Int(validate=validate.Range(min=0, max=100))
    bathrooms = fields.Int(validate=validate.Range(min=0, max=100))
    plot_size = fields.Float(validate=validate.Range(min=0))
    plot_size_unit = fields.Str(validate=validate.OneOf(['sqm', 'acres', 'hectares']))
    floor_area = fields.Float(validate=validate.Range(min=0))
    amenities = fields.List(fields.Str())


def _allowed_file_upload(file) -> bool:
    if file.content_type and file.content_type.lower() in ALLOWED_MIMETYPES:
        return True
    if file.filename and '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        return ext in ALLOWED_EXTENSIONS
    return False


@properties_bp.route('', methods=['GET'])
def list_properties():
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 12)), 50)
    category = request.args.get('category')
    county = request.args.get('county')
    town = request.args.get('town')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    bedrooms = request.args.get('bedrooms', type=int)
    min_plot = request.args.get('min_plot', type=float)
    q = request.args.get('q', '').strip()
    featured_only = request.args.get('featured', 'false').lower() == 'true'

    cache_key = f"properties:{category}:{county}:{town}:{min_price}:{max_price}:{bedrooms}:{q}:{page}:{per_page}"
    cached = get_cached(cache_key)
    if cached and not q:
        return jsonify(cached), 200

    query = Property.query.filter_by(verification_status='verified', status='active')

    if category:
        query = query.filter_by(category=category)
    if county:
        query = query.filter(Property.county.ilike(f'%{county}%'))
    if town:
        query = query.filter(Property.town.ilike(f'%{town}%'))
    if min_price:
        query = query.filter(Property.price >= min_price)
    if max_price:
        query = query.filter(Property.price <= max_price)
    if bedrooms:
        query = query.filter(Property.bedrooms >= bedrooms)
    if min_plot:
        query = query.filter(Property.plot_size >= min_plot)
    if featured_only:
        query = query.filter_by(featured=True)
    if q:
        query = query.filter(
            db.or_(
                Property.title.ilike(f'%{q}%'),
                Property.description.ilike(f'%{q}%'),
                Property.location.ilike(f'%{q}%'),
                Property.town.ilike(f'%{q}%'),
                Property.county.ilike(f'%{q}%'),
            )
        )

    query = query.order_by(Property.featured.desc(), Property.created_at.desc())
    total = query.count()
    properties = query.offset((page - 1) * per_page).limit(per_page).all()

    result = {
        'properties': [p.to_dict(include_owner=True) for p in properties],
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': math.ceil(total / per_page) if total else 0,
        }
    }

    set_cached(cache_key, result, ttl=300)
    return jsonify(result), 200


@properties_bp.route('/<property_id>', methods=['GET'])
def get_property(property_id):
    cache_key = f"property:{property_id}"
    cached = get_cached(cache_key)
    if cached:
        return jsonify(cached), 200

    prop = Property.query.get_or_404(property_id)
    prop.views_count = (prop.views_count or 0) + 1
    db.session.commit()

    data = prop.to_dict(include_owner=True)
    set_cached(cache_key, data, ttl=300)
    return jsonify(data), 200


@properties_bp.route('', methods=['POST'])
@jwt_required()
def create_property():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user.role not in ['owner', 'admin', 'agent']:
        return jsonify({'error': 'Only property owners can create listings'}), 403

    schema = PropertyCreateSchema()
    try:
        data = schema.load(request.json or {})
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400

    prop = Property(id=str(uuid.uuid4()), owner_id=user_id, **data)
    db.session.add(prop)
    db.session.commit()

    try:
        index_property(prop)
    except Exception:
        pass

    invalidate_pattern('properties:*')
    return jsonify({'property': prop.to_dict(), 'message': 'Property created successfully'}), 201


@properties_bp.route('/<property_id>', methods=['PUT'])
@jwt_required()
def update_property(property_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    prop = Property.query.get_or_404(property_id)

    if prop.owner_id != user_id and claims.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    schema = PropertyCreateSchema(partial=True)
    try:
        data = schema.load(request.json or {})
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400

    for key, value in data.items():
        setattr(prop, key, value)

    if any(k in data for k in ['title', 'description', 'price', 'location']):
        if claims.get('role') != 'admin':
            prop.verification_status = 'pending'

    db.session.commit()

    try:
        index_property(prop)
    except Exception:
        pass

    invalidate_pattern(f'property:{property_id}')
    invalidate_pattern('properties:*')
    return jsonify({'property': prop.to_dict(), 'message': 'Property updated'}), 200


@properties_bp.route('/<property_id>', methods=['DELETE'])
@jwt_required()
def delete_property(property_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    prop = Property.query.get_or_404(property_id)

    if prop.owner_id != user_id and claims.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    for img in prop.images:
        if img.public_id:
            try:
                delete_image(img.public_id)
            except Exception:
                pass

    try:
        delete_property_index(property_id)
    except Exception:
        pass

    db.session.delete(prop)
    db.session.commit()

    invalidate_pattern(f'property:{property_id}')
    invalidate_pattern('properties:*')
    return jsonify({'message': 'Property deleted'}), 200


@properties_bp.route('/<property_id>/images', methods=['POST'])
@jwt_required()
def upload_property_images(property_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    prop = Property.query.get_or_404(property_id)

    if prop.owner_id != user_id and claims.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    files = request.files.getlist('images') or request.files.getlist('image')
    valid_files = [f for f in files if f and f.filename != '']

    if not valid_files:
        return jsonify({'error': 'No images provided'}), 400

    max_images = current_app.config.get('MAX_IMAGES_PER_PROPERTY', 20)
    existing_count = len(prop.images)

    if existing_count + len(valid_files) > max_images:
        return jsonify({'error': f'Maximum {max_images} images allowed'}), 400

    uploaded = []
    errors = []

    for i, file in enumerate(valid_files):
        if not _allowed_file_upload(file):
            errors.append(f'File {i+1}: unsupported format (use PNG, JPG, WEBP)')
            continue
        try:
            result = upload_image(file, folder=f'nyumbalink/properties/{property_id}')
            image_url = result.get('secure_url') or result.get('url', '')
            if not image_url:
                errors.append(f'File {i+1}: no URL returned from Cloudinary')
                continue

            image_url = image_url.replace('http://', 'https://')

            img = PropertyImage(
                id=str(uuid.uuid4()),
                property_id=property_id,
                image_url=image_url,
                public_id=result.get('public_id'),
                is_primary=(existing_count == 0 and len(uploaded) == 0),
                sort_order=existing_count + i,
            )
            db.session.add(img)
            uploaded.append(img)
        except Exception as e:
            current_app.logger.error(f'Image upload error file {i+1}: {e}')
            errors.append(f'File {i+1}: upload failed — {str(e)}')

    if uploaded:
        db.session.commit()
        invalidate_pattern(f'property:{property_id}')
        invalidate_pattern('properties:*')

    response = {
        'images': [img.to_dict() for img in uploaded],
        'message': f'{len(uploaded)} image(s) uploaded successfully',
    }
    if errors:
        response['errors'] = errors

    return jsonify(response), 201 if uploaded else 400


@properties_bp.route('/<property_id>/images/<image_id>', methods=['DELETE'])
@jwt_required()
def delete_property_image(property_id, image_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    prop = Property.query.get_or_404(property_id)

    if prop.owner_id != user_id and claims.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    img = PropertyImage.query.filter_by(id=image_id, property_id=property_id).first_or_404()
    was_primary = img.is_primary

    if img.public_id:
        try:
            delete_image(img.public_id)
        except Exception:
            pass

    db.session.delete(img)
    db.session.commit()

    if was_primary:
        next_img = PropertyImage.query.filter_by(property_id=property_id).order_by(
            PropertyImage.sort_order.asc()
        ).first()
        if next_img:
            next_img.is_primary = True
            db.session.commit()

    invalidate_pattern(f'property:{property_id}')
    invalidate_pattern('properties:*')
    return jsonify({'message': 'Image deleted'}), 200


@properties_bp.route('/my/listings', methods=['GET'])
@jwt_required()
def my_listings():
    user_id = get_jwt_identity()
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 12)), 50)

    query = Property.query.filter_by(owner_id=user_id).order_by(Property.created_at.desc())
    total = query.count()
    properties = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'properties': [p.to_dict() for p in properties],
        'pagination': {'total': total, 'page': page, 'per_page': per_page, 'pages': math.ceil(total / per_page)}
    }), 200


@properties_bp.route('/saved', methods=['GET'])
@jwt_required()
def get_saved():
    user_id = get_jwt_identity()
    saved = SavedProperty.query.filter_by(user_id=user_id).all()
    prop_ids = [s.property_id for s in saved]
    properties = Property.query.filter(Property.id.in_(prop_ids)).all()
    return jsonify({'properties': [p.to_dict() for p in properties]}), 200


@properties_bp.route('/<property_id>/save', methods=['POST'])
@jwt_required()
def save_property(property_id):
    user_id = get_jwt_identity()
    Property.query.get_or_404(property_id)
    existing = SavedProperty.query.filter_by(user_id=user_id, property_id=property_id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'saved': False, 'message': 'Property unsaved'}), 200

    sp = SavedProperty(id=str(uuid.uuid4()), user_id=user_id, property_id=property_id)
    db.session.add(sp)
    db.session.commit()
    return jsonify({'saved': True, 'message': 'Property saved'}), 201


@properties_bp.route('/<property_id>/images/urls', methods=['POST'])
@jwt_required()
def save_image_urls(property_id):
    """Save Cloudinary URLs directly — no re-upload needed"""
    user_id = get_jwt_identity()
    claims = get_jwt()
    prop = Property.query.get_or_404(property_id)

    if prop.owner_id != user_id and claims.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json or {}
    images_data = data.get('images', [])

    if not images_data:
        return jsonify({'error': 'No image URLs provided'}), 400

    saved = []
    for item in images_data:
        image_url = item.get('image_url', '').replace('http://', 'https://')
        if not image_url:
            continue
        img = PropertyImage(
            id=str(uuid.uuid4()),
            property_id=property_id,
            image_url=image_url,
            public_id=item.get('public_id'),
            is_primary=item.get('is_primary', False),
            sort_order=item.get('sort_order', 0),
        )
        db.session.add(img)
        saved.append(img)

    db.session.commit()
    invalidate_pattern(f'property:{property_id}')
    invalidate_pattern('properties:*')

    return jsonify({
        'images': [img.to_dict() for img in saved],
        'message': f'{len(saved)} image(s) saved'
    }), 201
