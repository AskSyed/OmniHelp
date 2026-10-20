"""
JWT bearer authentication and scope-based authorization

In production an identity provider (Azure AD, Okta, Ping...) issues RS256 tokens and this
service verifies them against the provider's JWKS endpoint. HS256 with a shared secret
keeps the playground self-contained; the verification rules are the same.
"""
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    """The authenticated caller"""
    subject: str
    scopes: frozenset = frozenset()
    authenticated: bool = True


# Used when AUTH_ENABLED is false (local dev): every scope is granted
ANONYMOUS = Principal(subject="anonymous", scopes=frozenset({"*"}), authenticated=False)


def _signing_key() -> str:
    if settings.JWT_SECRET is None:
        raise RuntimeError("JWT_SECRET is not configured")
    return settings.JWT_SECRET.get_secret_value()


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_access_token(
    subject: str,
    scopes: List[str],
    expires_in: timedelta = timedelta(minutes=15)
) -> str:
    """
    Mint a short-lived access token (dev and tests only)

    Args:
        subject: User or client ID the token is issued to
        scopes: Permissions granted, e.g. ["query:read"]
        expires_in: Token lifetime

    Returns:
        Encoded JWT
    """
    now = datetime.now(timezone.utc)
    claims = {
        "sub": subject,
        "scope": " ".join(scopes),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(claims, _signing_key(), algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Principal:
    """
    Verify a token's signature and claims

    Raises:
        HTTPException: 401 if the token is expired, tampered with, or not meant for this API
    """
    try:
        claims = jwt.decode(
            token,
            _signing_key(),
            # Pin the algorithm: never trust the token's own "alg" header (blocks alg=none)
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token has expired")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid token")

    return Principal(subject=claims["sub"], scopes=frozenset(claims.get("scope", "").split()))


async def get_current_principal(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Principal:
    """FastAPI dependency: resolve the caller from the Authorization header"""
    if not settings.AUTH_ENABLED:
        return ANONYMOUS
    if credentials is None:
        raise _unauthorized("Missing bearer token")
    return decode_access_token(credentials.credentials)


def require_scope(scope: str):
    """
    Build a dependency that rejects callers without the given scope

    Usage:
        @router.post("", dependencies=[Depends(require_scope("query:read"))])
    """
    async def checker(principal: Principal = Depends(get_current_principal)) -> Principal:
        if "*" not in principal.scopes and scope not in principal.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}"
            )
        return principal

    return checker


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mint a dev access token")
    parser.add_argument("subject")
    parser.add_argument("scopes", nargs="*", default=["query:read"])
    parser.add_argument("--minutes", type=int, default=60)
    args = parser.parse_args()
    print(create_access_token(args.subject, args.scopes, timedelta(minutes=args.minutes)))
