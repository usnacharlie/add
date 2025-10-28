"""
Seed data script for initial database population
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.config.database import SessionLocal
from backend.models import Province, District, Constituency, Ward

def seed_sample_data():
    """Populate database with sample data"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_provinces = db.query(Province).count()
        if existing_provinces > 0:
            print("Database already contains data. Skipping seed.")
            return
        
        # Sample provinces
        provinces_data = [
            "Lusaka",
            "Copperbelt",
            "Central",
            "Eastern",
            "Northern",
            "Northwestern",
            "Southern",
            "Western",
            "Luapula",
            "Muchinga"
        ]
        
        provinces = []
        for prov_name in provinces_data:
            province = Province(name=prov_name)
            db.add(province)
            provinces.append(province)
        
        db.flush()
        
        # Sample districts, constituencies, and wards for Lusaka
        lusaka = provinces[0]
        lusaka_data = [
            ("Lusaka District", [
                ("Lusaka Central Constituency", ["Ward 1", "Ward 2", "Ward 3"]),
                ("Lusaka East Constituency", ["Ward 4", "Ward 5", "Ward 6"])
            ]),
            ("Chilanga District", [
                ("Chilanga Constituency", ["Ward A", "Ward B", "Ward C"])
            ]),
            ("Kafue District", [
                ("Kafue Constituency", ["Ward X", "Ward Y", "Ward Z"])
            ])
        ]

        for dist_name, constituencies_data in lusaka_data:
            district = District(name=dist_name, province_id=lusaka.id)
            db.add(district)
            db.flush()

            for const_name, wards_list in constituencies_data:
                constituency = Constituency(name=const_name, district_id=district.id)
                db.add(constituency)
                db.flush()

                for ward_name in wards_list:
                    ward = Ward(name=ward_name, constituency_id=constituency.id)
                    db.add(ward)

        # Sample districts, constituencies, and wards for Copperbelt
        copperbelt = provinces[1]
        copperbelt_data = [
            ("Ndola District", [
                ("Ndola Central Constituency", ["Ward 1", "Ward 2", "Ward 3"])
            ]),
            ("Kitwe District", [
                ("Kitwe Central Constituency", ["Ward A", "Ward B", "Ward C"])
            ]),
        ]

        for dist_name, constituencies_data in copperbelt_data:
            district = District(name=dist_name, province_id=copperbelt.id)
            db.add(district)
            db.flush()

            for const_name, wards_list in constituencies_data:
                constituency = Constituency(name=const_name, district_id=district.id)
                db.add(constituency)
                db.flush()

                for ward_name in wards_list:
                    ward = Ward(name=ward_name, constituency_id=constituency.id)
                    db.add(ward)
        
        db.commit()
        print("Sample data seeded successfully!")
        print(f"Added {len(provinces)} provinces")
        print(f"Added sample districts and wards")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_sample_data()
