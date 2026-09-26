import hashlib
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response

from lib.db import db
from models.auth import LoginRequest, SignupRequest, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])
SESSION_COOKIE = "kiit_session"
SESSION_DAYS = 7
LOGIN_ATTEMPTS: dict[str, list[float]] = {}


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 120_000)
        return secrets.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _public_user(document: dict) -> UserPublic:
    return UserPublic(
        id=document["id"],
        full_name=document["full_name"],
        email=document["email"],
        role=document.get("role", "CIVILIAN"),
        created_at=document["created_at"],
    )


async def _start_session(response: Response, user_id: str) -> None:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    await db.sessions.insert_one(
        {
            "token_hash": hashlib.sha256(token.encode()).hexdigest(),
            "user_id": user_id,
            "created_at": now,
            "expires_at": now + timedelta(days=SESSION_DAYS),
        }
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=os.environ.get("COOKIE_SECURE", "true").lower() == "true",
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 60 * 60,
        path="/",
    )


async def _user_from_cookie(token: str | None) -> dict | None:
    if not token:
        return None
    session = await db.sessions.find_one({"token_hash": hashlib.sha256(token.encode()).hexdigest()})
    if not session:
        return None
    expires_at = session.get("expires_at")
    if expires_at and expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        await db.sessions.delete_one({"_id": session["_id"]})
        return None
    return await db.users.find_one({"id": session["user_id"]})


async def require_user(kiit_session: str | None = Cookie(default=None)) -> dict:
    user = await _user_from_cookie(kiit_session)
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user


@router.post("/signup", response_model=UserPublic)
async def signup(payload: SignupRequest, response: Response):
    email = str(payload.email).lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = {
        "id": str(uuid.uuid4()),
        "full_name": payload.full_name.strip(),
        "email": email,
        "password_hash": _hash_password(payload.password),
        "role": "CIVILIAN",
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(user)
    await _start_session(response, user["id"])
    return _public_user(user)


@router.post("/login", response_model=UserPublic)
async def login(payload: LoginRequest, response: Response, request: Request):
    key = f"{request.client.host if request.client else 'unknown'}:{str(payload.email).lower()}"
    now = time.monotonic()
    attempts = [stamp for stamp in LOGIN_ATTEMPTS.get(key, []) if now - stamp < 300]
    if len(attempts) >= 8:
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Try again in five minutes")
    user = await db.users.find_one({"email": str(payload.email).lower()})
    if not user or not _verify_password(payload.password, user.get("password_hash", "")):
        LOGIN_ATTEMPTS[key] = [*attempts, now]
        raise HTTPException(status_code=401, detail="Invalid email or password")
    legacy = {"Control Room Officer": "OFFICER", "Civilian / Student": "CIVILIAN", "Response Team": "RESPONSE_TEAM"}
    role = legacy.get(user.get("role", ""), user.get("role", "CIVILIAN"))
    if payload.portal_role and payload.portal_role != role:
        LOGIN_ATTEMPTS[key] = [*attempts, now]
        raise HTTPException(status_code=403, detail="This account is not authorized for the selected portal")
    LOGIN_ATTEMPTS.pop(key, None)
    await _start_session(response, user["id"])
    return _public_user(user)


@router.get("/me", response_model=UserPublic)
async def me(user: dict = Depends(require_user)):
    return _public_user(user)


@router.post("/logout", status_code=204)
async def logout(response: Response, kiit_session: str | None = Cookie(default=None)):
    if kiit_session:
        await db.sessions.delete_one({"token_hash": hashlib.sha256(kiit_session.encode()).hexdigest()})
    response.delete_cookie(SESSION_COOKIE, path="/")