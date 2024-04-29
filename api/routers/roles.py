from fastapi import APIRouter, Depends, HTTPException
from api.models import RoleInput, RoleUpdateInput
from api.auth import has_role
from api.globals import role_manager, oauth2_scheme

router = APIRouter()

@router.post("/")
@has_role(allowed_roles=["admin"])
def add_role(data: RoleInput, token: str = Depends(oauth2_scheme)):
    if role_manager.read_role(data.name):
        raise HTTPException(status_code=400, detail="Role already exists")

    role_manager.create_role(data.name, data.prompt)
    return {"status": "Role Successfully Added!"}
   
    

@router.get("/")
@has_role(allowed_roles=["user", "admin"])
def get_roles(token: str = Depends(oauth2_scheme)):
    roles = role_manager.get_all_roles()
    return {"roles": [{"name": role.name} for role in roles]}


@router.get("/{name}")
@has_role(allowed_roles=["user", "admin"])
def get_role(name: str, token: str = Depends(oauth2_scheme)):
    if role := role_manager.read_role(name):
        return {"role": {"name": role.name, "prompt" : role.prompt_prefix}}
    else:
        raise HTTPException(status_code=404, detail="Role not found")
    

@router.put("/{name}")
@has_role(allowed_roles=["admin"])
def update_role(name: str, data: RoleUpdateInput, token: str = Depends(oauth2_scheme)):
    if not role_manager.read_role(name):
        raise HTTPException(status_code=400, detail="Role does not exist")

    if role_manager.read_role(data.new_name) and data.new_name != name:
        raise HTTPException(status_code=400, detail="Role with new name already exists")

    role_manager.update_role(name, data.new_name)
    return {"status": "Role Successfully Updated!"}


@router.delete("/{name}")
@has_role(allowed_roles=["admin"])
def delete_role(name: str, token: str = Depends(oauth2_scheme)):
    if not role_manager.read_role(name):
        raise HTTPException(status_code=400, detail="Role does not exist")
    
    role_manager.delete_role(name)
    return {"status": "Role Successfully Deleted!"}
  


