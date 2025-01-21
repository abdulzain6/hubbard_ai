from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from ..lib.openai_realtime_client import RealtimeClient, TurnDetectionMode
from ..auth import get_user_id_and_role
from ..lib.prompt import DEFAULT_PROMPT_VOICE, STARTER_MESSAGE

import json
import websockets
import os
import traceback
import base64
import asyncio


app = APIRouter()

tools = []


class RealtimeClientAsyncCallback(RealtimeClient):
    async def handle_messages(self) -> None:
        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")
                
                if event_type == "error":
                    print(f"Error: {event['error']}")
                    continue
                
                # Track response state
                elif event_type == "response.created":
                    self._current_response_id = event.get("response", {}).get("id")
                    self._is_responding = True
                
                elif event_type == "response.output_item.added":
                    self._current_item_id = event.get("item", {}).get("id")
                
                elif event_type == "response.done":
                    self._is_responding = False
                    self._current_response_id = None
                    self._current_item_id = None
                
                # Handle interruptions
                elif event_type == "input_audio_buffer.speech_started":
                    print("\n[Speech detected]")
                    if self._is_responding:
                        await self.handle_interruption()

                    if self.on_interrupt:
                        await self.on_interrupt()

                
                elif event_type == "input_audio_buffer.speech_stopped":
                    print("\n[Speech ended]")
                
                # Handle normal response events
                elif event_type == "response.text.delta":
                    if self.on_text_delta:
                        await self.on_text_delta(event["delta"])
                        
                elif event_type == "response.audio.delta":
                    if self.on_audio_delta:
                        audio_bytes = base64.b64decode(event["delta"])
                        await self.on_audio_delta(audio_bytes)
                        
                elif event_type == "response.function_call_arguments.done":
                    await self.call_tool(event["call_id"], event['name'], json.loads(event['arguments']))

                elif event_type in self.extra_event_handlers:
                    self.extra_event_handlers[event_type](event)

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        except Exception as e:
            print(f"Error in message handling: {str(e)}")



@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    print("Client connected")
    await websocket.accept()
    
    try:
        message = await websocket.receive_json()
        if 'token' not in message:
            await websocket.close(code=4000)
            return

        voice = message.get("voice", DEFAULT_PROMPT_VOICE)
        token = message['token']
        user = get_user_id_and_role(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        )
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        await websocket.send_json({"error" : f"auth error {e}"})
        await websocket.close(code=4001)
        return

    async def send_audio_to_user(audio_bytes: bytes):
        try:
            base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            await websocket.send_json({
                "type": "audio",
                "payload": base64_audio
            })
        except Exception as e:
            print(f"Error in send_audio_to_user: {e}")

    async def send_stop_command():
        try:
            print("Stop command")
            await websocket.send_json({
                "type": "command",
                "payload": "stop"
            })
        except Exception as e:
            print(f"Error in send_stop_command: {e}")

    async def receive_audio_from_user():
        try:
            async for message in websocket.iter_text():
                # { "type": "audio", "payload": "base64_encoded_audio_data" }
                data = json.loads(message)
                if data.get("type") == "audio" and data.get("payload"):
                    audio_bytes = base64.b64decode(data["payload"])
                    await client.stream_audio(audio_bytes)
        except WebSocketDisconnect:
            print("Client disconnected.")
            await client.close()

    client = RealtimeClientAsyncCallback(
        api_key=os.environ.get("OPENAI_API_KEY"),
        on_audio_delta=lambda audio: send_audio_to_user(audio),
        on_interrupt=lambda: send_stop_command(), # Might require converting to non async
        turn_detection_mode=TurnDetectionMode.SERVER_VAD,
        tools=tools,
        instructions=STARTER_MESSAGE,
        voice=voice
    )
    await client.connect()
    await asyncio.gather(receive_audio_from_user(), client.handle_messages())