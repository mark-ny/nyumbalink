# notifications_bp is defined in routes/search.py
# Re-export for app.py import compatibility
from routes.search import notifications_bp

__all__ = ['notifications_bp']
