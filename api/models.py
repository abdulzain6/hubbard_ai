from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


class ScenarioCreateRequest(BaseModel):
    name: str
    description: str
    scenario_description: str
    best_response: str
    response_explanation: str
    difficulty: str  # New field
    importance: int  # New field

class ScenarioUpdateRequest(BaseModel):
    description: Optional[str] = None
    scenario_description: Optional[str] = None
    best_response: Optional[str] = None
    response_explanation: Optional[str] = None
    difficulty: Optional[str] = None  # New field
    importance: Optional[int] = None  # New field
    
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
    new_name: str
    
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
    
class FeedbackRequest(BaseModel):
    star: int
    review: str
    
class GenerateScenarioRequest(BaseModel):
    theme: str
    
class EvaluateScenarioRequest(BaseModel):
    scenario_name: str
    salesman_response: str
