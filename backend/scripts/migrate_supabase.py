#!/usr/bin/env python3
"""
NyumbaLink — Supabase Schema Migrator
──────────────────────────────────────
Applies database/schema.sql to your Supabase PostgreSQL instance.

Usage:
    python scripts/migrate_supabase.py

Requirements:
    pip install psycopg2-binary python-dotenv
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
SCHEMA_FILE  = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")


def run():
    if not DATABASE_URL:
        print("❌  DATABASE_URL not set. Check your .env file.")
        sys.exit(1)

    print(f"🔌  Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        print(f"📄  Reading schema from {SCHEMA_FILE} ...")
        with open(SCHEMA_FILE, "r") as f:
            sql = f.read()

        print("🚀  Applying schema...")
        cur.execute(sql)

        print("✅  Schema applied successfully!")
        print()
        print("Next steps:")
        print("  1. Update the admin user password:")
        print("     UPDATE users SET password_hash = crypt('yourpassword', gen_salt('bf'))")
        print("     WHERE email = 'admin@nyumbalink.co.ke';")
        print()
        print("  2. Verify tables were created:")
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]
        for t in tables:
            print(f"     ✓ {t}")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"❌  Database error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌  Schema file not found: {SCHEMA_FILE}")
        sys.exit(1)


if __name__ == "__main__":
    run()
