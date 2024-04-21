import logging

from fastapi import APIRouter, Depends, HTTPException
from api.models import PromptInput, PromptNameInput, PromptUpdateInput
from api.auth import has_role
from api.globals import oauth2_scheme, prompt_handler

router = APIRouter()


@router.post("/create_prompt")
@has_role(allowed_roles=["admin"])
def create_prompt(data: PromptInput, token: str = Depends(oauth2_scheme)):
    if data.is_main and prompt_handler.get_main_prompt():
        raise HTTPException(status_code=400, detail="Main prompt already exists!")
    
    if prompt_handler.get_prompt_by_name(data.name):
        raise HTTPException(status_code=400, detail="Prompt already exists!")

    
    if not prompt_handler.validate_prompt(data.prompt):
        raise HTTPException(status_code=400, detail="Prompt must contain the following variables in {}: " + ", ".join([
            "insights", "human_question", "data", "chat_history", "role", "job", "company", "department", "company_role", "prompt_prefix"
        ]))
        
    prompt_handler.create_prompt(data.name, data.is_main, data.prompt)
    return {"status": "Prompt Successfully Created!"}



@router.post("/choose_main_prompt")
@has_role(allowed_roles=["admin"])
def choose_main_prompt(data: PromptNameInput, token: str = Depends(oauth2_scheme)):
    if not prompt_handler.get_prompt_by_name(data.name):
        logging.error("prompt not found")
        raise HTTPException(status_code=400, detail="prompt not found")

    prompt_handler.choose_main_prompt(data.name)
    return {"status": "Main Prompt Successfully Set!"}




@router.post("/update_prompt/{name}")
@has_role(allowed_roles=["admin"])
def update_prompt(name: str, data: PromptUpdateInput, token: str = Depends(oauth2_scheme)):
    if not prompt_handler.get_prompt_by_name(name):
        logging.error("prompt not found")
        raise HTTPException(status_code=400, detail="prompt not found")

    if not prompt_handler.validate_prompt(data.content):
            raise HTTPException(status_code=400, detail="Prompt must contain the following variables in {}: " + ", ".join([
                "insights", "human_question", "data", "chat_history", "role", "job"
            ]))
            
    attributes = data.dict(exclude_unset=True)
    prompt_handler.update_prompt(name, attributes)
    return {"status": "Prompt Successfully Updated!"}


@router.post("/list_prompts")
@has_role(allowed_roles=["admin"])
def list_prompts(token: str = Depends(oauth2_scheme)):
    prompts = prompt_handler.get_all_prompts()
    return {"prompts": prompts}

        

@router.delete("/delete_prompt/{name}")
@has_role(allowed_roles=["admin"])
def delete_prompt(name: str, token: str = Depends(oauth2_scheme)):
    prompt = prompt_handler.get_prompt_by_name(name)
    if not prompt:
        logging.error("Prompt not found")
        raise HTTPException(status_code=404, detail="Prompt not found")

    if prompt.is_main:
        logging.error("Main prompt cannot be deleted")
        raise HTTPException(status_code=400, detail="Main prompt cannot be deleted")

    prompt_handler.delete_prompt(name)
    return {"status": "Prompt Successfully Deleted!"}

