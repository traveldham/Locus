# Foundation Build Plan

Status: in progress

## Goal

Deliver a clean, locally runnable Locus Intelligence application foundation. A user can create an organization account, sign in, reach a protected branded workspace, view account and organization context, and sign out. No location-intelligence functionality is part of this milestone.

## Workstreams

### 1. Backend and database

- FastAPI application and `/api/v1` routing.
- PostgreSQL database `locus` through SQLAlchemy 2.
- Alembic migrations.
- User, organization, and organization-membership models.
- Password hashing, access/refresh session handling, and protected current-user endpoint.
- Health check, CORS, environment example, and focused tests.

### 2. Frontend application shell

- Retain the existing Next.js/Tailgrids design system.
- Remove NextAdmin demo pages, mock datasets, and visible template references.
- Add Locus Intelligence brand assets and product copy.
- Connect register, login, session restore, current user, and logout to FastAPI.
- Protect the authenticated app shell.
- Present a restrained empty foundation dashboard without invented analytics.

### 3. Integration and verification

- Create and migrate the local `locus` database.
- Seed or register a local test account.
- Verify browser-to-API-to-database authentication flow.
- Run backend tests, frontend lint, frontend production build, and visual checks at desktop and mobile widths.
- Update `PROJECT_MEMORY.md` and run instructions with the final contract and verification results.

## Completion criteria

- A new user can register with an organization.
- The credentials persist in PostgreSQL with a hashed password.
- The user can log in and load the protected workspace.
- The frontend can restore the authenticated user and organization context.
- Logout clears the session and protected screens are no longer accessible.
- No visible mock analytics or NextAdmin branding remains in the core product flow.
- Both applications have documented local startup commands and passing checks.
