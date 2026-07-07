from __future__ import annotations

import hashlib
from typing import Any

from ..core.exceptions import UnauthorizedError
from ..core.security import create_access_token, create_refresh_token

DEMO_USER = "admin"
DEMO_PASS_HASH = hashlib.sha256(b"admin").hexdigest()


class AuthService:
    async def login(self, username: str, password: str) -> dict[str, Any]:
        if username != DEMO_USER:
            raise UnauthorizedError("Invalid username or password")
        check_hash = hashlib.sha256(password.encode()).hexdigest()
        if check_hash != DEMO_PASS_HASH:
            raise UnauthorizedError("Invalid username or password")
        return {
            "access_token": create_access_token(username, {"role": "admin"}),
            "refresh_token": create_refresh_token(username),
        }
