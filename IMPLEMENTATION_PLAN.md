# Member Registry System - Feature Expansion Plan

## Overview
This document outlines the implementation plan for expanding the Member Registry System with:
1. Role-Based Access Control (RBAC)
2. Event Management
3. Referral System
4. Membership Card Generation
5. Member Portal

---

## 1. Database Schema Design

### 1.1 Role-Based Access Control (RBAC)

```sql
-- Roles Table
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Permissions Table
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,  -- e.g., 'members', 'events', 'roles'
    action VARCHAR(50) NOT NULL,     -- e.g., 'create', 'read', 'update', 'delete'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Role-Permission Mapping
CREATE TABLE role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_id)
);

-- User-Role Mapping (for both admins and members)
CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    user_type VARCHAR(20) NOT NULL,  -- 'admin' or 'member'
    role_id INTEGER NOT NULL,
    assigned_by INTEGER,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);
```

### 1.2 Event Management

```sql
-- Events Table
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_type VARCHAR(50),  -- 'meeting', 'rally', 'training', 'social'
    start_date DATETIME NOT NULL,
    end_date DATETIME,
    location VARCHAR(200),
    venue TEXT,
    max_attendees INTEGER,
    status VARCHAR(20) DEFAULT 'upcoming',  -- 'upcoming', 'ongoing', 'completed', 'cancelled'
    created_by INTEGER NOT NULL,
    province_id INTEGER,
    district_id INTEGER,
    constituency_id INTEGER,
    ward_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (ward_id) REFERENCES wards(id)
);

-- Event Registrations
CREATE TABLE event_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    registration_status VARCHAR(20) DEFAULT 'registered',  -- 'registered', 'attended', 'cancelled'
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attendance_marked_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    UNIQUE(event_id, member_id)
);

-- Event Attachments (optional)
CREATE TABLE event_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);
```

### 1.3 Referral System

```sql
-- Referrals Table
CREATE TABLE referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,  -- Member who made the referral
    referred_member_id INTEGER,     -- New member who joined (NULL until they register)
    referred_name VARCHAR(200),
    referred_contact VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'registered', 'expired'
    referral_code VARCHAR(50) UNIQUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    registered_at TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES members(id),
    FOREIGN KEY (referred_member_id) REFERENCES members(id)
);

-- Referral Rewards (optional - for gamification)
CREATE TABLE referral_rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    referral_id INTEGER NOT NULL,
    reward_type VARCHAR(50),
    reward_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES members(id),
    FOREIGN KEY (referral_id) REFERENCES referrals(id)
);
```

### 1.4 Membership Cards

```sql
-- Membership Cards Table
CREATE TABLE membership_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    card_number VARCHAR(50) UNIQUE NOT NULL,
    issue_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'expired', 'suspended', 'revoked'
    card_type VARCHAR(50) DEFAULT 'standard',  -- 'standard', 'premium', 'lifetime'
    qr_code_path VARCHAR(500),
    issued_by INTEGER,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    renewed_at TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);

-- Card Transactions (for tracking renewals, etc.)
CREATE TABLE card_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    transaction_type VARCHAR(50),  -- 'issued', 'renewed', 'suspended', 'reactivated'
    performed_by INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES membership_cards(id) ON DELETE CASCADE
);
```

---

## 2. API Endpoints Structure

### 2.1 RBAC Endpoints

```
# Roles Management
POST   /api/v1/roles                    - Create new role
GET    /api/v1/roles                    - List all roles
GET    /api/v1/roles/{id}               - Get role details
PUT    /api/v1/roles/{id}               - Update role
DELETE /api/v1/roles/{id}               - Delete role

# Permissions Management
GET    /api/v1/permissions              - List all permissions
GET    /api/v1/permissions/{id}         - Get permission details

# Role-Permission Assignment
POST   /api/v1/roles/{id}/permissions   - Assign permissions to role
DELETE /api/v1/roles/{id}/permissions/{permission_id}  - Remove permission

# User-Role Assignment
POST   /api/v1/users/{id}/roles         - Assign role to user
DELETE /api/v1/users/{id}/roles/{role_id}  - Remove role from user
GET    /api/v1/users/{id}/permissions   - Get user's effective permissions
```

### 2.2 Event Management Endpoints

```
# Events
POST   /api/v1/events                   - Create new event
GET    /api/v1/events                   - List all events (with filters)
GET    /api/v1/events/{id}              - Get event details
PUT    /api/v1/events/{id}              - Update event
DELETE /api/v1/events/{id}              - Delete event

# Event Registrations
POST   /api/v1/events/{id}/register     - Register member for event
GET    /api/v1/events/{id}/attendees    - List event attendees
PUT    /api/v1/events/{id}/attendance/{member_id}  - Mark attendance
DELETE /api/v1/events/{id}/register/{member_id}    - Cancel registration

# Member's Events
GET    /api/v1/members/{id}/events      - Get member's registered events
```

### 2.3 Referral Endpoints

```
# Referrals
POST   /api/v1/referrals                - Create new referral
GET    /api/v1/referrals                - List all referrals
GET    /api/v1/referrals/{id}           - Get referral details
PUT    /api/v1/referrals/{id}           - Update referral
DELETE /api/v1/referrals/{id}           - Delete referral

# Member's Referrals
GET    /api/v1/members/{id}/referrals   - Get member's referrals
GET    /api/v1/referrals/code/{code}    - Validate referral code
```

### 2.4 Membership Card Endpoints

```
# Membership Cards
POST   /api/v1/cards                    - Issue new membership card
GET    /api/v1/cards                    - List all cards
GET    /api/v1/cards/{id}               - Get card details
PUT    /api/v1/cards/{id}               - Update card status
DELETE /api/v1/cards/{id}               - Revoke card

# Member's Card
GET    /api/v1/members/{id}/card        - Get member's card
POST   /api/v1/members/{id}/card/renew  - Renew member's card
GET    /api/v1/cards/{id}/pdf           - Generate card PDF
GET    /api/v1/cards/{id}/qr            - Generate card QR code
```

---

## 3. Frontend Structure

### 3.1 Admin Module

```
/admin/
├── roles/
│   ├── index              - List all roles
│   ├── new                - Create new role
│   ├── {id}/edit          - Edit role
│   └── {id}/permissions   - Manage role permissions
├── events/
│   ├── index              - List all events
│   ├── new                - Create new event
│   ├── {id}/view          - View event details & attendees
│   └── {id}/edit          - Edit event
├── referrals/
│   ├── index              - List all referrals
│   └── stats              - Referral statistics
└── cards/
    ├── index              - List all cards
    ├── issue              - Issue new card
    └── {id}/view          - View card details
```

### 3.2 Member Portal

```
/member/
├── dashboard              - Member dashboard with quick stats
├── profile                - View/edit own profile
├── events/
│   ├── index              - Browse available events
│   ├── {id}/view          - View event details
│   └── my-events          - My registered events
├── referrals/
│   ├── index              - My referrals
│   └── new                - Create referral
└── card/
    └── view               - View my membership card
```

---

## 4. System Roles (Pre-defined)

```python
SYSTEM_ROLES = {
    'super_admin': {
        'name': 'Super Administrator',
        'description': 'Full system access',
        'permissions': ['*']  # All permissions
    },
    'admin': {
        'name': 'Administrator',
        'description': 'General administrative access',
        'permissions': [
            'members.create', 'members.read', 'members.update', 'members.delete',
            'events.create', 'events.read', 'events.update', 'events.delete',
            'referrals.read', 'referrals.update',
            'cards.create', 'cards.read', 'cards.update',
            'reports.read'
        ]
    },
    'ward_coordinator': {
        'name': 'Ward Coordinator',
        'description': 'Manage ward-level activities',
        'permissions': [
            'members.create', 'members.read', 'members.update',
            'events.create', 'events.read', 'events.update',
            'referrals.read',
            'cards.read'
        ]
    },
    'member': {
        'name': 'Member',
        'description': 'Regular member access',
        'permissions': [
            'events.read', 'events.register',
            'referrals.create', 'referrals.read_own',
            'cards.read_own',
            'profile.read_own', 'profile.update_own'
        ]
    }
}
```

---

## 5. Implementation Phases

### Phase 1: Foundation (RBAC System)
1. Create database models for roles, permissions, role_permissions
2. Create API endpoints for role management
3. Update authentication to check permissions
4. Create admin UI for role management
5. Seed default roles and permissions

### Phase 2: Event Management
1. Create database models for events and registrations
2. Create API endpoints for event CRUD and registration
3. Create admin UI for event management
4. Create member UI for browsing and registering events

### Phase 3: Referral System
1. Create database models for referrals
2. Create API endpoints for referral management
3. Create admin UI for viewing referrals
4. Create member UI for creating referrals

### Phase 4: Membership Cards
1. Create database models for membership cards
2. Create API endpoints for card management
3. Implement QR code generation
4. Implement PDF card generation
5. Create admin UI for issuing cards
6. Create member UI for viewing cards

### Phase 5: Member Portal
1. Create member authentication system
2. Create member dashboard
3. Integrate all member-facing features
4. Implement permission-based view rendering

---

## 6. Technology Stack

### Backend
- FastAPI (existing)
- SQLAlchemy ORM (existing)
- QR Code Generation: `python-qrcode`
- PDF Generation: `reportlab` or `weasyprint`

### Frontend
- Flask (existing)
- Bootstrap 5 (existing)
- Chart.js (for analytics)
- FullCalendar (for event calendar)

---

## 7. Next Steps

Please review this plan and confirm:
1. Are these the features you want?
2. Should we proceed in phases or implement everything at once?
3. Any specific requirements for membership cards (design, format)?
4. Any additional features for events (payments, reminders)?
5. Should referrals have rewards/points system?

Once approved, I'll start with Phase 1 (RBAC System).
