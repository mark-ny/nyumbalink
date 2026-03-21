import random
import string
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User
from services.notification_service import mail
from flask_mail import Message

verification_bp = Blueprint('verification', __name__, url_prefix='/api/verification')

# Store codes in memory (simple approach)
# In production use Redis
verification_codes = {}

def generate_code():
    return ''.join(random.choices(string.digits, k=6))

@verification_bp.route('/send', methods=['POST'])
@jwt_required()
def send_code():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if user.email_verified:
        return jsonify({'message': 'Email already verified'}), 200

    code = generate_code()
    expires = datetime.utcnow() + timedelta(minutes=10)
    verification_codes[user.email] = {'code': code, 'expires': expires}

    try:
        msg = Message(
            subject='NyumbaLink - Email Verification Code',
            recipients=[user.email],
            html=f'''
            <div style="font-family:sans-serif;max-width:400px;margin:0 auto;padding:20px">
              <h2 style="color:#16a34a">NyumbaLink</h2>
              <p>Your email verification code is:</p>
              <div style="background:#f3f4f6;border-radius:12px;padding:24px;text-align:center;margin:20px 0">
                <span style="font-size:36px;font-weight:800;letter-spacing:8px;color:#16a34a">{code}</span>
              </div>
              <p style="color:#6b7280;font-size:13px">This code expires in 10 minutes.</p>
            </div>
            '''
        )
        mail.send(msg)
        return jsonify({'message': f'Verification code sent to {user.email}'}), 200
    except Exception as e:
        # For testing — return code if email fails
        return jsonify({'message': 'Code generated', 'dev_code': code}), 200

@verification_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_code():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.json or {}
    code = data.get('code', '').strip()

    if not code:
        return jsonify({'error': 'Code is required'}), 400

    stored = verification_codes.get(user.email)
    if not stored:
        return jsonify({'error': 'No verification code found. Please request a new one.'}), 400

    if datetime.utcnow() > stored['expires']:
        del verification_codes[user.email]
        return jsonify({'error': 'Code has expired. Please request a new one.'}), 400

    if stored['code'] != code:
        return jsonify({'error': 'Invalid code. Please try again.'}), 400

    user.email_verified = True
    db.session.commit()
    del verification_codes[user.email]

    return jsonify({'message': 'Email verified successfully!'}), 200
