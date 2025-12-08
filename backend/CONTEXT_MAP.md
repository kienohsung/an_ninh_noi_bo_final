# Project Context Map

## Domain Modules (Backend)
**Location**: `backend/app/modules/`

- **User/Auth**: `backend/app/modules/user/` & `backend/app/core/auth.py`
  - Handles: User authentication, User management.
- **Guest**: `backend/app/modules/guest/`
  - Handles: Guest registration, check-in/out, Long-term guests.
- **Asset**: `backend/app/modules/asset/`
  - Handles: Asset logging, Print tracking, Asset management.
- **Supplier**: `backend/app/modules/supplier/`
  - Handles: Supplier info, Supplier plates.
- **Report**: `backend/app/modules/report/`
  - Handles: Reporting logic.

## Core Components
- **Config**: `backend/app/core/config.py`
- **Database**: `backend/app/database.py` (Central Registry for all models)
- **Security**: `backend/app/core/security.py`

## Scripts
**Location**: `backend/scripts/`

- **Migrations**: `backend/scripts/migrations/`
  - `migrate_*.py`: Schema migrations and data fixes.
- **Tools**: `backend/scripts/tools/`
  - `sync_users.py`: User synchronization tools.
- **Setup**: `backend/scripts/setup/`
  - `add_bug_entry.py`: Setup utilities.

## Database
- SQLite File: `backend/security_v2_3.db`
