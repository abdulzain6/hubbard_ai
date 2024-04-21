from fastapi import APIRouter, Depends, HTTPException, UploadFile
from api.auth import has_role, get_current_user
from api.globals import manager, oauth2_scheme, role_manager
from typing import Optional
from fastapi.responses import JSONResponse

from pydantic import BaseModel
from typing import Optional
import logging, shutil, tempfile
import os

router = APIRouter()


class ChatInput(BaseModel):
    question: str
    chat_history: list[tuple[str, str]]
    get_highest_ranking_response: bool
    temperature: int


class ChatResponse(BaseModel):
    ai_response: str
    error: str


@router.post("/chat", response_model=ChatResponse)
def chat(
    data: ChatInput,
    token: str = Depends(oauth2_scheme),
    current_user=Depends(get_current_user),
):
    if not (role := role_manager.read_role(current_user.company_role)):
        prefix = ""
    else:
        prefix = role.prompt_prefix

    @has_role(allowed_roles=["user", "admin"])
    def get_chat(token):
        try:
            error = ""
            ai_response = manager.chat(
                data.question,
                data.chat_history,
                temperature=data.temperature,
                get_highest_ranking_response=data.get_highest_ranking_response,
                prefix=prefix,
                role=current_user.company_role,
                department=current_user.department,
                company=current_user.company,
            )
            if not ai_response:
                raise HTTPException(status_code=400, detail="Chat operation failed")
        except Exception as e:
            logging.error(str(e))
            error = str(e)
            ai_response = ""

        return ChatResponse(ai_response=ai_response, error=error)

    resp = get_chat(token=token)
    return resp


@router.post("/injest_data")
@has_role(allowed_roles=["admin"])
def injest_data(
    text: Optional[str] = None,
    file: UploadFile = Optional[None],
    description: Optional[str] = None,
    token: str = Depends(oauth2_scheme),
) -> dict:
    if not text and not file:
        logging.error("Both text and file not sent")
        return JSONResponse(
            status_code=400, content={"detail": "Either provide text or file"}
        )
    if text and file:
        logging.error("Both text and file sent")
        return JSONResponse(
            status_code=400,
            content={"detail": "Either provide text or file, not both"},
        )

    if file:
        # Extract the extension from the original filename
        extension = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(suffix=extension, delete=True) as temp:
            shutil.copyfileobj(file.file, temp)
            temp.flush()  # make sure data is written to disk before ingesting
            manager.injest_data_api(file_path=temp.name, description=description)
    else:
        manager.injest_data_api(text=text, description=description)

    return {"status": "Data Successfully Ingested!"}
