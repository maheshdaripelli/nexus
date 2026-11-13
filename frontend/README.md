# Nexus Frontend

A responsive React + TypeScript workspace-management dashboard starter.

## Requirements
- Node.js 20+ recommended
- npm

## Run locally
```powershell
npm install
npm run dev
```
Open http://localhost:5173.

## Production build
```powershell
npm run build
npm run preview
```

## Backend integration
The UI currently uses demo data so you can focus on the FastAPI backend without waiting for endpoints.
An API client is prepared in `src/lib/api.ts`.

1. Copy `.env.example` to `.env`.
2. Set `VITE_API_BASE_URL` to your FastAPI URL.
3. When your backend endpoints are ready, set `VITE_USE_DEMO_DATA=false` and connect the relevant queries in the feature pages.

Expected API routes to implement later:
- `GET /api/users`
- `GET /api/teams`
- `GET /api/roles`
- `GET /api/audit-logs`
- `GET /health`

This frontend does not yet implement real authentication, authorization, or persistence. Demo interactions are local UI state only.
