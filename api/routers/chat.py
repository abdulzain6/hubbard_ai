import base64
import logging, tempfile
import queue
import os
import threading

from fastapi import APIRouter, Body, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from api.auth import UserInfo, get_user_id_and_role
from api.globals import manager, GLOBAL_MODEL
from pydantic import BaseModel
from typing import Any, Dict, Generator, List, Optional
from api.lib.ai import CustomCallback, split_into_chunks
from api.lib.database import RoleManager, FileManager, FileModel

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
    weight: int = 1
    role: Optional[str] = None
  
  
  
@router.post("/chat-stream")
def chat(
    data: ChatInput,
    background_tasks: BackgroundTasks,
    user: UserInfo = Depends(get_user_id_and_role)
):
    role_manager = RoleManager()

    if not (role := role_manager.read_role(data.role)) and role:
        raise HTTPException(404, detail="Role not found")
    else:
        prefix = role.prompt_prefix
        
    print("Chosen role: ", data.role)
    data_queue = queue.Queue(maxsize=-1)

    def data_generator() -> Generator[str, None, None]:
        while True:
            try:
                data = data_queue.get(timeout=60)
                if data is None:
                    break
                yield data
            except queue.Empty:
                break

    def callback(data: str) -> None:
        data_queue.put(data)

    def on_end_callback(response: str) -> None:
        pass
            
    def get_chat():
        try:
            ai_response = manager.chat_stream(
                question=data.question,
                chat_history=data.chat_history,
                get_highest_ranking_response=data.get_highest_ranking_response,
                prefix=prefix,
                role=data.role,
                llm=ChatOpenAI(model=GLOBAL_MODEL, temperature=0.5, streaming=True, callbacks=[CustomCallback(callback=callback, on_end_callback=on_end_callback)])
            )
            if ai_response:
                callback(ai_response)
            callback(None)
        except Exception as e:
            logging.error(f"Error running chat in chat_file_stream: {e}")
            error_message = "Error in getting response"
            for chunk in split_into_chunks(error_message, 4):
                callback(chunk)
            callback(None)

    threading.Thread(target=get_chat).start()

    return StreamingResponse(data_generator())

@router.post("/injest_data")
def injest_data(
    file_name: str,
    data: InjestModel,
    user: UserInfo = Depends(get_user_id_and_role)
) -> dict:
    
    file_manager = FileManager(user.user_id)

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
                vector_ids, content = manager.injest_data_api(file_path=temp.name, weight=data.weight, role=data.role)
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
        vector_ids, content = manager.injest_data_api(text=data.text, weight=data.weight, role=data.role)
        file_manager.create_or_update_file(
            FileModel(
                file_name=file_name,
                description=data.description,
                content=content,
                vector_ids=vector_ids
            )
        )

    return {"status": "Data Successfully Ingested!"}

@router.post("/files/{file_name}", response_model=Dict)
def update_metadata_endpoint(
    file_name: str, 
    metadata: Dict[str, Any] = Body(...), 
    user: UserInfo = Depends(get_user_id_and_role)
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
    
@router.get("/files-metadata/", response_model=Dict)
def get_all_files_metadata(user: UserInfo = Depends(get_user_id_and_role)):
    try:
        file_manager = FileManager(user_id=user.user_id)
        metadatas = []
        files = file_manager.get_all_files()
        for file in files:
            vec_ids = file.vector_ids
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
def get_all_files(user: UserInfo = Depends(get_user_id_and_role)):
    try:
        file_manager = FileManager(user_id=user.user_id)
        files = file_manager.get_all_files()
        return [file.model_dump(exclude=["content", "vector_ids"]) for file in files]
    except Exception as e:
        logging.error(f"Failed to retrieve files: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve files")

@router.delete("/files/{file_name}", response_model=Dict)
def delete_file(file_name: str, user: UserInfo = Depends(get_user_id_and_role)):
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
