"""
Seed script for RBAC (Role-Based Access Control) system
Creates default roles, permissions, and role-permission mappings
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.config.database import SessionLocal
from backend.models import Role, Permission, RolePermission


def seed_rbac():
    """Seed RBAC data"""
    db = SessionLocal()

    try:
        print("🔐 Seeding RBAC System...")
        print("=" * 60)

        # ==================== CREATE PERMISSIONS ====================
        print("\n📋 Creating Permissions...")

        permissions_data = [
            # Member permissions
            {"name": "Create Members", "resource": "members", "action": "create", "description": "Create new members"},
            {"name": "Read Members", "resource": "members", "action": "read", "description": "View member information"},
            {"name": "Update Members", "resource": "members", "action": "update", "description": "Update member information"},
            {"name": "Delete Members", "resource": "members", "action": "delete", "description": "Delete members"},

            # Location permissions
            {"name": "Manage Provinces", "resource": "locations", "action": "manage_provinces", "description": "Manage provinces"},
            {"name": "Manage Districts", "resource": "locations", "action": "manage_districts", "description": "Manage districts"},
            {"name": "Manage Constituencies", "resource": "locations", "action": "manage_constituencies", "description": "Manage constituencies"},
            {"name": "Manage Wards", "resource": "locations", "action": "manage_wards", "description": "Manage wards"},

            # Role & Permission management
            {"name": "Create Roles", "resource": "roles", "action": "create", "description": "Create new roles"},
            {"name": "Read Roles", "resource": "roles", "action": "read", "description": "View roles"},
            {"name": "Update Roles", "resource": "roles", "action": "update", "description": "Update roles"},
            {"name": "Delete Roles", "resource": "roles", "action": "delete", "description": "Delete roles"},
            {"name": "Assign Permissions", "resource": "roles", "action": "assign_permissions", "description": "Assign permissions to roles"},

            # User-Role management
            {"name": "Assign User Roles", "resource": "user_roles", "action": "assign", "description": "Assign roles to users"},
            {"name": "View User Roles", "resource": "user_roles", "action": "read", "description": "View user role assignments"},
            {"name": "Remove User Roles", "resource": "user_roles", "action": "remove", "description": "Remove roles from users"},

            # Events permissions (for future use)
            {"name": "Create Events", "resource": "events", "action": "create", "description": "Create new events"},
            {"name": "Read Events", "resource": "events", "action": "read", "description": "View events"},
            {"name": "Update Events", "resource": "events", "action": "update", "description": "Update events"},
            {"name": "Delete Events", "resource": "events", "action": "delete", "description": "Delete events"},
            {"name": "Register for Events", "resource": "events", "action": "register", "description": "Register members for events"},
            {"name": "Mark Attendance", "resource": "events", "action": "mark_attendance", "description": "Mark event attendance"},

            # Referral permissions (for future use)
            {"name": "Create Referrals", "resource": "referrals", "action": "create", "description": "Create referrals"},
            {"name": "Read Referrals", "resource": "referrals", "action": "read", "description": "View referrals"},
            {"name": "Read Own Referrals", "resource": "referrals", "action": "read_own", "description": "View own referrals"},
            {"name": "Update Referrals", "resource": "referrals", "action": "update", "description": "Update referrals"},

            # Card permissions (for future use)
            {"name": "Issue Cards", "resource": "cards", "action": "create", "description": "Issue membership cards"},
            {"name": "Read Cards", "resource": "cards", "action": "read", "description": "View membership cards"},
            {"name": "Read Own Card", "resource": "cards", "action": "read_own", "description": "View own membership card"},
            {"name": "Update Cards", "resource": "cards", "action": "update", "description": "Update card status"},
            {"name": "Renew Cards", "resource": "cards", "action": "renew", "description": "Renew membership cards"},

            # Reports permissions
            {"name": "View Reports", "resource": "reports", "action": "read", "description": "View and generate reports"},
            {"name": "Export Data", "resource": "reports", "action": "export", "description": "Export data"},

            # Profile permissions
            {"name": "View Own Profile", "resource": "profile", "action": "read_own", "description": "View own profile"},
            {"name": "Update Own Profile", "resource": "profile", "action": "update_own", "description": "Update own profile"},

            # Dashboard permissions
            {"name": "View Admin Dashboard", "resource": "dashboard", "action": "view_admin", "description": "View admin dashboard"},
            {"name": "View Member Dashboard", "resource": "dashboard", "action": "view_member", "description": "View member dashboard"},
        ]

        permission_map = {}
        for perm_data in permissions_data:
            existing = db.query(Permission).filter(
                Permission.resource == perm_data["resource"],
                Permission.action == perm_data["action"]
            ).first()

            if existing:
                print(f"   ⏭  Permission '{perm_data['name']}' already exists")
                permission_map[f"{perm_data['resource']}.{perm_data['action']}"] = existing.id
            else:
                permission = Permission(**perm_data)
                db.add(permission)
                db.flush()
                permission_map[f"{perm_data['resource']}.{perm_data['action']}"] = permission.id
                print(f"   ✅ Created permission: {perm_data['name']}")

        db.commit()

        # ==================== CREATE ROLES ====================
        print("\n👥 Creating Roles...")

        roles_data = [
            {
                "name": "Super Administrator",
                "description": "Full system access with all permissions",
                "is_system_role": True,
                "permissions": "ALL"  # Special marker for all permissions
            },
            {
                "name": "Administrator",
                "description": "General administrative access",
                "is_system_role": True,
                "permissions": [
                    "members.create", "members.read", "members.update", "members.delete",
                    "events.create", "events.read", "events.update", "events.delete",
                    "events.register", "events.mark_attendance",
                    "referrals.read", "referrals.update",
                    "cards.create", "cards.read", "cards.update", "cards.renew",
                    "reports.read", "reports.export",
                    "dashboard.view_admin"
                ]
            },
            {
                "name": "Ward Coordinator",
                "description": "Manage ward-level activities and members",
                "is_system_role": True,
                "permissions": [
                    "members.create", "members.read", "members.update",
                    "events.create", "events.read", "events.update",
                    "events.register", "events.mark_attendance",
                    "referrals.read",
                    "cards.read",
                    "reports.read",
                    "dashboard.view_admin"
                ]
            },
            {
                "name": "Member",
                "description": "Regular member access",
                "is_system_role": True,
                "permissions": [
                    "events.read", "events.register",
                    "referrals.create", "referrals.read_own",
                    "cards.read_own",
                    "profile.read_own", "profile.update_own",
                    "dashboard.view_member"
                ]
            }
        ]

        role_map = {}
        for role_data in roles_data:
            permissions = role_data.pop("permissions")

            existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()

            if existing_role:
                print(f"   ⏭  Role '{role_data['name']}' already exists")
                role_map[role_data["name"]] = existing_role.id
            else:
                role = Role(**role_data)
                db.add(role)
                db.flush()
                role_map[role_data["name"]] = role.id
                print(f"   ✅ Created role: {role_data['name']}")

                # Assign permissions to role
                if permissions == "ALL":
                    # Assign all permissions to Super Administrator
                    all_permissions = db.query(Permission).all()
                    for perm in all_permissions:
                        role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
                        db.add(role_perm)
                    print(f"      → Assigned ALL permissions to {role_data['name']}")
                else:
                    # Assign specific permissions
                    for perm_key in permissions:
                        if perm_key in permission_map:
                            role_perm = RolePermission(
                                role_id=role.id,
                                permission_id=permission_map[perm_key]
                            )
                            db.add(role_perm)
                    print(f"      → Assigned {len(permissions)} permissions to {role_data['name']}")

        db.commit()

        print("\n" + "=" * 60)
        print("✅ RBAC System seeded successfully!")
        print(f"   📋 Created {len(permissions_data)} permissions")
        print(f"   👥 Created {len(roles_data)} roles")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding RBAC system: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_rbac()
