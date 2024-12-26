import base64
import logging, tempfile
import os
from fastapi import APIRouter, Body, Depends, HTTPException
from concurrent.futures import ThreadPoolExecutor, as_completed
from api.auth import UserInfo, get_admin_user
from api.globals import manager
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from api.lib.database import RoleManager, FileManager, FileModel

router = APIRouter()


class IngestModel(BaseModel):
    text: Optional[str] = None
    file: Optional[str] = None
    description: Optional[str] = None
    extension: Optional[str] = None
    weight: int = 1
    role: Optional[str] = None
  

@router.post("/ingest")
def ingest_data(
    file_name: str,
    data: IngestModel,
    user: UserInfo = Depends(get_admin_user)
) -> dict:
    
    file_manager = FileManager(user.user_id)
    role_manager = RoleManager()
    if data.role:
        role = role_manager.read_role(data.role)
        if not role:
            raise HTTPException(status_code=400, detail="Role not found.")


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
                vector_ids, content = manager.ingest_data_api(file_path=temp.name, weight=data.weight, role=data.role)
                file_manager.create_or_update_file(
                    FileModel(
                        file_name=file_name,
                        description=data.description,
                        content=content,
                        vector_ids=vector_ids
                    )
                )
        finally:
            if os.path.exists(temp.name):
                os.unlink(temp.name)  # Ensure the temp file is deleted
                logging.info(f"Temporary file {temp.name} deleted after ingestion")
    else:
        logging.info("Ingesting data from text input")
        vector_ids, content = manager.ingest_data_api(text=data.text, weight=data.weight, role=data.role)
        file_manager.create_or_update_file(
            FileModel(
                file_name=file_name,
                description=data.description,
                content=content,
                vector_ids=vector_ids
            )
        )

    return {"status": "Data Successfully Ingested!"}

@router.post("/{file_name}/metadata", response_model=Dict)
def update_metadata_endpoint(
    file_name: str, 
    metadata: Dict[str, Any] = Body(...), 
    user: UserInfo = Depends(get_admin_user)
):
    file_manager = FileManager(user_id=user.user_id)

    try:
        # Read the file to get the vector IDs
        file_data = file_manager.read_file(file_name=file_name)
        if not file_data:
            raise ValueError("File not found!")
            
        vector_ids = file_data.vector_ids
        # Update metadata for the vector IDs
        manager.update_metadata(ids=vector_ids, update_dict=metadata)

        return {"message": f"Metadata for file {file_name} updated successfully."}
    except Exception as e:
        print("Error: ", e)
        raise HTTPException(status_code=500, detail="An error occurred during the operation")
    
@router.get("/metadata", response_model=Dict)
def get_all_files_metadata(user: UserInfo = Depends(get_admin_user)):
    try:
        file_manager = FileManager(user_id=user.user_id)
        files = file_manager.get_all_files()

        def get_metadata(file: FileModel):
            vec_ids = file.vector_ids
            if not vec_ids:
                return None
            metadata = manager.get_file_metadata(vec_ids[0])
            return {"metadata": metadata, "filename": file.file_name}

        metadatas = []
        with ThreadPoolExecutor() as executor:
            future_to_file = {executor.submit(get_metadata, file): file for file in files}
            for future in as_completed(future_to_file):
                result = future.result()
                if result:
                    metadatas.append(result)
        return {"metadatas": metadatas}
    except Exception as e:
        logging.error(f"Error in get_all_files_metadata: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during the operation")

@router.get("/all", response_model=List[Dict])
def get_all_files(user: UserInfo = Depends(get_admin_user)):
    try:
        file_manager = FileManager(user_id=user.user_id)
        files = file_manager.get_all_files()
        return [file.model_dump(exclude=["content", "vector_ids"]) for file in files]
    except Exception as e:
        logging.error(f"Failed to retrieve files: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve files")

@router.delete("/{file_name}", response_model=Dict)
def delete_file(file_name: str, user: UserInfo = Depends(get_admin_user)):
    try:
        file_manager = FileManager(user_id=user.user_id)

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
