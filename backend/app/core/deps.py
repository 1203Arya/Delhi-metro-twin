from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import async_session_factory
from .exceptions import UnauthorizedError
from .security import decode_token


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_current_user(
    authorization: str = Header(default="", alias="Authorization"),
) -> dict[str, Any]:
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ")
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedError("Invalid or expired token")
    return payload


async def get_optional_user(
    authorization: str = Header(default="", alias="Authorization"),
) -> dict[str, Any] | None:
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ")
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    return payload


class Pagination:
    def __init__(self, skip: int = 0, limit: int = 100) -> None:
        self.skip = skip
        self.limit = limit


async def get_pagination(skip: int = 0, limit: int = 100) -> Pagination:
    return Pagination(skip=skip, limit=min(limit, 500))
