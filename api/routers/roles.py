from fastapi import APIRouter, Depends, HTTPException
from api.models import RoleInput, RoleUpdateInput
from api.auth import get_user_id_and_role, UserInfo
from api.lib.database import RoleManager, RoleModel


router = APIRouter()


@router.post("/")
def add_role(data: RoleInput, user: UserInfo = Depends(get_user_id_and_role)):
    role_manager = RoleManager()

    if role_manager.read_role(data.name):
        raise HTTPException(status_code=400, detail="Role already exists")

    role_manager.create_or_update_role(
        RoleModel(
            name=data.name,
            prompt_prefix=data.prompt
        )
    )
    return {"status": "Role Successfully Added!"}    

@router.get("/")
def get_roles(user: UserInfo = Depends(get_user_id_and_role)):
    role_manager = RoleManager()
    roles = role_manager.get_all_roles()
    return {"roles": [{"name": role.name, "prompt" : role.prompt_prefix} for role in roles]}


@router.get("/{name}")
def get_role(name: str, user: UserInfo = Depends(get_user_id_and_role)):
    role_manager = RoleManager()
    if role := role_manager.read_role(name):
        return {"role": {"name": role.name, "prompt" : role.prompt_prefix}}
    else:
        raise HTTPException(status_code=404, detail="Role not found")
    

@router.put("/{name}")
def update_role(name: str, data: RoleUpdateInput, user: UserInfo = Depends(get_user_id_and_role)):
    role_manager = RoleManager()
    if not role_manager.read_role(name):
        raise HTTPException(status_code=400, detail="Role does not exist")

    role_manager.create_or_update_role(
        RoleModel(
            prompt_prefix=data.prompt_prefix,
            name=name
        )
    )
    return {"status": "Role Successfully Updated!"}


@router.delete("/{name}")
def delete_role(name: str, user: UserInfo = Depends(get_user_id_and_role)):
    role_manager = RoleManager()

    if not role_manager.read_role(name):
        raise HTTPException(status_code=400, detail="Role does not exist")
    
    role_manager.delete_role(name)
    return {"status": "Role Successfully Deleted!"}
