from langchain.globals import set_verbose
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, scenarios, tts_stt
import logging

logging.basicConfig(level=logging.INFO)

set_verbose(True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (including "OPTIONS")
    allow_headers=["*"],  # Allow all headers
)

app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(scenarios.router, prefix="/api/v1/scenarios")
app.include_router(tts_stt.router, prefix="/api/v1/tts_stt")