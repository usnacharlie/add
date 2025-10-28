"""
Seed sample members for testing
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.config.database import SessionLocal
from backend.models import Member, Ward

def seed_members():
    """Add sample members to the database"""
    db = SessionLocal()

    try:
        # Check if members already exist
        existing_members = db.query(Member).count()
        if existing_members > 0:
            print(f"Database already contains {existing_members} members. Skipping seed.")
            return

        # Get a ward to assign members to
        ward = db.query(Ward).first()
        if not ward:
            print("No wards found! Please run seed_data.py first.")
            return

        # Sample members
        members_data = [
            {
                "name": "John Mwanza",
                "contact": "+260971234567",
                "date_of_birth": "1985-03-15",
                "gender": "Male",
                "nrc": "123456/78/1"
            },
            {
                "name": "Mary Phiri",
                "contact": "+260972345678",
                "date_of_birth": "1990-07-22",
                "gender": "Female",
                "nrc": "234567/89/1"
            },
            {
                "name": "Peter Banda",
                "contact": "+260973456789",
                "date_of_birth": "1978-11-30",
                "gender": "Male",
                "nrc": "345678/90/1"
            },
            {
                "name": "Sarah Zulu",
                "contact": "+260974567890",
                "date_of_birth": "1995-05-18",
                "gender": "Female",
                "nrc": "456789/01/1"
            },
            {
                "name": "James Tembo",
                "contact": "+260975678901",
                "date_of_birth": "1982-09-10",
                "gender": "Male",
                "nrc": "567890/12/1"
            },
            {
                "name": "Grace Mulenga",
                "contact": "+260976789012",
                "date_of_birth": "1988-12-25",
                "gender": "Female",
                "nrc": "678901/23/1"
            },
            {
                "name": "David Lungu",
                "contact": "+260977890123",
                "date_of_birth": "1992-02-14",
                "gender": "Male",
                "nrc": "789012/34/1"
            },
            {
                "name": "Ruth Chanda",
                "contact": "+260978901234",
                "date_of_birth": "1987-08-07",
                "gender": "Female",
                "nrc": "890123/45/1"
            },
            {
                "name": "Michael Siame",
                "contact": "+260979012345",
                "date_of_birth": "1980-04-20",
                "gender": "Male",
                "nrc": "901234/56/1"
            },
            {
                "name": "Elizabeth Mbewe",
                "contact": "+260970123456",
                "date_of_birth": "1993-06-12",
                "gender": "Female",
                "nrc": "012345/67/1"
            }
        ]

        for member_data in members_data:
            member = Member(
                name=member_data["name"],
                contact=member_data["contact"],
                date_of_birth=datetime.strptime(member_data["date_of_birth"], "%Y-%m-%d").date(),
                gender=member_data["gender"],
                nrc=member_data["nrc"],
                ward_id=ward.id
            )
            db.add(member)

        db.commit()
        print(f"✅ Successfully seeded {len(members_data)} members!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding members: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_members()
