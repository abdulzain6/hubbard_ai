from langchain.globals import set_verbose
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, scenarios, tts_stt, roles, files, voice_chat
from .middleware.error_handler import TracebackMiddleware
import logging, mangum, uvicorn

logging.basicConfig(level=logging.INFO)

set_verbose(True)

app = FastAPI()

app.add_middleware(TracebackMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(scenarios.router, prefix="/api/v1/scenarios")
app.include_router(tts_stt.router, prefix="/api/v1/tts_stt")
app.include_router(roles.router, prefix="/api/v1/roles")
app.include_router(files.router, prefix="/api/v1/files")
app.include_router(voice_chat.app, prefix="/api/v1/voice-ai")

mangum_app = mangum.Mangum(app=app)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="./key.pem",
        ssl_certfile="./aacert.pem"
    )
