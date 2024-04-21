import logging
import jwt

from fastapi import APIRouter, Depends, HTTPException
from api.models import User, UserUpdate
from api.settings import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from api.globals import user_manager, oauth2_scheme
from api.auth import get_current_user
from peewee import IntegrityError

router = APIRouter()


@router.post("/register")
def register_user(user: User):
    try:
        validated_password = User.validate_password(user.password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if existing_user := user_manager.get_user_by_email(user.email):
        return {"status": "User already exists!"}

    try:
        user_manager.create_new_user(**user.model_dump(), role="user")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"status": "User Successfully Created!"}

@router.get("/", dependencies=[Depends(oauth2_scheme)])
def get_user(current_user = Depends(get_current_user)):
    return current_user.dict()


@router.post("/register_admin", dependencies=[Depends(oauth2_scheme)])
def register_admin(user: User, token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    current_role = payload.get("role")

    if current_role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        validated_password = User.validate_password(user.password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if existing_user := user_manager.get_user_by_email(user.email):
        return {"status": "User already exists!"}

    try:
        user_manager.create_new_user(**user.model_dump(), role="admin")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"status": "Admin Successfully Created!"}


@router.delete("/delete_user/{email}", dependencies=[Depends(oauth2_scheme)])
def delete_user(email: str, token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    current_user = payload.get("sub")
    current_role = payload.get("role")
    if current_user != email and current_role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    user_manager.delete_user(email)
    return {"status": "User Successfully Deleted!"}


@router.post("/update_user/{old_email}", dependencies=[Depends(oauth2_scheme)])
def update_user(
    old_email: str,
    request: UserUpdate,
    current_user = Depends(get_current_user)
) -> dict[str, str]:
    try:
        # Ensure that only the authenticated user can edit their own details, unless they are an admin
        if current_user.email != old_email and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # If attempting to update the role, ensure that the current user is an admin
        if request.role is not None and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can edit roles")

        attributes = request.model_dump(exclude_unset=True)
        user_manager.update_user(old_email, attributes)
        return {"status": "User Successfully Updated!"}
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Email already in use") from e






