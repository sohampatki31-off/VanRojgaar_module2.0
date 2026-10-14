"""
Who is calling. Tokens are the host's: HS256 JWTs with `sub` (user id), `type` ("access") and
`exp`, signed with VANMITRA_JWT_SECRET (vanmitra_backend/app/auth/security.py).

The host also looks the user up in MongoDB (AppUser + UserRole) to learn the village. Standalone,
that lookup is a `UserDirectory`. At merge, replace `get_directory` with a function that reads
the host's `app_user` / `user_role` collections (docs/INTEGRATION.md); nothing else changes.

Only `villager` and `gram_sabha` users may use this module, each for their OWN land (PDF §4).
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Protocol

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import get_settings
from ..errors import ApiError
from .identity import UserInfo

ALLOWED_ROLES = frozenset({"villager", "gram_sabha"})
_bearer = HTTPBearer(auto_error=False)


class UserDirectory(Protocol):
    def get(self, user_id: uuid.UUID) -> UserInfo | None: ...


class EmptyDirectory:
    """Knows nobody. The safe default: every request is refused until a directory is wired."""

    def get(self, user_id: uuid.UUID) -> UserInfo | None:
        return None


# Built-in DEVELOPMENT users (only when VANMITRA_LIVELIHOOD_DEV_USERS=true; refused in production).
DEV_VILLAGER = UserInfo(
    uuid.UUID("00000000-0000-7000-8000-000000000001"),
    "Demo villager",
    "sample_ozhar",
    frozenset({"villager"}),
)
DEV_VILLAGER_2 = UserInfo(
    uuid.UUID("00000000-0000-7000-8000-000000000002"),
    "Second villager",
    "sample_ozhar",
    frozenset({"villager"}),
)
DEV_OFFICER = UserInfo(  # a role this module does not serve
    uuid.UUID("00000000-0000-7000-8000-000000000009"),
    "Sub-divisional officer",
    None,
    frozenset({"sdo"}),
)


class StaticDirectory:
    def __init__(self, users: list[UserInfo]) -> None:
        self._users = {u.id: u for u in users}

    def get(self, user_id: uuid.UUID) -> UserInfo | None:
        return self._users.get(user_id)


def get_directory() -> UserDirectory:
    if get_settings().livelihood_dev_users:
        return StaticDirectory([DEV_VILLAGER, DEV_VILLAGER_2, DEV_OFFICER])
    return EmptyDirectory()


def create_access_token(user_id: uuid.UUID, *, minutes: int | None = None) -> str:
    """Mint a token in the host's format. For development scripts and tests only."""
    settings = get_settings()
    issued = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": issued,
        "exp": issued
        + timedelta(minutes=settings.access_token_minutes if minutes is None else minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "type", "exp"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise ApiError(401, "TOKEN_EXPIRED", "auth.token_expired") from exc
    except jwt.PyJWTError as exc:
        raise ApiError(401, "TOKEN_INVALID", "auth.token_invalid") from exc
    if payload.get("type") != "access":
        raise ApiError(401, "TOKEN_INVALID", "auth.token_invalid")
    try:
        return uuid.UUID(payload["sub"])
    except ValueError as exc:
        raise ApiError(401, "TOKEN_INVALID", "auth.token_invalid") from exc


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    directory: Annotated[UserDirectory, Depends(get_directory)],
) -> UserInfo:
    if creds is None:
        raise ApiError(401, "NOT_AUTHENTICATED", "auth.required")
    user = directory.get(decode_access_token(creds.credentials))
    if user is None:
        raise ApiError(401, "NOT_AUTHENTICATED", "auth.required")
    if not (user.roles & ALLOWED_ROLES):
        raise ApiError(403, "FORBIDDEN", "livelihood.role_not_allowed")
    return user
