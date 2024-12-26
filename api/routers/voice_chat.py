import os
import traceback
from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials

from ..auth import get_user_id_and_role
from ..lib.voice_mode import OpenAIHandler
from ..lib.prompt import DEFAULT_PROMPT_VOICE, STARTER_MESSAGE
import json
import base64
import asyncio


app = APIRouter()

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    print("Client connected")
    await websocket.accept()
    try:

        try:
            message = await websocket.receive_json()
            if 'token' not in message:
                await websocket.close(code=4000)
                return

            token = message['token']
            user = get_user_id_and_role(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            await websocket.send_json({"error" : f"auth error {e}"})
            await websocket.close(code=4001)
            return

        print("Authentication Successful")
        openai_handler = OpenAIHandler(
            voice="alloy",
            system_message=DEFAULT_PROMPT_VOICE,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            start_message=STARTER_MESSAGE
        )
        await openai_handler.connect()

        async def receive_audio_from_user():
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if openai_handler.ws.open:
                        await openai_handler.send_audio(data['payload'])
            except WebSocketDisconnect:
                print("Client disconnected.")
                await openai_handler.close()

        async def send_audio_to_user():
            try:
                async for response in openai_handler.receive_events():
                    if response['type'] not in ["response.audio.delta", "response.audio_transcript.delta"]:
                        print(f"Received event: {response['type']}", response)

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "type" : "audio",
                            "payload": audio_payload
                        }
                        await websocket.send_json(audio_delta)

                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("sent speech started")
                        await websocket.send_json({"type": "speech_started"})

            except Exception as e:
                print(f"Error in send_audio_to_user: {e}")

        await asyncio.gather(receive_audio_from_user(), send_audio_to_user())
    except Exception as e:
        websocket.send_json({"error" : traceback.format_exc()})
        print(f"Error in websocket_endpoint: {e}")
