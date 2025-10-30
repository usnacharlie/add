"""
Migration script to create users table and migrate demo users
"""
import sys
import os
sys.path.insert(0, '/opt/test/ffan/member')

# Set DATABASE_URL to SQLite before importing
os.environ['DATABASE_URL'] = 'sqlite:///member_registry.db'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config.database import Base
from backend.models import User, Member
import hashlib

# Create engine and session for SQLite
engine = create_engine('sqlite:///member_registry.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def hash_pin(pin: str) -> str:
    """Hash a PIN using SHA256"""
    return hashlib.sha256(pin.encode()).hexdigest()


def create_users_table():
    """Create the users table"""
    print("Creating users table...")
    Base.metadata.create_all(bind=engine, tables=[User.__table__])
    print("✓ Users table created successfully")


def migrate_demo_users():
    """Migrate demo users to database"""
    print("\nMigrating demo users to database...")

    db = SessionLocal()

    try:
        # Demo users data
        demo_users = [
            {
                'email': 'admin@add.org.zm',
                'phone': '0977000001',
                'pin': '1234',
                'full_name': 'Admin User',
                'role': 'admin',
                'member_id': 1
            },
            {
                'email': 'charles@ontech.co.zm',
                'phone': '0977123400',
                'pin': '9852',
                'full_name': 'Charles Mwansa',
                'role': 'admin',
                'member_id': 11
            },
            {
                'email': 'john.banda@email.com',
                'phone': '0977123456',
                'pin': '5678',
                'full_name': 'John Banda',
                'role': 'member',
                'member_id': 2
            },
            {
                'email': 'mary.mwansa@email.com',
                'phone': '0966987654',
                'pin': '9999',
                'full_name': 'Mary Mwansa',
                'role': 'member',
                'member_id': 3
            }
        ]

        # Create users
        for user_data in demo_users:
            # Check if user already exists
            existing = db.query(User).filter(User.email == user_data['email']).first()

            if existing:
                print(f"  - User {user_data['email']} already exists, skipping...")
                continue

            # Verify member exists if member_id is provided
            if user_data['member_id']:
                member = db.query(Member).filter(Member.id == user_data['member_id']).first()
                if not member:
                    print(f"  ⚠ Warning: Member ID {user_data['member_id']} not found for {user_data['email']}, creating user without member link")
                    user_data['member_id'] = None

            # Create user
            user = User(
                email=user_data['email'],
                phone=user_data['phone'],
                pin_hash=hash_pin(user_data['pin']),
                full_name=user_data['full_name'],
                role=user_data['role'],
                member_id=user_data['member_id'],
                is_active=True
            )

            db.add(user)
            print(f"  ✓ Created user: {user_data['email']} ({user_data['role']})")

        db.commit()
        print("\n✓ Demo users migrated successfully")

        # Show summary
        print("\n" + "="*60)
        print("USER SUMMARY")
        print("="*60)

        users = db.query(User).all()
        for user in users:
            print(f"\nEmail: {user.email}")
            print(f"Phone: {user.phone}")
            print(f"Name: {user.full_name}")
            print(f"Role: {user.role}")
            print(f"Member ID: {user.member_id}")
            print(f"Active: {user.is_active}")

        print("\n" + "="*60)
        print(f"Total users: {len(users)}")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("USER MIGRATION SCRIPT")
    print("="*60)

    create_users_table()
    migrate_demo_users()

    print("\n✓ Migration complete!")
    print("\nYou can now use these credentials to login:")
    print("  - admin@add.org.zm / PIN: 1234")
    print("  - charles@ontech.co.zm / PIN: 9852")
    print("  - john.banda@email.com / PIN: 5678")
    print("  - mary.mwansa@email.com / PIN: 9999")
