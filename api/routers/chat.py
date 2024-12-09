import logging
import queue
import threading

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from api.auth import UserInfo, get_user_id_and_role
from api.globals import manager, GLOBAL_MODEL
from pydantic import BaseModel
from typing import Generator, Optional
from api.lib.ai import CustomCallback, split_into_chunks
from api.lib.database import RoleManager

router = APIRouter()


class ChatInput(BaseModel):
    question: str
    chat_history: list[tuple[str, str]]
    role: Optional[str] = None

class ChatResponse(BaseModel):
    ai_response: str
    error: str
  
  
@router.post("/chat-stream")
def chat(
    data: ChatInput,
    background_tasks: BackgroundTasks,
    user: UserInfo = Depends(get_user_id_and_role)
):
    role_manager = RoleManager()

    if data.role:
        role = role_manager.read_role(data.role)
        if not role:
            raise HTTPException(status_code=400, detail="Role not found.")
        prefix = role.prompt_prefix
    else:
        prefix = ""
        
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

