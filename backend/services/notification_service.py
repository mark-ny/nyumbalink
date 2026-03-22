from flask import current_app, render_template_string

try:
    from flask_mail import Mail, Message
    mail = Mail()
except Exception:
    mail = None

def send_welcome_email(email: str, name: str):
    try:
        if not mail:
            return
        msg = Message(
            subject='Welcome to NyumbaLink',
            recipients=[email],
            html=f'<h2>Welcome {name}!</h2><p>Your account has been created successfully.</p>'
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Welcome email failed: {e}')

def notify_owner_new_inquiry(prop, inquiry):
    try:
        if not mail:
            return
        owner = prop.owner
        if not owner or not owner.email:
            return
        msg = Message(
            subject=f'New Inquiry: {prop.title}',
            recipients=[owner.email],
            html=f'<h2>New Inquiry</h2><p>{inquiry.name} sent an inquiry about "{prop.title}"</p><p>{inquiry.message}</p>'
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Inquiry notification failed: {e}')

def notify_owner_viewing_request(prop, viewing):
    try:
        if not mail:
            return
        owner = prop.owner
        if not owner or not owner.email:
            return
        msg = Message(
            subject=f'Viewing Request: {prop.title}',
            recipients=[owner.email],
            html=f'<h2>Viewing Request</h2><p>Someone wants to view "{prop.title}" on {viewing.preferred_date}</p>'
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Viewing notification failed: {e}')

def send_whatsapp_notification(phone: str, message: str):
    try:
        from twilio.rest import Client
        from flask import current_app
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        from_number = current_app.config.get('TWILIO_WHATSAPP_FROM')
        if not all([account_sid, auth_token, from_number]):
            return
        client = Client(account_sid, auth_token)
        if not phone.startswith('+'):
            phone = f'+{phone}'
        client.messages.create(
            body=message,
            from_=f'whatsapp:{from_number}',
            to=f'whatsapp:{phone}',
        )
    except Exception as e:
        current_app.logger.error(f'WhatsApp failed: {e}')
