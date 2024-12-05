from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserInfo(BaseModel):
    user_id: str
    role: str
    
def get_user_id_and_role(token: str = Depends(oauth2_scheme)) -> UserInfo:
    return UserInfo(user_id="test_user_id", role="user")

async def get_current_user_id_and_role(token: str = Depends(oauth2_scheme)) -> UserInfo:
    return await get_user_id_and_role(token)
