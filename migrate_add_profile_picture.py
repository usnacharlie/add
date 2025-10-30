#!/usr/bin/env python3
"""
Migration script to add profile_picture column to members table
"""
import sys
import os

sys.path.insert(0, '/opt/test/ffan/member')
os.environ['DATABASE_URL'] = 'sqlite:///member_registry.db'

from sqlalchemy import create_engine, text
from backend.config.database import Base
from backend.models import Member

# Create engine
engine = create_engine('sqlite:///member_registry.db', echo=True)


def add_profile_picture_column():
    """Add profile_picture column to members table"""
    print("\n" + "="*60)
    print("Adding profile_picture column to members table")
    print("="*60 + "\n")

    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(members)"))
            columns = [row[1] for row in result.fetchall()]

            if 'profile_picture' in columns:
                print("✅ profile_picture column already exists")
                return True

            # Add the column
            conn.execute(text(
                "ALTER TABLE members ADD COLUMN profile_picture VARCHAR(500)"
            ))
            conn.commit()

            print("✅ Successfully added profile_picture column")
            return True

    except Exception as e:
        print(f"❌ Error adding column: {e}")
        return False


def verify_column():
    """Verify the column was added"""
    print("\n" + "="*60)
    print("Verifying profile_picture column")
    print("="*60 + "\n")

    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(members)"))
            columns = {row[1]: row[2] for row in result.fetchall()}

            if 'profile_picture' in columns:
                print(f"✅ Column verified: profile_picture ({columns['profile_picture']})")
                return True
            else:
                print("❌ Column not found")
                return False

    except Exception as e:
        print(f"❌ Error verifying column: {e}")
        return False


def main():
    """Main migration function"""
    print("\n" + "="*60)
    print("Profile Picture Column Migration")
    print("="*60 + "\n")

    # Add column
    if not add_profile_picture_column():
        print("\n❌ Migration failed")
        return False

    # Verify column
    if not verify_column():
        print("\n❌ Migration verification failed")
        return False

    print("\n" + "="*60)
    print("✅ Migration Completed Successfully!")
    print("="*60 + "\n")
    print("The profile_picture column has been added to the members table.")
    print("Members can now upload profile pictures from their edit profile page.\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
