"""
NyumbaLink Logging System
─────────────────────────
Structured JSON logging with:
  • Console (dev) or JSON file (prod) output
  • Rotating file handlers (access, error, audit)
  • Request context injection (request_id, user_id, ip)
  • Audit trail for sensitive operations
"""

import os
import json
import logging
import logging.handlers
import traceback
import uuid
from datetime import datetime, timezone
from functools import wraps
from flask import request, g, has_request_context


# ── JSON Formatter ────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    RESERVED = {'msg', 'args', 'exc_info', 'exc_text', 'stack_info',
                 'levelno', 'pathname', 'filename', 'module',
                 'created', 'msecs', 'relativeCreated', 'thread',
                 'threadName', 'processName', 'process'}

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level':     record.levelname,
            'logger':    record.name,
            'message':   record.getMessage(),
        }

        # Request context
        if has_request_context():
            payload.update({
                'request_id': getattr(g, 'request_id', None),
                'method':     request.method,
                'path':       request.path,
                'ip':         request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')[:120],
                'user_id':    getattr(g, 'current_user_id', None),
            })

        # Exception info
        if record.exc_info:
            payload['exception'] = {
                'type':       record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message':    str(record.exc_info[1]),
                'traceback':  traceback.format_exception(*record.exc_info),
            }

        # Extra fields from logger.info('...', extra={'key': val})
        for k, v in record.__dict__.items():
            if k not in self.RESERVED and not k.startswith('_'):
                payload[k] = v

        return json.dumps(payload, default=str)


# ── Pretty Formatter (dev) ────────────────────────────────────────────

class DevFormatter(logging.Formatter):
    COLORS = {
        'DEBUG':    '\033[36m',   # cyan
        'INFO':     '\033[32m',   # green
        'WARNING':  '\033[33m',   # yellow
        'ERROR':    '\033[31m',   # red
        'CRITICAL': '\033[35m',   # magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        ts    = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        rid   = f" [{getattr(g, 'request_id', '')[:8]}]" if has_request_context() else ''
        msg   = record.getMessage()
        base  = f"{color}{ts} {record.levelname:<8}{self.RESET}{rid} {record.name}: {msg}"
        if record.exc_info:
            base += '\n' + self.formatException(record.exc_info)
        return base


# ── Setup ─────────────────────────────────────────────────────────────

def setup_logging(app) -> None:
    """Attach handlers to the Flask app logger and root logger."""

    log_dir   = app.config.get('LOG_DIR', 'logs')
    log_level = app.config.get('LOG_LEVEL', 'INFO').upper()
    env       = app.config.get('FLASK_ENV', 'production')
    max_bytes = int(app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024))
    backup    = int(app.config.get('LOG_BACKUP_COUNT', 5))

    os.makedirs(log_dir, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))

    # Remove default handlers
    root.handlers.clear()

    if env == 'development':
        # Pretty console output for dev
        ch = logging.StreamHandler()
        ch.setFormatter(DevFormatter())
        root.addHandler(ch)

    else:
        # ── Structured JSON handlers for production ──

        # General application log
        app_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=max_bytes,
            backupCount=backup,
            encoding='utf-8',
        )
        app_handler.setFormatter(JSONFormatter())
        root.addHandler(app_handler)

        # Error-only log
        err_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'error.log'),
            maxBytes=max_bytes,
            backupCount=backup,
            encoding='utf-8',
        )
        err_handler.setLevel(logging.ERROR)
        err_handler.setFormatter(JSONFormatter())
        root.addHandler(err_handler)

        # Audit log (immutable operations: payments, auth, admin)
        audit_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'audit.log'),
            maxBytes=max_bytes,
            backupCount=backup,
            encoding='utf-8',
        )
        audit_handler.setFormatter(JSONFormatter())
        audit_logger = logging.getLogger('nyumbalink.audit')
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False

        # Also mirror to stdout so Docker captures logs
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(JSONFormatter())
        stdout_handler.setLevel(logging.WARNING)
        root.addHandler(stdout_handler)

    # Silence noisy third-party loggers
    for noisy in ('urllib3', 'botocore', 'elasticsearch', 'werkzeug'):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    app.logger.info('Logging initialised', extra={'env': env, 'level': log_level})


# ── Request ID Middleware ─────────────────────────────────────────────

def init_request_logging(app) -> None:
    """Inject a unique request_id per request and log every request."""

    @app.before_request
    def _before():
        g.request_id      = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        g.request_start   = datetime.utcnow()

    @app.after_request
    def _after(response):
        duration_ms = (
            (datetime.utcnow() - g.request_start).total_seconds() * 1000
            if hasattr(g, 'request_start') else -1
        )
        # Skip health check noise
        if request.path != '/api/health':
            app.logger.info(
                'HTTP %s %s → %s',
                request.method,
                request.path,
                response.status_code,
                extra={
                    'duration_ms': round(duration_ms, 2),
                    'status_code': response.status_code,
                    'content_length': response.content_length,
                },
            )
        response.headers['X-Request-ID'] = g.get('request_id', '')
        return response

    @app.teardown_request
    def _teardown(exc):
        if exc:
            app.logger.error('Unhandled exception in request', exc_info=exc)


# ── Audit Logger ──────────────────────────────────────────────────────

audit_log = logging.getLogger('nyumbalink.audit')


def audit(event: str, **kwargs) -> None:
    """
    Write a structured audit event.

    Usage:
        audit('property.verified', property_id=prop.id, admin_id=user_id)
        audit('payment.completed', payment_id=pay.id, amount=500)
    """
    audit_log.info(
        event,
        extra={
            'event':     event,
            'user_id':   getattr(g, 'current_user_id', None) if has_request_context() else None,
            'ip':        request.remote_addr if has_request_context() else None,
            **kwargs,
        },
    )


# ── Decorator: log function calls ─────────────────────────────────────

def log_call(logger_name: str = 'nyumbalink'):
    """Decorator that logs entry/exit and exceptions of a function."""
    def decorator(fn):
        logger = logging.getLogger(logger_name)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            logger.debug('→ %s called', fn.__qualname__)
            try:
                result = fn(*args, **kwargs)
                logger.debug('← %s returned', fn.__qualname__)
                return result
            except Exception as exc:
                logger.exception('✗ %s raised %s', fn.__qualname__, type(exc).__name__)
                raise
        return wrapper
    return decorator
