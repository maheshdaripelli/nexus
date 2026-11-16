# Nexus

Nexus is a multi-tenant workspace and organization management application. The repository contains a FastAPI + SQLAlchemy async backend and a React + TypeScript + Vite frontend.

## Prerequisites

- Python 3.12 recommended
- Node.js 22
- PostgreSQL 15 or later
- Git

## Backend setup (Windows PowerShell)

From the repository root:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` with your local PostgreSQL connection string and a strong random JWT secret. Do not commit this file.

Example:

```env
DATABASE_URL=postgresql+asyncpg://nexus_app:YOUR_PASSWORD@localhost:5432/nexus
JWT_SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_ORIGIN=http://localhost:5173
```

Create the database and a database user in PostgreSQL, then from `backend`:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Useful URLs:

- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Database health: http://127.0.0.1:8000/health/database

## Frontend setup

Open another terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

The frontend defaults to the API at `http://127.0.0.1:8000`. Change `VITE_API_BASE_URL` in `frontend/.env` only if your API runs elsewhere.

Open http://localhost:5173.

## First-use flow

1. Register a user.
2. Create a workspace during onboarding (the creator becomes its owner).
3. Use Overview, Users, Teams, Roles, Audit Logs and Settings.
4. To invite someone, create an invitation and share the generated acceptance link. Email delivery is not configured; the API currently returns a development token.
5. The invited person must register or sign in using the invited email before accepting the invitation.

## Platform Super Admin

Platform administration is separate from organization membership. To grant the role to an existing user, run this trusted operator command from the `backend` directory:

```powershell
python -m scripts.grant_platform_admin --email admin@example.com
```

The account must already exist. This command writes to the `platform_admins` table; there is intentionally no public self-promotion endpoint.

Then sign in as that account and open the Platform admin section.

## Current implementation notes

- Organization membership roles (owner/admin/manager/member/viewer) are currently the authorization values used by several endpoints.
- Custom roles and permission sets can be created and edited, but they are not yet connected to membership assignment or consistently enforced as granular authorization rules.
- Audit events are recorded for the main organization, team, invitation, member-role and role-management mutations. Other actions may not yet emit audit events.
- Invitation email delivery, password reset, MFA, notification delivery, billing, and production deployment configuration are not included.
- Platform admin dashboard is read-only for global overview and organization listing.
- This project is a development MVP, not yet a production security-reviewed service.

## Validation

GitHub Actions workflow `.github/workflows/nexus-ci.yml` installs backend dependencies, compiles backend modules, installs frontend dependencies, and runs the frontend TypeScript/Vite production build. Database integration tests and full API behavior tests still need to be added.
