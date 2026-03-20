from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Payment, Property
from services.mpesa_service import MpesaService
import uuid

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


@payments_bp.route('/initiate', methods=['POST'])
@jwt_required()
def initiate_payment():
    """Initiate M-Pesa STK Push for listing fee"""
    user_id = get_jwt_identity()
    data = request.json or {}

    phone = data.get('phone')
    property_id = data.get('property_id')
    amount = data.get('amount', current_app.config['LISTING_FEE_KES'])

    if not phone:
        return jsonify({'error': 'Phone number required'}), 400

    prop = Property.query.get(property_id) if property_id else None

    # Create pending payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        user_id=user_id,
        property_id=property_id,
        amount=amount,
        payment_method='mpesa',
        phone_number=phone,
        status='pending',
        description=f'Listing fee for {prop.title if prop else "property"}',
    )
    db.session.add(payment)
    db.session.commit()

    # Initiate STK Push
    try:
        mpesa = MpesaService()
        result = mpesa.stk_push(
            phone_number=phone,
            amount=int(amount),
            account_reference=payment.id[:10].upper(),
            transaction_desc=f'NyumbaLink listing fee',
        )

        if result.get('ResponseCode') == '0':
            payment.transaction_code = result.get('CheckoutRequestID')
            db.session.commit()
            return jsonify({
                'message': 'STK Push sent. Enter your M-Pesa PIN to complete payment.',
                'payment_id': payment.id,
                'checkout_request_id': result.get('CheckoutRequestID'),
            }), 200
        else:
            payment.status = 'failed'
            db.session.commit()
            return jsonify({'error': 'Failed to initiate payment', 'details': result}), 400

    except Exception as e:
        payment.status = 'failed'
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    """M-Pesa callback endpoint"""
    data = request.json or {}

    try:
        body = data.get('Body', {})
        callback = body.get('stkCallback', {})
        result_code = callback.get('ResultCode')
        checkout_request_id = callback.get('CheckoutRequestID')

        payment = Payment.query.filter_by(transaction_code=checkout_request_id).first()
        if not payment:
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'}), 200

        if result_code == 0:
            # Payment successful
            items = callback.get('CallbackMetadata', {}).get('Item', [])
            metadata = {item['Name']: item.get('Value') for item in items}

            payment.status = 'completed'
            payment.mpesa_receipt = metadata.get('MpesaReceiptNumber')
            payment.extra_data = metadata

            # Activate listing if this is a listing fee
            if payment.property_id:
                prop = Property.query.get(payment.property_id)
                if prop:
                    prop.verification_status = 'pending'  # Submit for admin review
        else:
            payment.status = 'failed'

        db.session.commit()

    except Exception as e:
        current_app.logger.error(f'M-Pesa callback error: {e}')

    return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'}), 200


@payments_bp.route('/status/<payment_id>', methods=['GET'])
@jwt_required()
def payment_status(payment_id):
    user_id = get_jwt_identity()
    payment = Payment.query.filter_by(id=payment_id, user_id=user_id).first_or_404()
    return jsonify({'payment': payment.to_dict()}), 200


@payments_bp.route('/query/<checkout_request_id>', methods=['GET'])
@jwt_required()
def query_payment(checkout_request_id):
    """Query M-Pesa payment status"""
    try:
        mpesa = MpesaService()
        result = mpesa.query_stk_status(checkout_request_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/my', methods=['GET'])
@jwt_required()
def my_payments():
    user_id = get_jwt_identity()
    payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()
    return jsonify({'payments': [p.to_dict() for p in payments]}), 200
