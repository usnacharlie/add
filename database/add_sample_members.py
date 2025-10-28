"""
Add sample members to the database
"""
import sys
import os
from datetime import date, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.config.database import SessionLocal
from backend.models import Member, Ward

def add_sample_members():
    """Add sample members to the database"""
    db = SessionLocal()

    try:
        # Get available wards
        wards = db.query(Ward).all()
        if not wards:
            print("No wards found. Please run seed_data.py first.")
            return

        # Sample member data
        sample_members = [
            {
                "name": "Charles Mwansa",
                "gender": "Male",
                "date_of_birth": date(1985, 3, 15),
                "nrc": "123456/10/1",
                "voters_id": "VID001234",
                "contact": "0977123400"
            },
            {
                "name": "Sarah Phiri",
                "gender": "Female",
                "date_of_birth": date(1990, 7, 22),
                "nrc": "234567/10/1",
                "voters_id": "VID002345",
                "contact": "0966234567"
            },
            {
                "name": "David Chirwa",
                "gender": "Male",
                "date_of_birth": date(1988, 11, 8),
                "nrc": "345678/10/1",
                "voters_id": "VID003456",
                "contact": "0977345678"
            },
            {
                "name": "Grace Lungu",
                "gender": "Female",
                "date_of_birth": date(1992, 5, 30),
                "nrc": "456789/10/1",
                "voters_id": "VID004567",
                "contact": "0966456789"
            },
            {
                "name": "Joseph Banda",
                "gender": "Male",
                "date_of_birth": date(1987, 9, 14),
                "nrc": "567890/10/1",
                "voters_id": "VID005678",
                "contact": "0977567890"
            },
            {
                "name": "Patricia Mulenga",
                "gender": "Female",
                "date_of_birth": date(1995, 2, 18),
                "nrc": "678901/10/1",
                "voters_id": "VID006789",
                "contact": "0966678901"
            },
            {
                "name": "Michael Simwanza",
                "gender": "Male",
                "date_of_birth": date(1983, 12, 25),
                "nrc": "789012/10/1",
                "voters_id": "VID007890",
                "contact": "0977789012"
            },
            {
                "name": "Elizabeth Haamukwanza",
                "gender": "Female",
                "date_of_birth": date(1991, 6, 10),
                "nrc": "890123/10/1",
                "voters_id": "VID008901",
                "contact": "0966890123"
            },
            {
                "name": "Peter Musonda",
                "gender": "Male",
                "date_of_birth": date(1989, 4, 5),
                "nrc": "901234/10/1",
                "voters_id": "VID009012",
                "contact": "0977901234"
            },
            {
                "name": "Rachel Kasonde",
                "gender": "Female",
                "date_of_birth": date(1993, 8, 20),
                "nrc": "012345/10/1",
                "voters_id": "VID010123",
                "contact": "0966012345"
            },
            {
                "name": "James Tembo",
                "gender": "Male",
                "date_of_birth": date(1986, 1, 12),
                "nrc": "111111/10/1",
                "voters_id": "VID011111",
                "contact": "0977111111"
            },
            {
                "name": "Mary Zulu",
                "gender": "Female",
                "date_of_birth": date(1994, 10, 28),
                "nrc": "222222/10/1",
                "voters_id": "VID022222",
                "contact": "0966222222"
            },
            {
                "name": "Andrew Ng'andu",
                "gender": "Male",
                "date_of_birth": date(1984, 7, 16),
                "nrc": "333333/10/1",
                "voters_id": "VID033333",
                "contact": "0977333333"
            },
            {
                "name": "Rebecca Chilufya",
                "gender": "Female",
                "date_of_birth": date(1996, 3, 9),
                "nrc": "444444/10/1",
                "voters_id": "VID044444",
                "contact": "0966444444"
            },
            {
                "name": "Moses Mwale",
                "gender": "Male",
                "date_of_birth": date(1982, 11, 23),
                "nrc": "555555/10/1",
                "voters_id": "VID055555",
                "contact": "0977555555"
            }
        ]

        # Add members to database
        added_count = 0
        for member_data in sample_members:
            # Assign random ward
            ward = random.choice(wards)

            # Check if member already exists
            existing = db.query(Member).filter(Member.nrc == member_data["nrc"]).first()
            if existing:
                print(f"Member {member_data['name']} already exists, skipping...")
                continue

            # Create member
            member = Member(
                name=member_data["name"],
                gender=member_data["gender"],
                date_of_birth=member_data["date_of_birth"],
                nrc=member_data["nrc"],
                voters_id=member_data["voters_id"],
                contact=member_data["contact"],
                ward_id=ward.id
            )

            db.add(member)
            added_count += 1
            print(f"Added member: {member_data['name']}")

        db.commit()
        print(f"\n✅ Successfully added {added_count} sample members!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error adding sample members: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_sample_members()
