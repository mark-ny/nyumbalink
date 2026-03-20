#!/usr/bin/env python3
"""
NyumbaLink — Pre-Deploy Checklist
───────────────────────────────────
Run this locally before your first deploy to catch missing config.

Usage:
    cd nyumbalink/backend
    pip install psycopg2-binary redis requests python-dotenv
    python scripts/predeploy_check.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import os
import sys
import socket
from dotenv import load_dotenv

load_dotenv()

PASS  = "  ✅"
FAIL  = "  ❌"
WARN  = "  ⚠️ "
INFO  = "  ℹ️ "

errors   = []
warnings = []


def check(label: str, ok: bool, detail: str = "", warn_only: bool = False):
    if ok:
        print(f"{PASS} {label}" + (f" — {detail}" if detail else ""))
    else:
        sym = WARN if warn_only else FAIL
        msg = f"{sym} {label}" + (f" — {detail}" if detail else "")
        print(msg)
        if warn_only:
            warnings.append(label)
        else:
            errors.append(label)


def section(title: str):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


# ── Required env vars ─────────────────────────────────────────────────

section("Environment Variables")

REQUIRED = [
    ("SECRET_KEY",            "Flask secret key"),
    ("JWT_SECRET_KEY",        "JWT signing secret"),
    ("DATABASE_URL",          "Supabase PostgreSQL URL"),
    ("CLOUDINARY_CLOUD_NAME", "Cloudinary cloud name"),
    ("CLOUDINARY_API_KEY",    "Cloudinary API key"),
    ("CLOUDINARY_API_SECRET", "Cloudinary API secret"),
]

OPTIONAL = [
    ("REDIS_URL",             "Upstash Redis URL (caching)"),
    ("MPESA_CONSUMER_KEY",    "M-Pesa Daraja key"),
    ("MPESA_CONSUMER_SECRET", "M-Pesa Daraja secret"),
    ("MPESA_CALLBACK_URL",    "M-Pesa callback URL"),
    ("MAIL_USERNAME",         "Gmail SMTP username"),
    ("MAIL_PASSWORD",         "Gmail app password"),
    ("TWILIO_ACCOUNT_SID",    "Twilio WhatsApp SID"),
    ("CORS_ORIGINS",          "Allowed CORS origins"),
]

for key, label in REQUIRED:
    val = os.environ.get(key, "")
    check(f"{key}", bool(val), label if not val else f"{val[:8]}…")

for key, label in OPTIONAL:
    val = os.environ.get(key, "")
    check(f"{key}", bool(val), label if not val else "set", warn_only=True)


# ── Secret strength ───────────────────────────────────────────────────

section("Secret Key Strength")

for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
    val = os.environ.get(key, "")
    check(f"{key} length >= 32 chars", len(val) >= 32,
          f"currently {len(val)} chars")
    check(f"{key} not a default/placeholder",
          val not in ("CHANGE_ME_32_CHAR_RANDOM_STRING",
                      "your-very-secret-key-change-in-production", ""),
          warn_only=False)


# ── Database ──────────────────────────────────────────────────────────

section("Database (Supabase)")

db_url = os.environ.get("DATABASE_URL", "")
check("DATABASE_URL is set", bool(db_url))
check("Uses postgresql:// scheme",
      db_url.startswith("postgresql://") or db_url.startswith("postgres://"),
      db_url[:30] if db_url else "not set")
check("Uses Supabase pooler port 6543",
      ":6543/" in db_url,
      "Use Transaction Pooler (port 6543) for Render",
      warn_only=True)
check("Has sslmode=require",
      "sslmode=require" in db_url,
      "Add ?sslmode=require to DATABASE_URL",
      warn_only=True)

try:
    import psycopg2
    url = db_url.replace("postgresql://", "").replace("postgres://", "")
    conn = psycopg2.connect(db_url, connect_timeout=8)
    conn.close()
    check("Database connection", True, "connected successfully")
except Exception as e:
    check("Database connection", False, str(e))


# ── Redis ─────────────────────────────────────────────────────────────

section("Redis Cache (Upstash)")

redis_url = os.environ.get("REDIS_URL", "")
if redis_url:
    check("REDIS_URL starts with rediss:// (TLS)",
          redis_url.startswith("rediss://"),
          "Upstash requires TLS (rediss://)")
    try:
        import redis as redis_lib
        r = redis_lib.from_url(redis_url, socket_connect_timeout=5, decode_responses=True)
        r.ping()
        check("Redis connection", True, "PONG received")
    except Exception as e:
        check("Redis connection", False, str(e))
else:
    print(f"{WARN} REDIS_URL not set — caching disabled (acceptable for launch)")


# ── Cloudinary ────────────────────────────────────────────────────────

section("Cloudinary (Image Storage)")

cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
api_key    = os.environ.get("CLOUDINARY_API_KEY", "")
api_secret = os.environ.get("CLOUDINARY_API_SECRET", "")

check("CLOUDINARY_CLOUD_NAME set", bool(cloud_name))
check("CLOUDINARY_API_KEY set", bool(api_key))
check("CLOUDINARY_API_SECRET set", bool(api_secret))

if all([cloud_name, api_key, api_secret]):
    try:
        import cloudinary
        import cloudinary.api
        cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)
        result = cloudinary.api.ping()
        check("Cloudinary API ping", result.get("status") == "ok", result.get("status"))
    except Exception as e:
        check("Cloudinary API ping", False, str(e))


# ── M-Pesa ────────────────────────────────────────────────────────────

section("M-Pesa Daraja")

mpesa_env = os.environ.get("MPESA_ENVIRONMENT", "sandbox")
check("MPESA_ENVIRONMENT set", bool(mpesa_env), mpesa_env)
check("MPESA_CONSUMER_KEY set", bool(os.environ.get("MPESA_CONSUMER_KEY")), warn_only=True)
check("MPESA_CONSUMER_SECRET set", bool(os.environ.get("MPESA_CONSUMER_SECRET")), warn_only=True)
check("MPESA_CALLBACK_URL set", bool(os.environ.get("MPESA_CALLBACK_URL")), warn_only=True)

callback = os.environ.get("MPESA_CALLBACK_URL", "")
if callback:
    check("Callback URL is HTTPS", callback.startswith("https://"),
          "Safaricom requires HTTPS callback")
    check("Callback URL is public (not localhost)",
          "localhost" not in callback and "127.0.0.1" not in callback)


# ── Email ─────────────────────────────────────────────────────────────

section("Email (Gmail SMTP)")

mail_user = os.environ.get("MAIL_USERNAME", "")
mail_pass = os.environ.get("MAIL_PASSWORD", "")
check("MAIL_USERNAME set", bool(mail_user), warn_only=True)
check("MAIL_PASSWORD set", bool(mail_pass), warn_only=True)

if mail_user and mail_pass:
    try:
        import smtplib
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=8) as s:
            s.starttls()
            s.login(mail_user, mail_pass)
        check("Gmail SMTP login", True, "credentials valid")
    except Exception as e:
        check("Gmail SMTP login", False, str(e))


# ── CORS ──────────────────────────────────────────────────────────────

section("CORS Configuration")

cors = os.environ.get("CORS_ORIGINS", "")
check("CORS_ORIGINS set", bool(cors), warn_only=True)
if cors:
    origins = cors.split(",")
    check("CORS has at least one origin", len(origins) >= 1, cors[:60])
    check("No wildcard * in production CORS",
          "*" not in cors,
          "Wildcard CORS is insecure in production")
    for origin in origins:
        origin = origin.strip()
        if origin:
            check(f"Origin uses HTTPS: {origin}",
                  origin.startswith("https://") or "localhost" in origin)


# ── Network reachability ──────────────────────────────────────────────

section("Network Checks")

hosts = [
    ("Cloudinary CDN", "res.cloudinary.com", 443),
    ("Supabase",       "aws.supabase.co",    443),
    ("Safaricom API",  "api.safaricom.co.ke", 443),
    ("Gmail SMTP",     "smtp.gmail.com",      587),
]

for label, host, port in hosts:
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        check(f"Reach {label} ({host}:{port})", True)
    except Exception as e:
        check(f"Reach {label} ({host}:{port})", False, str(e), warn_only=True)


# ── Final report ──────────────────────────────────────────────────────

print(f"\n{'═'*50}")
print(f"  RESULTS")
print(f"{'═'*50}")

if errors:
    print(f"\n{FAIL} {len(errors)} blocking error(s):")
    for e in errors:
        print(f"     • {e}")
    print(f"\n  Fix these before deploying.\n")
    sys.exit(1)
elif warnings:
    print(f"\n{WARN} {len(warnings)} optional item(s) not configured:")
    for w in warnings:
        print(f"     • {w}")
    print(f"\n{PASS} No blocking errors. Ready to deploy!\n")
    sys.exit(0)
else:
    print(f"\n{PASS} All checks passed. Ready to deploy! 🚀\n")
    sys.exit(0)
