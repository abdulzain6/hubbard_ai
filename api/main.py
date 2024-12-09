from langchain.globals import set_verbose
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, scenarios, tts_stt, roles, files, voice_chat
import logging, mangum

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
app.include_router(roles.router, prefix="/api/v1/roles")
app.include_router(files.router, prefix="/api/v1/files")
app.include_router(voice_chat.app, prefix="/api/v1/voice-ai")

mangum_app = mangum.Mangum(app=app)
