from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import bcrypt

from app.core.config import settings

def hash_password(password: str) -> str:
    encoded_password = password.encode("utf-8")
    if len(encoded_password) > 72:
        raise ValueError("Password must be at most 72 UTF-8 bytes")
    return bcrypt.hashpw(encoded_password, bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, hashed_password: str) -> bool:
    encoded_password = password.encode("utf-8")
    if len(encoded_password) > 72:
        return False
    try:
        return bcrypt.checkpw(encoded_password, hashed_password.encode("ascii"))
    except (TypeError, ValueError, UnicodeEncodeError):
        return False


def create_access_token(subject: str, role: str = "EXTERNAL_SUBMITTER") -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXP_MINUTES)
    payload = {
        "sub": subject,
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
