import asyncio
import os
import uuid
from datetime import datetime, timezone

from lib.db import db, ensure_indexes
from routers.auth import _hash_password


ACCOUNTS = [
    {"email": "control@kiit.ac.in", "full_name": "KIIT Control Room", "password_env": "DEMO_OFFICER_PASSWORD", "role": "OFFICER"},
    {"email": "security.alpha@kiit.ac.in", "full_name": "Security Alpha", "password_env": "DEMO_TEAM_PASSWORD", "role": "RESPONSE_TEAM", "team": {"id": "team-security-alpha", "name": "Security Alpha", "capabilities": ["Security", "Campus Disturbance", "Asset Theft", "Traffic Accident"], "latitude": 20.3533, "longitude": 85.8188}},
    {"email": "medical.response@kiit.ac.in", "full_name": "KIMS Medical Response", "password_env": "DEMO_TEAM_PASSWORD", "role": "RESPONSE_TEAM", "team": {"id": "team-medical", "name": "KIMS Medical Response", "capabilities": ["Medical Emergency", "Medical"], "latitude": 20.3498, "longitude": 85.8175}},
    {"email": "fire.response@kiit.ac.in", "full_name": "Campus Fire Unit", "password_env": "DEMO_TEAM_PASSWORD", "role": "RESPONSE_TEAM", "team": {"id": "team-fire", "name": "Campus Fire Unit", "capabilities": ["Fire Hazard", "Fire", "Infrastructure"], "latitude": 20.3572, "longitude": 85.8144}},
    {"email": "technical.response@kiit.ac.in", "full_name": "Technical Response Unit", "password_env": "DEMO_TEAM_PASSWORD", "role": "RESPONSE_TEAM", "team": {"id": "team-technical", "name": "Technical Response Unit", "capabilities": ["CCTV/Network Glitch", "Infrastructure", "Other"], "latitude": 20.3560, "longitude": 85.8214}},
]


async def seed() -> None:
    now = datetime.now(timezone.utc)
    for account in ACCOUNTS:
        existing = await db.users.find_one({"email": account["email"]})
        user_id = existing["id"] if existing else str(uuid.uuid4())
        await db.users.update_one(
            {"email": account["email"]},
            {"$set": {"id": user_id, "full_name": account["full_name"], "email": account["email"], "password_hash": _hash_password(os.environ[account["password_env"]]), "role": account["role"], "created_at": existing.get("created_at", now) if existing else now}},
            upsert=True,
        )
        if account.get("team"):
            team = {**account["team"], "user_id": user_id, "status": "AVAILABLE", "active_incidents": 0}
            await db.response_teams.update_one({"id": team["id"]}, {"$set": team}, upsert=True)
    await db.sessions.delete_many({"user_id": {"$in": [document["id"] async for document in db.users.find({"email": "gate-1790440226@kiit.ac.in"}, {"id": 1})]}})
    await db.users.delete_one({"email": "gate-1790440226@kiit.ac.in"})
    await ensure_indexes()
    print("Seeded verified officer and response-team accounts")


if __name__ == "__main__":
    asyncio.run(seed())