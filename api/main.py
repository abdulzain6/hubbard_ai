from langchain.globals import set_verbose
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from .settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from .globals import user_manager
from .auth import create_access_token
from .routers import users, prompts, chat, roles, scenarios, responses, tts_stt
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

app.include_router(users.router, prefix="/api/v1/users")
app.include_router(prompts.router, prefix="/api/v1/prompts")
app.include_router(roles.router, prefix="/api/v1/roles")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(scenarios.router, prefix="/api/v1/scenarios")
app.include_router(responses.router, prefix="/api/v1/responses")
app.include_router(tts_stt.router, prefix="/api/v1/tts_stt")


@app.post("/token")
def login_for_access_token(user_data: OAuth2PasswordRequestForm = Depends()):
    user = user_manager.get_user_by_email(user_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user_manager.verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    role = user.role
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


