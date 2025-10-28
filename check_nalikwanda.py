#!/usr/bin/env python3
"""
Script to check if Nalikwanda already exists and what codes are in use
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://member_admin:secure_password_123@localhost:57022/party_membership"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main():
    session = SessionLocal()

    try:
        # Check if Nalikwanda already exists
        print("=== Checking for Nalikwanda constituency ===")
        result = session.execute(
            text("SELECT id, constituency_name, constituency_code, district_id FROM constituencies WHERE constituency_name LIKE '%alik%'")
        )
        nalikwanda = result.fetchall()

        if nalikwanda:
            print(f"Found {len(nalikwanda)} constituency(ies) with 'alik' in name:")
            for const in nalikwanda:
                print(f"  - Name: {const[1]}, Code: {const[2]}, ID: {const[0]}")
        else:
            print("No Nalikwanda constituency found")

        # Check codes starting with NAL
        print("\n=== Checking codes starting with NAL ===")
        result = session.execute(
            text("SELECT id, constituency_name, constituency_code FROM constituencies WHERE constituency_code LIKE 'NAL%'")
        )
        nal_codes = result.fetchall()

        if nal_codes:
            print(f"Found {len(nal_codes)} constituency(ies) with NAL codes:")
            for const in nal_codes:
                print(f"  - {const[1]}: {const[2]}")
        else:
            print("No NAL codes found")

        # Check all codes starting with MON (for Mongu)
        print("\n=== Checking codes starting with MON ===")
        result = session.execute(
            text("SELECT id, constituency_name, constituency_code FROM constituencies WHERE constituency_code LIKE 'MON%' ORDER BY constituency_code")
        )
        mon_codes = result.fetchall()

        if mon_codes:
            print(f"Found {len(mon_codes)} constituency(ies) with MON codes:")
            for const in mon_codes:
                print(f"  - {const[1]}: {const[2]}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
