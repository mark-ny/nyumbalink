#!/usr/bin/env python3
"""
NyumbaLink — Database Seeder
─────────────────────────────
Creates the initial admin user in Supabase.
Run ONCE after migrate_supabase.py.

Usage:
    python scripts/seed.py --email admin@nyumbalink.co.ke --password YourSecurePass
"""

import os
import sys
import uuid
import argparse
import bcrypt
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed(email: str, password: str, name: str = "NyumbaLink Admin"):
    if not DATABASE_URL:
        print("❌  DATABASE_URL not set.")
        sys.exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()

    # Check if admin already exists
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        print(f"ℹ️   User {email} already exists. Skipping.")
        cur.close()
        conn.close()
        return

    pw_hash = hash_password(password)
    user_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO users (id, name, email, password_hash, role, is_active, email_verified, phone)
        VALUES (%s, %s, %s, %s, 'admin', TRUE, TRUE, NULL)
    """, (user_id, name, email, pw_hash))

    conn.commit()
    print(f"✅  Admin user created!")
    print(f"    ID:    {user_id}")
    print(f"    Email: {email}")
    print(f"    Role:  admin")

    cur.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed NyumbaLink admin user")
    parser.add_argument("--email",    default="admin@nyumbalink.co.ke")
    parser.add_argument("--password", required=True)
    parser.add_argument("--name",     default="NyumbaLink Admin")
    args = parser.parse_args()

    seed(args.email, args.password, args.name)
