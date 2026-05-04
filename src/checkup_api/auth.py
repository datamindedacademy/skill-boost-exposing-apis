"""
Authentication and authorization utilities.
"""

from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

KEYCLOAK_JWKS_URL = "http://localhost:8080/realms/checkup/protocol/openid-connect/certs"

security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """
    Validate JWT token and return user claims.

    Fetches Keycloak's JWKS, verifies signature + expiration, returns claims.
    The `products` claim is what you'll use in `get_allowed_products`.
    """

    token = credentials.credentials

    try:
        jwks = httpx.get(KEYCLOAK_JWKS_URL).raise_for_status().json()
        return jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience="account",
            options={"verify_aud": True, "verify_exp": True},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not validate token: auth service unavailable",
        )


def get_allowed_products(user: Annotated[dict, Depends(get_current_user)]) -> list[str]:
    """
    Return the list of product slugs this caller may access.

    TODO: The JWT contains a `products` claim, a list of product slugs. The `*` scope means access to all products.
    """

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Exercise 4: implement get_allowed_products",
    )
