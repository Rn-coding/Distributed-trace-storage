"""Database Initialization Script.

Repeatable initialization for Phase 2:
- Applies JSON Schema validators to all 5 collections.
- Creates all required unique and query-supporting indexes.
- Seeds the initial development admin account with password hashing.
- Optionally resets data if --drop flag is supplied.
"""

import argparse
import sys
from werkzeug.security import generate_password_hash
from config import Config
from db.connection import get_database
from db.validation import SCHEMA_MAP
from db.indexes import create_all_indexes


def init_database(drop_existing=False):
    db = get_database()
    print(f"[*] Initializing MongoDB database: '{db.name}'")

    existing_collections = db.list_collection_names()

    if drop_existing:
        print("[!] Dropping existing collections for clean reset...")
        for col in SCHEMA_MAP.keys():
            if col in existing_collections:
                db[col].drop()
                print(f"    - Dropped collection '{col}'")
        existing_collections = db.list_collection_names()

    # 1. Setup collections with JSON Schema Validation
    print("[*] Setting up collections and JSON Schema validators...")
    for col_name, validator in SCHEMA_MAP.items():
        if col_name not in existing_collections:
            db.create_collection(col_name, validator=validator)
            print(f"    + Created collection '{col_name}' with schema validation")
        else:
            # Update validator on existing collection
            try:
                db.command({
                    "collMod": col_name,
                    "validator": validator,
                    "validationLevel": "moderate",
                })
                print(f"    ~ Updated validator on existing collection '{col_name}'")
            except Exception as e:
                print(f"    ! Warning updating validator on '{col_name}': {e}")

    # 2. Setup Indexes
    print("[*] Creating indexes...")
    index_results = create_all_indexes(db)
    for col_name, idx_names in index_results.items():
        print(f"    + Indexes for '{col_name}': {idx_names}")

    # 3. Seed Default Admin User
    print("[*] Ensuring development admin account exists...")
    admin_user = db.users.find_one({"username": Config.ADMIN_USERNAME})
    if not admin_user:
        hashed_pwd = generate_password_hash(Config.ADMIN_PASSWORD)
        db.users.insert_one({
            "username": Config.ADMIN_USERNAME,
            "password_hash": hashed_pwd,
            "role": "admin",
            "active": True,
        })
        print(f"    + Created default admin user: '{Config.ADMIN_USERNAME}'")
    else:
        print(f"    = Admin user '{Config.ADMIN_USERNAME}' already exists.")

    print("[SUCCESS] Database initialization completed successfully.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Jaeger-NoSQL MongoDB schema and indexes")
    parser.add_argument("--drop", action="store_true", help="Drop collections before initialization")
    args = parser.parse_args()

    try:
        init_database(drop_existing=args.drop)
    except Exception as exc:
        print(f"[FATAL] Initialization failed: {exc}", file=sys.stderr)
        sys.exit(1)
