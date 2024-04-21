import functools
import logging
import jwt

from datetime import timezone
from fastapi import Depends, HTTPException
from jwt.exceptions import PyJWTError
from datetime import datetime, timedelta
from .settings import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from .globals import oauth2_scheme, user_manager



def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e

    user = user_manager.get_user_by_email(email)
    if user is None:
        logging.error("User not found")
        raise HTTPException(status_code=404, detail="User not found")
    return user


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def has_role(allowed_roles: list = ["user"]):
    if not isinstance(allowed_roles, list):
        raise ValueError("allowed_roles must be a string, list, or set")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token = kwargs.get("token")
            if not token:
                raise HTTPException(
                    status_code=401, detail="No authentication token provided"
                )
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                role = payload.get("role")
                if role not in allowed_roles:
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )
            except PyJWTError:
                raise HTTPException(
                    status_code=401, detail="Invalid authentication token"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator