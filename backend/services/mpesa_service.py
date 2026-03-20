import base64
import requests
from datetime import datetime
from flask import current_app


class MpesaService:
    SANDBOX_BASE = 'https://sandbox.safaricom.co.ke'
    PROD_BASE = 'https://api.safaricom.co.ke'

    def __init__(self):
        self.consumer_key = current_app.config['MPESA_CONSUMER_KEY']
        self.consumer_secret = current_app.config['MPESA_CONSUMER_SECRET']
        self.shortcode = current_app.config['MPESA_SHORTCODE']
        self.passkey = current_app.config['MPESA_PASSKEY']
        self.callback_url = current_app.config['MPESA_CALLBACK_URL']
        self.env = current_app.config.get('MPESA_ENVIRONMENT', 'sandbox')
        self.base_url = self.SANDBOX_BASE if self.env == 'sandbox' else self.PROD_BASE

    def get_access_token(self) -> str:
        credentials = base64.b64encode(
            f'{self.consumer_key}:{self.consumer_secret}'.encode()
        ).decode('utf-8')

        response = requests.get(
            f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials',
            headers={'Authorization': f'Basic {credentials}'}
        )
        response.raise_for_status()
        return response.json()['access_token']

    def generate_password(self) -> tuple:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data = f'{self.shortcode}{self.passkey}{timestamp}'
        password = base64.b64encode(data.encode()).decode('utf-8')
        return password, timestamp

    def format_phone(self, phone: str) -> str:
        """Format phone to 254XXXXXXXXX"""
        phone = phone.strip().replace(' ', '').replace('-', '')
        if phone.startswith('+254'):
            return phone[1:]
        if phone.startswith('0'):
            return f'254{phone[1:]}'
        if phone.startswith('254'):
            return phone
        return f'254{phone}'

    def stk_push(self, phone_number: str, amount: int,
                 account_reference: str, transaction_desc: str) -> dict:
        token = self.get_access_token()
        password, timestamp = self.generate_password()
        phone = self.format_phone(phone_number)

        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': amount,
            'PartyA': phone,
            'PartyB': self.shortcode,
            'PhoneNumber': phone,
            'CallBackURL': self.callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc,
        }

        response = requests.post(
            f'{self.base_url}/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            }
        )
        return response.json()

    def query_stk_status(self, checkout_request_id: str) -> dict:
        token = self.get_access_token()
        password, timestamp = self.generate_password()

        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id,
        }

        response = requests.post(
            f'{self.base_url}/mpesa/stkpushquery/v1/query',
            json=payload,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            }
        )
        return response.json()
