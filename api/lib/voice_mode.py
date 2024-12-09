import json
import websockets
from typing import Dict, Any, AsyncGenerator


class OpenAIHandler:
    def __init__(self, voice: str, system_message: str, start_message: str, openai_api_key: str, temperature: float = 0.8):
        self.ws = None
        self.voice = voice
        self.system_message = system_message
        self.temperature = temperature
        self.openai_api_key = openai_api_key
        self.start_message = start_message

    async def connect(self):
        self.ws = await websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        extra_headers={
            "Authorization": f"Bearer {self.openai_api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        )
        await self.initialize_session()

    async def initialize_session(self):
        session_update = {
            "type": "session.update",
            "session": {
                "turn_detection": {"type": "server_vad"},
                "voice": self.voice,
                "instructions": self.system_message,
                "modalities": ["text", "audio"],
                "temperature": self.temperature,
            }
        }
        print('Sending session update:', json.dumps(session_update))
        await self.ws.send(json.dumps(session_update))
        await self.send_initial_conversation_item()

    async def send_initial_conversation_item(self):
        initial_conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": self.start_message
                    }
                ]
            }
        }
        await self.ws.send(json.dumps(initial_conversation_item))
        await self.ws.send(json.dumps({"type": "response.create"}))

    async def send_audio(self, audio_data: str) -> None:
        audio_append: Dict[str, Any] = {
            "type": "input_audio_buffer.append",
            "audio": audio_data
        }
        await self.ws.send(json.dumps(audio_append))

    async def receive_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        async for message in self.ws:
            yield json.loads(message)

    async def close(self):
        if self.ws:
            await self.ws.close()