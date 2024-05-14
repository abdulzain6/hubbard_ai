from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

    
class PromptInput(BaseModel):
    prompt: str
    name: str
    is_main: bool

class PromptNameInput(BaseModel):
    name: str
    
class PromptUpdateInput(BaseModel):
    content: str

class DepartmentUpdateInput(BaseModel):
    new_name: str
    
class RoleUpdateInput(BaseModel):
    prompt_prefix: str
    
class User(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    country: str
    phone: str
    company_role: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None


    @validator("password")
    def validate_password(cls, password):
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        return password
    
class UserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=8)
    name: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    company_role: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None


    @validator("password")
    def validate_password(cls, password: Optional[str]) -> Optional[str]:
        if password:
            if not any(char.isupper() for char in password):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(char.islower() for char in password):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(char.isdigit() for char in password):
                raise ValueError("Password must contain at least one digit")
        return password
    
class RoleInput(BaseModel):
    name: str
    prompt: str
