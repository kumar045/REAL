import asyncio
import os
import httpx
import types

# Assuming these are your custom modules for logging and singleton pattern
from realtime_ai_character.logger import get_logger
from realtime_ai_character.utils import Singleton
from realtime_ai_character.audio.text_to_speech.base import TextToSpeech

# Initialize the logger
logger = get_logger(__name__)
DEBUG = False  # Set to True for debugging

# Configuration for OpenAI API
config = types.SimpleNamespace(**{
    'default_voice': 'shimmer',
    'url': 'https://api.openai.com/v1/audio/speech',
    'headers': {
        'Authorization': f'Bearer {os.environ["OPENAI_API_KEY"]}',  # Set your OpenAI API key in environment variables
        'Content-Type': 'application/json'
    },
    'data': {
        'model': 'tts-1',
        'response_format': 'mp3',
        'speed': 1
    }
})

class ElevenLabs(Singleton, TextToSpeech):
    def __init__(self):
        super().__init__()
        logger.info("Initializing OpenAI Text To Speech...")
        self.voice_ids = {
            "Axis Bank": os.environ.get('RAIDEN_VOICE') or config.default_voice,
            
        }
    def get_voice_id(self, name):
        # Customize the voice ID logic if needed
        return self.voice_ids.get(name, config.default_voice)

    async def stream(self, text, websocket, tts_event: asyncio.Event, characater_name="", first_sentence=False,sid="",
        platform="") -> None:
        if DEBUG:
            return
        data = {
            "input": text,
            "voice": self.get_voice_id(characater_name),
            **config.data,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(config.url, json=data, headers=config.headers)
            async for chunk in response.aiter_bytes():
                await asyncio.sleep(0.1)  # Control the rate of streaming
                if tts_event.is_set():
                    break
                logger.info("Streaming chunk from OpenAI: %s", chunk)
                
                if platform != "twilio":
                    await websocket.send_bytes(chunk)
                else:
                    audio_b64 = base64.b64encode(chunk).decode()
                    media_response = {
                        "event": "media",
                        "streamSid": sid,
                        "media": {
                            "payload": audio_b64,
                        },
                    }
                    # "done" marker is sent to twilio to track if the audio has been completed.
                    await websocket.send_json(media_response)
                    mark = {
                        "event": "mark",
                        "streamSid": sid,
                        "mark": {
                            "name": "done",
                        },
                    }
                    await websocket.send_json(mark)
