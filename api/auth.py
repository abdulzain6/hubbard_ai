import os
import jwt
from jwt.exceptions import PyJWTError
from fastapi import HTTPException, status
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

oauth2_scheme = HTTPBearer()


class UserInfo(BaseModel):
    user_id: str
    role: str
    
class UserInfo(BaseModel):
    user_id: str
    role: str
    first_name: str
    last_name: str
    email: str
    company_id: int
    company_name: str

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512', 'PS256', 'PS384', 'PS512'])
        return payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

def get_user_info(token_info: dict) -> UserInfo:
    user_id = str(token_info.get("id"))
    role = "admin" if token_info.get("roleId") == 1 else "user"
    first_name = token_info.get("first_name")
    last_name = token_info.get("last_name")
    email = token_info.get("email")
    company_id = token_info.get("company_id")
    company_name = token_info.get("company", {}).get("company_name")

    if not all([user_id, role, first_name, last_name, email, company_id, company_name]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user information in token",
        )
    
    return UserInfo(
        user_id=user_id,
        role=role,
        first_name=first_name,
        last_name=last_name,
        email=email,
        company_id=company_id,
        company_name=company_name
    )

def get_user_id_and_role(creds: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> UserInfo:
    payload = decode_token(creds.credentials)
    token_info = payload.get("tokenInfo")
    if token_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return get_user_info(token_info)

def get_admin_user(creds: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> UserInfo:
    user_info = get_user_id_and_role(creds)
    if user_info.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user_info

def get_regular_user(creds: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> UserInfo:
    user_info = get_user_id_and_role(creds)
    if user_info.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Regular user access required",
        )
    return user_info

async def get_current_user_id_and_role(creds: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> UserInfo:
    return await get_user_id_and_role(creds)
