import base64
import mimetypes
import magic
import logging, tempfile
import os

from fastapi import APIRouter, Depends, HTTPException
from api.auth import has_role, get_current_user
from api.globals import manager, oauth2_scheme, role_manager, file_manager
from pydantic import BaseModel
from typing import Dict, List, Optional

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
    file_name: str,
    text: Optional[str] = None,
    file: Optional[str] = None,
    description: Optional[str] = None,
    token: str = Depends(oauth2_scheme),
) -> dict:
    if not text and not file:
        logging.error("Both text and file not provided")
        raise HTTPException(status_code=400, detail="Either provide text or file")
    
    tmpfile = file_manager.read_file(file_name=file_name)
    if tmpfile:
        raise HTTPException(status_code=404, detail="File already exists")

    if text and file:
        logging.error("Both text and file provided")
        raise HTTPException(status_code=400, detail="Either provide text or file, not both")

    if file:
        try:
            file_data = base64.b64decode(file)
        except base64.binascii.Error as e:
            logging.error(f"Base64 decoding failed: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid base64 data")

        # Use python-magic to determine the file type
        mime_type = magic.Magic(mime=True)
        content_type = mime_type.from_buffer(file_data)
        extension = mimetypes.guess_extension(content_type) or '.unknown'  # Fallback if no extension is guessed

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp:
                temp.write(file_data)
                temp.flush()
                logging.info(f"File saved temporarily as {temp.name} with detected type {content_type} for ingestion")
                vector_ids, content = manager.injest_data_api(file_path=temp.name)
                file_manager.create_file(file_name=file_name, description=description, content=content, vector_ids=vector_ids)
        finally:
            if os.path.exists(temp.name):
                os.unlink(temp.name)  # Ensure the temp file is deleted
                logging.info(f"Temporary file {temp.name} deleted after ingestion")
    else:
        logging.info("Ingesting data from text input")
        vector_ids, content = manager.injest_data_api(text=text)
        file_manager.create_file(file_name=file_name, description=description, content=content, vector_ids=vector_ids)

    return {"status": "Data Successfully Ingested!"}


@router.get("/files", response_model=List[Dict])
@has_role(allowed_roles=["admin"])
def get_all_files(token: str = Depends(oauth2_scheme)):
    try:
        files = file_manager.get_all_files()
        return files
    except Exception as e:
        logging.error(f"Failed to retrieve files: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve files")

@router.delete("/files/{file_name}", response_model=Dict)
@has_role(allowed_roles=["admin"])
def delete_file(file_name: str, token: str = Depends(oauth2_scheme)):
    try:
        file = file_manager.read_file(file_name=file_name)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        manager.delete_ids(file.vector_ids)
        file_manager.delete_file(file_name)  # Ensure to delete after all dependent deletions
        return {"status": "success", "message": f"File '{file_name}' deleted successfully"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Failed to delete file '{file_name}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
