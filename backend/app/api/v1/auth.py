from __future__ import annotations

from fastapi import APIRouter, Depends

from ...schemas import LoginRequest, TokenResponse
from ...services import AuthService

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    svc = AuthService()
    tokens = await svc.login(body.username, body.password)
    return TokenResponse(**tokens)
