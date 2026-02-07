from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt
from app.core.config import settings
import requests

# This is a skeleton for Auth0 integration.
# It currently doesn't do full validation but structures where it should go.

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://{settings.AUTH0_DOMAIN}/authorize",
    tokenUrl=f"https://{settings.AUTH0_DOMAIN}/oauth/token",
)

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        # real implementation would pull JWKS and verify
        # for now, we just pass through or do basic check
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
