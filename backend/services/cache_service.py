import json
import redis
from flask import current_app

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(current_app.config['REDIS_URL'], decode_responses=True)
    return _redis_client


def get_cached(key: str):
    try:
        r = get_redis()
        value = r.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        return None


def set_cached(key: str, value, ttl: int = 300):
    try:
        r = get_redis()
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def delete_cached(key: str):
    try:
        r = get_redis()
        r.delete(key)
    except Exception:
        pass


def invalidate_pattern(pattern: str):
    try:
        r = get_redis()
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception:
        pass
