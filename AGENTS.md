# AGENTS.md

## Project: Project-COMMAND / KIIT Safety Connect

### Purpose
Project-COMMAND is a campus safety and emergency-response web platform for the KIIT campus. It is designed around incident reporting, control-room coordination, responder dispatch, campus mapping, and role-based access.

The project is being developed for a hackathon based on the Web-Shooter Dispatch problem statement.

## Repository Structure

- `frontend/` — Vite + React + TypeScript frontend
- `backend/` — FastAPI backend
- `tests/` — project tests
- `memory/` — project memory/context files
- `README.md` — project documentation

## Frontend Rules

- Preserve the existing UI/UX unless a change is explicitly requested.
- Do not remove existing dashboards, maps, incident views, dispatch functionality, or role-specific flows while making unrelated changes.
- Use the existing React/TypeScript architecture and components where possible.
- Keep the application responsive and usable on desktop and mobile.
- Run `npm run build` after frontend changes whenever possible.

## Authentication

The project supports role-based portals:

- `CIVILIAN`
- `OFFICER` / Control Room
- `RESPONSE_TEAM`

The current hackathon demo may use frontend demo authentication when the production backend is unavailable.

Demo authentication must remain clearly separated from production authentication.

Never place real passwords, API keys, MongoDB credentials, JWT secrets, or other sensitive credentials in source code or Git.

## Campus Map and Incident Data

- Preserve the existing KIIT campus map and safety/incident visualization.
- Do not replace existing map functionality with unrelated mock UI.
- Mock/demo incident data should be clearly identifiable as demo data when used.
- Do not present fabricated historical incidents as verified real-world incidents.

## Backend

- Backend is FastAPI-based.
- Backend API routes are under `/api`.
- Keep backend API contracts stable unless the task specifically requires changing them.
- Do not expose secrets or local `.env` values in commits.

## Security

- Never commit `.env`, credentials, private keys, tokens, or production secrets.
- Use environment variables for configuration.
- Do not weaken authentication or authorization for production code.
- If demo authentication is implemented, label it as demo-only and keep the real authentication path available when configured.

## Development and Git

Before committing:

1. Review changed files.
2. Ensure unrelated files were not modified.
3. Do not commit `node_modules/`, build output, or secrets.
4. Run the relevant build/test commands when practical.

Use clear commit messages describing the change.

## Deployment

For the frontend on Vercel:

- Framework: Vite
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

Do not assume the backend is deployed unless it has been explicitly configured.

## AI Coding Instructions

When modifying this repository:

1. Inspect the existing implementation before changing it.
2. Prefer the smallest change that satisfies the requested task.
3. Preserve existing functionality.
4. Do not rewrite unrelated files.
5. Explain important architectural or security implications of changes.
6. Verify builds after significant frontend changes.
