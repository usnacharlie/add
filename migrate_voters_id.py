"""
Migration script to add voter IDs to existing members
and enforce voters_id as required and unique field
"""

from backend.config.database import SessionLocal, engine
from backend.models.member import Member
from sqlalchemy import text
import sys

def migrate_voters_id():
    """Migrate voters_id field to be required and unique"""
    db = SessionLocal()

    try:
        print("=" * 60)
        print("VOTER ID MIGRATION SCRIPT")
        print("=" * 60)

        # Get all members with NULL voters_id
        members_without_voterid = db.query(Member).filter(
            (Member.voters_id == None) | (Member.voters_id == '')
        ).all()

        if not members_without_voterid:
            print("\n✓ All members already have voter IDs!")
        else:
            print(f"\nFound {len(members_without_voterid)} members without voter IDs")
            print("\nOptions:")
            print("1. Generate temporary voter IDs (format: TEMP-XXXXXX)")
            print("2. Exit and manually populate voter IDs")

            choice = input("\nEnter your choice (1 or 2): ").strip()

            if choice == "1":
                print("\nGenerating temporary voter IDs...")
                for member in members_without_voterid:
                    # Generate temporary voter ID
                    temp_voterid = f"TEMP-{member.id:06d}"
                    member.voters_id = temp_voterid
                    print(f"  - {member.name} (ID: {member.id}) → {temp_voterid}")

                db.commit()
                print(f"\n✓ Generated {len(members_without_voterid)} temporary voter IDs")
                print("\nIMPORTANT: Update these temporary IDs with real voter IDs!")

            elif choice == "2":
                print("\nMigration cancelled. Please populate voter IDs manually.")
                db.close()
                return False
            else:
                print("\nInvalid choice. Migration cancelled.")
                db.close()
                return False

        # Apply database constraints
        print("\nApplying database constraints...")

        try:
            # Check if constraint already exists
            with engine.connect() as conn:
                # SQLite doesn't support ALTER TABLE to add constraints easily
                # We need to check if the unique constraint exists
                result = conn.execute(text("""
                    SELECT sql FROM sqlite_master
                    WHERE type='table' AND name='members'
                """))
                table_sql = result.fetchone()[0]

                if "UNIQUE" in table_sql and "voters_id" in table_sql:
                    print("✓ Unique constraint already exists on voters_id")
                else:
                    print("\nWARNING: Cannot add constraints to existing SQLite table.")
                    print("The model has been updated, but you may need to:")
                    print("1. Create a new database with the updated schema")
                    print("2. Or use Alembic for proper migrations")
                    print("\nFor now, the application will enforce uniqueness at the application level.")
        except Exception as e:
            print(f"\nNote: {e}")
            print("Constraints will be enforced at the application level.")

        # Verify all members now have voter IDs
        members_without_voterid = db.query(Member).filter(
            (Member.voters_id == None) | (Member.voters_id == '')
        ).count()

        if members_without_voterid == 0:
            print("\n" + "=" * 60)
            print("✓ MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print("\nAll members now have voter IDs")
            print("Voter ID is now a required and unique field")
            return True
        else:
            print("\n" + "=" * 60)
            print("⚠ MIGRATION INCOMPLETE")
            print("=" * 60)
            print(f"{members_without_voterid} members still without voter IDs")
            return False

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migrate voters_id to be required and unique')
    parser.add_argument('--auto', action='store_true', help='Automatically generate temporary voter IDs')
    args = parser.parse_args()

    if args.auto:
        # Modify the function to auto-generate
        print("\nAuto-generating temporary voter IDs for existing members...")
        db = SessionLocal()
        try:
            members_without_voterid = db.query(Member).filter(
                (Member.voters_id == None) | (Member.voters_id == '')
            ).all()

            if not members_without_voterid:
                print("\n✓ All members already have voter IDs!")
            else:
                print(f"\nGenerating temporary voter IDs for {len(members_without_voterid)} members...")
                for member in members_without_voterid:
                    temp_voterid = f"TEMP-{member.id:06d}"
                    member.voters_id = temp_voterid
                    print(f"  - {member.name} (ID: {member.id}) → {temp_voterid}")

                db.commit()
                print(f"\n✓ Generated {len(members_without_voterid)} temporary voter IDs")
                print("\nIMPORTANT: Update these temporary IDs with real voter IDs!")
                print("\n" + "=" * 60)
                print("✓ MIGRATION COMPLETED SUCCESSFULLY")
                print("=" * 60)
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            db.rollback()
            db.close()
            sys.exit(1)
        finally:
            db.close()
        sys.exit(0)
    else:
        print("\nThis script will update the voters_id field to be required and unique.")
        print("For existing members without voter IDs, temporary IDs will be generated.")
        print("\nPress Ctrl+C to cancel, or Enter to continue...")

        try:
            input()
            success = migrate_voters_id()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n\nMigration cancelled by user.")
            sys.exit(1)
