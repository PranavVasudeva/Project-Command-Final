# KIIT Safety GIS — Bhubaneswar Incident Command

## What it does
The app is a role-based KIIT safety dispatch network built around getting the right available hero to an incident quickly. Civilians/students report and track issues, control-room officers validate reports and assign ranked response teams, and field teams move incidents through en-route and resolved states. The officer portal also retains the Bhubaneswar GIS, hotspot analytics, and patrol geofences.

## Data model
- `UserPublic`: string id, full name, email, role, created timestamp.
- `Incident`: id, category, title, zone, severity, status, occurred timestamp, dispatch unit, resolution minutes, description, latitude, and longitude.
- `CampusZone`: KIIT or Bhubaneswar area name, representative historical incident count, risk level, latitude/longitude, geographic scope, peak hours, and category breakdown.
- `Geofence`: account-owned named polygon, patrol owner, risk threshold, notes, timestamps, and calculated incident count, severity risk score, average response time, and category breakdown.
- `IncidentReport`: civilian report with category, severity, description, map coordinates, optional contact/photo filename, status, assigned teams, primary team, and full actor-stamped timeline.
- `ResponseTeam`: verified seeded team account, capabilities, base coordinates, availability, and current workload.
- Sessions are stored in MongoDB and represented to the browser only by an httpOnly `kiit_session` cookie.

## Key flows
1. New officer opens `/login`, switches to Create account, submits name/email/password (8+ characters), and is signed in immediately.
2. Returning officer signs in with the same email/password; invalid credentials show a clear error instead of a dead end.
3. Authenticated officer sees `/` control room. The map defaults to Bhubaneswar, supports native pan/zoom, KIIT and city focus, predefined landmark search, fullscreen, locally styled Street/Light/Tactical views over the same key-free OSM tiles, incident dots, and clickable hotspot radii.
4. Time/category filters update the feed through `/api/incidents`; hotspot and feed clicks open local intelligence details.
5. JSON and share actions operate client-side on the current incident feed. Drawer dispatch/review controls are clearly labeled prototype actions and contact no emergency service.
6. Officers can draw a polygon from map clicks, name it, set an owner/threshold/notes, save it to MongoDB, compare analytics across saved boundaries, edit metadata, redraw geometry, and delete the zone.
7. A civilian report appears in the control-room queue on a 2.5-second refresh. Officers can acknowledge it and compare team recommendations scored by capability match, distance, availability, and current workload.
8. An officer assigns one or more teams and selects a primary responder. Assigned teams see the incident in their own portal, mark themselves en route, and resolve it; every transition is visible to the civilian and officer timeline.
9. Authenticated Server-Sent Events invalidate each role’s dispatch/message caches immediately; 10–15 second polling remains a visible fallback.
10. Teams explicitly accept missions before going en route, control availability, update location, and can exchange scoped messages with the reporter and officer.
11. Officers can escalate unacknowledged assignments back into the recommendation queue so incidents do not fall through the cracks.

## Auth roles
- `CIVILIAN`: self-registers, creates reports, and sees only their own reports.
- `OFFICER`: verified seeded account, sees every report, recommendation, team, GIS and geofence tool.
- `RESPONSE_TEAM`: verified seeded account, sees only incidents assigned to its team and can mark en-route/resolved.
Auth is custom email/password with PBKDF2 password hashes, MongoDB sessions, httpOnly cookies, and server-side role authorization. Portal selection at login is checked against the stored role.

Privileged seed passwords are loaded from backend environment values, cookies are Secure/HttpOnly/SameSite=Lax, CORS is explicitly allowlisted, login attempts are throttled, and the previously exposed gate account is removed during seeding.

## Demo data note
Incident overlays and counts are representative demo data for product demonstration, not official KIIT, police, hospital, or city records. Base geography comes from OpenStreetMap tiles with visible attribution. KIIT Square Junction remains the primary KIIT hotspot; wider Bhubaneswar zones provide city context. Google Maps is deferred until a billing-enabled, browser-restricted key is supplied.