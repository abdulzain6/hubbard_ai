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
from api.lib.database import RoleManager, ChatHistoryManager, ChatHistoryModel
from langchain_core.messages import HumanMessage
from langchain.pydantic_v1 import BaseModel as V1BaseModel

router = APIRouter()


class ChatInput(BaseModel):
    question: str
    chat_history: list[tuple[str, str]] | None = None
    role: Optional[str] = None
    chat_session_id: str | None = None


class ChatResponse(BaseModel):
    ai_response: str
    error: str


class Topic(V1BaseModel):
    topic: str


@router.get("/chat-history/{chat_session_id}")
def get_chat_history(
    chat_session_id: str, user: UserInfo = Depends(get_user_id_and_role)
):
    chat_manager = ChatHistoryManager()
    conversation = chat_manager.get_conversation(chat_session_id, user.user_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Chat history not found")
    return conversation


@router.get("/chat-history/")
def get_user_chat_history(user: UserInfo = Depends(get_user_id_and_role)):
    chat_manager = ChatHistoryManager()
    conversations = chat_manager.get_user_conversations(user.user_id)
    return [conv.model_dump(exclude=["chat_history"]) for conv in conversations]


@router.delete("/chat-history/{chat_session_id}")
def delete_chat_history(
    chat_session_id: str, user: UserInfo = Depends(get_user_id_and_role)
):
    try:
        chat_manager = ChatHistoryManager()
        chat_manager.delete_conversation(chat_session_id, user.user_id)
        return {"message": "Chat history deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat-stream")
def chat(
    data: ChatInput,
    background_tasks: BackgroundTasks,
    user: UserInfo = Depends(get_user_id_and_role),
):
    role_manager = RoleManager()
    chat_manager = ChatHistoryManager()

    if data.role:
        role = role_manager.read_role(data.role)
        if not role:
            raise HTTPException(status_code=400, detail="Role not found.")
        prefix = role.prompt_prefix
    else:
        prefix = ""

    convo_exists = False
    if data.chat_session_id:
        conversation = chat_manager.get_conversation(data.chat_session_id, user.user_id)
        if conversation:
            convo_exists = True
            chat_history = conversation.chat_history
        else:
            chat_history = []
    else:
        chat_history = data.chat_history if data.chat_history else []

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
        if not convo_exists and data.chat_session_id:
            topic = (
                ChatOpenAI(model=GLOBAL_MODEL, temperature=0.5)
                .with_structured_output(schema=Topic)
                .invoke(
                    [
                        HumanMessage(
                            content=f"""Generate a chat topic, based on the following conversation:
                    Human: {data.question}
                    AI: {response}
                    """
                        )
                    ]
                )
            )
            chat_manager.create_or_update_conversation(
                ChatHistoryModel(
                    chat_session_id=data.chat_session_id,
                    user_id=user.user_id,
                    topic=topic.topic,
                    chat_history=[(data.question, response)],
                )
            )

        elif convo_exists and data.chat_session_id:
            chat_manager.add_message(
                data.chat_session_id,
                user_id=user.user_id,
                human_message=data.question,
                ai_message=response,
            )

    def get_chat():
        try:
            ai_response = manager.chat_stream(
                question=data.question,
                chat_history=chat_history,
                prefix=prefix,
                role=data.role,
                llm=ChatOpenAI(
                    model=GLOBAL_MODEL,
                    temperature=0.5,
                    streaming=True,
                    callbacks=[
                        CustomCallback(
                            callback=callback, on_end_callback=on_end_callback
                        )
                    ],
                ),
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
