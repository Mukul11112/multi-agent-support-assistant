"""Module 1: registration, login, JWT sessions."""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
from jose import JWTError, jwt

from backend import config
from backend.database.db import get_db, new_id, now
from backend.models.schemas import (LoginRequest, RegisterRequest, TokenResponse,
                                    UserPublic)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)

# We call bcrypt directly rather than going through passlib's CryptContext.
# passlib 1.7.4 probes bcrypt's version with a private attribute that bcrypt 4.1+
# removed, which raises "password cannot be longer than 72 bytes" on every hash
# call regardless of the actual password length. passlib is unmaintained, so
# pinning bcrypt<4.1 only defers the problem. bcrypt's own API is simpler anyway.


def hash_password(raw: str) -> str:
    # bcrypt hard-limits input to 72 bytes and errors past it, so truncate
    # explicitly. Note the limit is BYTES, not characters: a password of emoji
    # or Devanagari hits it far sooner than 72 keystrokes.
    payload = raw.encode("utf-8")[:72]
    return bcrypt.hashpw(payload, bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False  # malformed hash in the DB


def create_token(user_id: str) -> str:
    expire = now() + timedelta(minutes=config.JWT_EXPIRY_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM,
    )


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, config.JWT_SECRET,
                             algorithms=[config.JWT_ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user = get_db().get_user(user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return user


def _public(user: dict) -> UserPublic:
    return UserPublic(id=user["id"], email=user["email"], name=user["name"],
                      is_premium=user.get("is_premium", False))


@router.post("/register", response_model=TokenResponse,
             status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    db = get_db()
    if db.get_user_by_email(body.email.lower()):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = {
        "id": new_id(),
        "email": body.email.lower(),
        "name": body.name.strip(),
        "password_hash": hash_password(body.password),
        "is_premium": False,
        "created_at": now(),
    }
    db.create_user(user)
    return TokenResponse(access_token=create_token(user["id"]), user=_public(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = get_db().get_user_by_email(body.email.lower())
    # Same message for unknown email and wrong password: distinguishing them
    # tells an attacker which emails are registered.
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return TokenResponse(access_token=create_token(user["id"]), user=_public(user))


@router.get("/me", response_model=UserPublic)
def me(user: dict = Depends(current_user)):
    return _public(user)
