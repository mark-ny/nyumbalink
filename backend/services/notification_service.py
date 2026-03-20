from flask import current_app, render_template_string
from flask_mail import Mail, Message

mail = Mail()

INQUIRY_EMAIL = """
<h2>New Inquiry - NyumbaLink</h2>
<p>You have a new inquiry for your property: <strong>{{ prop_title }}</strong></p>
<table>
  <tr><td><strong>Name:</strong></td><td>{{ name }}</td></tr>
  <tr><td><strong>Email:</strong></td><td>{{ email }}</td></tr>
  <tr><td><strong>Phone:</strong></td><td>{{ phone }}</td></tr>
  <tr><td><strong>Message:</strong></td><td>{{ message }}</td></tr>
</table>
<p>Log in to your <a href="{{ dashboard_url }}">NyumbaLink Dashboard</a> to respond.</p>
"""

VIEWING_EMAIL = """
<h2>Viewing Request - NyumbaLink</h2>
<p>You have a new viewing request for: <strong>{{ prop_title }}</strong></p>
<table>
  <tr><td><strong>From:</strong></td><td>{{ name }}</td></tr>
  <tr><td><strong>Phone:</strong></td><td>{{ phone }}</td></tr>
  <tr><td><strong>Preferred Date:</strong></td><td>{{ preferred_date }}</td></tr>
  <tr><td><strong>Preferred Time:</strong></td><td>{{ preferred_time }}</td></tr>
</table>
<p>Log in to <a href="{{ dashboard_url }}">confirm or decline the viewing</a>.</p>
"""

WELCOME_EMAIL = """
<h2>Welcome to NyumbaLink!</h2>
<p>Hi {{ name }},</p>
<p>Your account has been created successfully. Start browsing thousands of properties across Kenya.</p>
<p><a href="https://nyumbalink.co.ke">Visit NyumbaLink</a></p>
"""


def send_welcome_email(email: str, name: str):
    try:
        msg = Message(
            subject='Welcome to NyumbaLink',
            recipients=[email],
            html=render_template_string(WELCOME_EMAIL, name=name),
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Failed to send welcome email: {e}')


def notify_owner_new_inquiry(prop, inquiry):
    try:
        owner = prop.owner
        if not owner or not owner.email:
            return

        msg = Message(
            subject=f'New Inquiry: {prop.title}',
            recipients=[owner.email],
            html=render_template_string(
                INQUIRY_EMAIL,
                prop_title=prop.title,
                name=inquiry.name,
                email=inquiry.email or 'N/A',
                phone=inquiry.phone or 'N/A',
                message=inquiry.message,
                dashboard_url='https://nyumbalink.co.ke/dashboard',
            )
        )
        mail.send(msg)

        # WhatsApp if configured
        if owner.phone:
            send_whatsapp_notification(
                owner.phone,
                f'New inquiry on NyumbaLink for "{prop.title}" from {inquiry.name}. Log in to respond.'
            )
    except Exception as e:
        current_app.logger.error(f'Failed to notify owner of inquiry: {e}')


def notify_owner_viewing_request(prop, viewing):
    try:
        owner = prop.owner
        if not owner or not owner.email:
            return

        msg = Message(
            subject=f'Viewing Request: {prop.title}',
            recipients=[owner.email],
            html=render_template_string(
                VIEWING_EMAIL,
                prop_title=prop.title,
                name=viewing.name or 'N/A',
                phone=viewing.phone or 'N/A',
                preferred_date=str(viewing.preferred_date),
                preferred_time=str(viewing.preferred_time) if viewing.preferred_time else 'Not specified',
                dashboard_url='https://nyumbalink.co.ke/dashboard',
            )
        )
        mail.send(msg)

        if owner.phone:
            send_whatsapp_notification(
                owner.phone,
                f'Viewing request on NyumbaLink for "{prop.title}" on {viewing.preferred_date}. Log in to confirm.'
            )
    except Exception as e:
        current_app.logger.error(f'Failed to notify owner of viewing: {e}')


def send_whatsapp_notification(phone: str, message: str):
    try:
        from twilio.rest import Client
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        from_number = current_app.config.get('TWILIO_WHATSAPP_FROM')

        if not all([account_sid, auth_token, from_number]):
            return

        client = Client(account_sid, auth_token)
        # Format phone for WhatsApp
        if not phone.startswith('+'):
            phone = f'+{phone}'

        client.messages.create(
            body=message,
            from_=f'whatsapp:{from_number}',
            to=f'whatsapp:{phone}',
        )
    except Exception as e:
        current_app.logger.error(f'WhatsApp notification failed: {e}')
