# Nexus

Nexus is a multi-tenant organization and workspace management application. It includes a FastAPI + async SQLAlchemy + PostgreSQL backend and a React + TypeScript + Vite frontend.

## Stack and prerequisites

- Python 3.12
- Node.js 22
- PostgreSQL 15+
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

Create a PostgreSQL database named `nexus` and a database user with access to it. Set `DATABASE_URL` in `backend/.env` to:

```env
DATABASE_URL=postgresql+asyncpg://nexus_app:YOUR_PASSWORD@localhost:5432/nexus
JWT_SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
FRONTEND_ORIGIN=http://localhost:5173
```

Also configure the SMTP values if you want invitation emails to be delivered. For Gmail, use a Google App Password, not your normal account password. Keep `.env` private and never commit secrets.

Run migrations and start the API from the `backend` directory:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

Health checks: http://127.0.0.1:8000/health and http://127.0.0.1:8000/health/database

## Frontend setup

In a second terminal from the repository root:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

The frontend defaults to `http://127.0.0.1:8000` for the API. Set `VITE_API_BASE_URL` in `frontend/.env` if your backend uses another address. Open http://localhost:5173.

## First-time platform bootstrap

Public registration and self-service organization creation are intentionally disabled. After migrations, create the first Platform Super Admin using the trusted operator CLI. It creates the account if it does not exist, asks for the password interactively, and grants platform access:

```powershell
cd backend
python -m scripts.bootstrap_platform_admin --email admin@example.com
```

For an existing user, the same command promotes the account without changing its password. Do not expose platform-admin assignment as a public endpoint.

Sign in as the Platform Super Admin and open **Platform admin** to provision an organization and issue its first Owner invitation. The Owner can then invite users to that organization.

## Product behavior

- One global user account can belong to multiple organizations.
- Organization membership and roles are scoped to each organization.
- Platform Super Admin access is separate from organization roles.
- Public registration is disabled; a valid invitation is required to create a new account.
- Existing users accept invitations after signing in with the invited email address.
- Invitation tokens are random, single-use, stored as SHA-256 hashes, and expire after seven days.
- Users can update their personal display name; email addresses remain immutable through the profile UI.
- Custom roles are assigned to memberships and their permissions are checked by the backend.
- Team and member records are always queried through the active organization scope.
- Audit events are written for core membership, invitation, team, role, and organization changes.

## Local validation

Run backend unit tests from `backend`:

```powershell
python -m unittest discover -s tests -v
```

Build and type-check the frontend from `frontend`:

```powershell
npm ci
npm run build
```

GitHub Actions runs backend compilation, backend authorization unit tests, and the frontend TypeScript/Vite build. These checks do not replace local PostgreSQL-backed API and end-to-end testing.

## Not included

Password reset, MFA, billing, external SSO, production hosting configuration, and a full production security audit are outside the current MVP scope. Review deployment secrets, HTTPS, database backups, CORS origins, and rate limiting before a public production launch.