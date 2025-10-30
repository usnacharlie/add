#!/usr/bin/env python3
"""
Migration script to create ussd_sessions table
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/opt/test/ffan/member')

# Set database URL to SQLite
os.environ['DATABASE_URL'] = 'sqlite:///member_registry.db'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config.database import Base
from backend.models import USSDSession

# Create engine and session for SQLite
engine = create_engine('sqlite:///member_registry.db', echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_ussd_sessions_table():
    """Create the ussd_sessions table"""
    print("\n" + "="*60)
    print("Creating ussd_sessions table...")
    print("="*60 + "\n")

    try:
        # Create only the ussd_sessions table
        Base.metadata.create_all(bind=engine, tables=[USSDSession.__table__])
        print("\n✅ Successfully created ussd_sessions table!")
        return True
    except Exception as e:
        print(f"\n❌ Error creating table: {e}")
        return False


def verify_table():
    """Verify the table was created"""
    print("\n" + "="*60)
    print("Verifying ussd_sessions table...")
    print("="*60 + "\n")

    try:
        db = SessionLocal()

        # Check if we can query the table
        count = db.query(USSDSession).count()
        print(f"✅ Table verified! Current session count: {count}")

        db.close()
        return True
    except Exception as e:
        print(f"❌ Error verifying table: {e}")
        return False


def main():
    """Main migration function"""
    print("\n" + "="*60)
    print("USSD Sessions Table Migration Script")
    print("="*60 + "\n")

    # Step 1: Create the table
    if not create_ussd_sessions_table():
        print("\n❌ Migration failed at table creation step")
        return False

    # Step 2: Verify the table
    if not verify_table():
        print("\n❌ Migration failed at verification step")
        return False

    print("\n" + "="*60)
    print("✅ USSD Sessions Migration Completed Successfully!")
    print("="*60 + "\n")
    print("The ussd_sessions table is ready for use.")
    print("\nTable structure:")
    print("  - id (PRIMARY KEY)")
    print("  - session_id (UNIQUE, NOT NULL)")
    print("  - phone_number (NOT NULL)")
    print("  - current_step (NOT NULL)")
    print("  - session_data (JSON)")
    print("  - is_active (BOOLEAN)")
    print("  - created_at (DATETIME)")
    print("  - updated_at (DATETIME)")
    print("\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
