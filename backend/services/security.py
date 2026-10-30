import os

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from functools import wraps

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token", auto_error=False)


def current_user(token: str | None = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to access this information")
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError as error:
        raise HTTPException(status_code=401, detail="Your session has expired; sign in again") from error


def business_access(business_id: str, user=Depends(current_user)):
    if user.get("business_id") != business_id and user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="You cannot access this business")
    return user


def require_roles(*roles):
    def check(business_id: str, user=Depends(current_user)):
        business_access(business_id, user)
        if user.get("role") not in roles and user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Your account does not have permission for this action")
        return user
    return check
