from fastapi import APIRouter
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from ..lib.voice_mode import OpenAIHandler
import json
import base64
import asyncio

LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created'
]

app = APIRouter()


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    print("Client connected")
    await websocket.accept()

    openai_handler = OpenAIHandler()
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
                if response['type'] in LOG_EVENT_TYPES:
                    print(f"Received event: {response['type']}", response)

                if response.get('type') == 'response.audio.delta' and 'delta' in response:
                    audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                    audio_delta = {
                        "payload": audio_payload
                    }
                    await websocket.send_json(audio_delta)

        except Exception as e:
            print(f"Error in send_audio_to_user: {e}")

    await asyncio.gather(receive_audio_from_user(), send_audio_to_user())

