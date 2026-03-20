import os
from datetime import timedelta


def _bool(key, default=False):
    return os.environ.get(key, str(default)).lower() in ('1', 'true', 'yes')


class Config:
    SECRET_KEY     = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    DEBUG          = False
    TESTING        = False

    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///nyumbalink_dev.db')
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI        = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5, 'pool_recycle': 300,
        'pool_pre_ping': True, 'connect_args': {'connect_timeout': 10},
    }

    JWT_SECRET_KEY            = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-me')
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)))
    JWT_ALGORITHM             = 'HS256'

    REDIS_URL             = os.environ.get('REDIS_URL')
    CACHE_TTL             = 300
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT     = os.environ.get('RATELIMIT_DEFAULT', '200 per day;50 per hour')

    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY    = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

    MPESA_CONSUMER_KEY    = os.environ.get('MPESA_CONSUMER_KEY')
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
    MPESA_SHORTCODE       = os.environ.get('MPESA_SHORTCODE')
    MPESA_PASSKEY         = os.environ.get('MPESA_PASSKEY')
    MPESA_CALLBACK_URL    = os.environ.get('MPESA_CALLBACK_URL')
    MPESA_ENVIRONMENT     = os.environ.get('MPESA_ENVIRONMENT', 'sandbox')

    MAIL_SERVER         = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT           = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS        = True
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@nyumbalink.co.ke')
    MAIL_SUPPRESS_SEND  = not bool(os.environ.get('MAIL_USERNAME'))

    TWILIO_ACCOUNT_SID   = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN    = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM')

    CORS_ORIGINS = [o.strip() for o in
                    os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')]

    MAX_CONTENT_LENGTH      = 20 * 1024 * 1024
    ALLOWED_EXTENSIONS      = {'png', 'jpg', 'jpeg', 'webp'}
    MAX_IMAGES_PER_PROPERTY = 20

    DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', 12))
    MAX_PAGE_SIZE     = int(os.environ.get('MAX_PAGE_SIZE', 50))
    LISTING_FEE_KES   = int(os.environ.get('LISTING_FEE_KES', 500))

    LOG_LEVEL        = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_DIR          = os.environ.get('LOG_DIR', '/tmp/logs')
    LOG_MAX_BYTES    = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    FLASK_ENV        = os.environ.get('FLASK_ENV', 'production')


class DevelopmentConfig(Config):
    DEBUG     = True
    FLASK_ENV = 'development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///nyumbalink_dev.db')


class ProductionConfig(Config):
    DEBUG                  = False
    FLASK_ENV              = 'production'
    SESSION_COOKIE_SECURE  = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING    = True
    DEBUG      = True
    FLASK_ENV  = 'testing'
    SQLALCHEMY_DATABASE_URI   = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=1)
    MAIL_SUPPRESS_SEND        = True
    RATELIMIT_ENABLED         = False
    RATELIMIT_STORAGE_URL     = 'memory://'


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'testing':     TestingConfig,
    'default':     DevelopmentConfig,
}
