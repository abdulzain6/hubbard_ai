import base64
import mimetypes
import magic
import logging, tempfile
import os

from fastapi import APIRouter, Body, Depends, HTTPException
from api.auth import has_role, get_current_user
from api.globals import manager, oauth2_scheme, role_manager, file_manager
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter()


class ChatInput(BaseModel):
    question: str
    chat_history: list[tuple[str, str]]
    get_highest_ranking_response: bool
    role: str

class ChatResponse(BaseModel):
    ai_response: str
    error: str

class InjestModel(BaseModel):
    text: Optional[str] = None
    file: Optional[str] = None
    description: Optional[str] = None
    extension: Optional[str] = None
    weight: Optional[int] = 1
    
@router.post("/chat", response_model=ChatResponse)
def chat(
    data: ChatInput,
    token: str = Depends(oauth2_scheme),
    current_user=Depends(get_current_user),
):
    if not (role := role_manager.read_role(data.role)):
        raise HTTPException(404, detail="Role not found")
    else:
        prefix = role.prompt_prefix

    @has_role(allowed_roles=["user", "admin"])
    def get_chat(token):
        try:
            error = ""
            ai_response = manager.chat(
                data.question,
                data.chat_history,
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
    data: InjestModel,
    token: str = Depends(oauth2_scheme),
) -> dict:
    if not data.text and not data.file:
        logging.error("Both text and file not provided")
        raise HTTPException(status_code=400, detail="Either provide text or file")
    
    tmpfile = file_manager.read_file(file_name=file_name)
    if tmpfile:
        raise HTTPException(status_code=404, detail="File already exists")

    if data.text and data.file:
        logging.error("Both text and file provided")
        raise HTTPException(status_code=400, detail="Either provide text or file, not both")

    if data.file:
        try:
            file_data = base64.b64decode(data.file)
        except base64.binascii.Error as e:
            logging.error(f"Base64 decoding failed: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid base64 data")

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=data.extension) as temp:
                temp.write(file_data)
                temp.flush()
                logging.info(f"File saved temporarily as {temp.name} for ingestion")
                vector_ids, content = manager.injest_data_api(file_path=temp.name)
                file_manager.create_file(file_name=file_name, description=data.description, content=content, vector_ids=vector_ids)
        finally:
            if os.path.exists(temp.name):
                os.unlink(temp.name)  # Ensure the temp file is deleted
                logging.info(f"Temporary file {temp.name} deleted after ingestion")
    else:
        logging.info("Ingesting data from text input")
        vector_ids, content = manager.injest_data_api(text=data.text)
        file_manager.create_file(file_name=file_name, description=data.description, content=content, vector_ids=vector_ids)

    return {"status": "Data Successfully Ingested!"}

@router.post("/files/{file_name}", response_model=Dict)
@has_role(allowed_roles=["admin"])
def update_metadata_endpoint(file_name: str, metadata: Dict[str, Any] = Body(...), token: str = Depends(oauth2_scheme)):
    try:
        # Read the file to get the vector IDs
        file_data = file_manager.read_file(file_name=file_name)
        if not file_data:
            raise ValueError("File not found!")
            
        vector_ids = file_data.vector_ids
        print(vector_ids) #Influence_ The Psychology of Persuasion.epub

        # Update metadata for the vector IDs
        manager.update_metadata(ids=vector_ids, update_dict=metadata)

        return {"message": f"Metadata for file {file_name} updated successfully."}
    except Exception as e:
        print("Error: ", e)
        raise HTTPException(status_code=500, detail="An error occurred during the operation")
    
@router.get("/files-metadata/", response_model=Dict)
@has_role(allowed_roles=["admin"])
def get_all_files_metadata(token: str = Depends(oauth2_scheme)):
    try:
        metadatas = []
        files = file_manager.get_all_files()
        for file in files:
            vec_ids = file.get("vector_ids", [])
            if not vec_ids:
                continue
            else:
                metadata = manager.get_file_metadata(vec_ids[0])
                metadatas.append(
                    {"metadata" : metadata, "filename" : file["file_name"]}
                )
        return {"metadatas" : metadatas}
    except Exception as e:
        print("Error: ", e)
        raise HTTPException(status_code=500, detail="An error occurred during the operation")

@router.get("/files", response_model=List[Dict])
@has_role(allowed_roles=["admin"])
def get_all_files(token: str = Depends(oauth2_scheme)):
    try:
        files: list[dict] = file_manager.get_all_files()
        for file in files:
            file.pop("content", "")
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
