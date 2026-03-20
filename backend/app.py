import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

from config import config
from models import db
from services.notification_service import mail
from utils.logger import setup_logging, init_request_logging


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
        if config_name not in config:
            config_name = 'production'

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    mail.init_app(app)
    JWTManager(app)
    Migrate(app, db)

    CORS(app,
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

    Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=['200 per day', '50 per hour'],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://'),
        enabled=not app.config.get('TESTING', False),
    )

    setup_logging(app)
    init_request_logging(app)

    from routes.auth         import auth_bp
    from routes.properties   import properties_bp
    from routes.interactions import inquiries_bp, viewings_bp
    from routes.admin        import admin_bp
    from routes.payments     import payments_bp
    from routes.search       import search_bp, notifications_bp
    from routes.seo          import seo_bp
    from routes.swagger      import swagger_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(inquiries_bp)
    app.register_blueprint(viewings_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(seo_bp)
    app.register_blueprint(swagger_bp)

    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'NyumbaLink API', 'env': config_name}), 200

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': str(e.description)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Authentication required'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Access forbidden'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({'error': 'Unprocessable entity'}), 422

    @app.errorhandler(429)
    def rate_limit(e):
        return jsonify({'error': 'Too many requests. Please slow down.'}), 429

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error('Internal server error', exc_info=e)
        return jsonify({'error': 'Internal server error'}), 500

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
