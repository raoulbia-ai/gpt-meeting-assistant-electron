import os
import json
import asyncio
import websockets
import base64
import logging
# from logging.handlers import RotatingFileHandler
from common_logging import setup_logging

class OpenAIClient:
    def __init__(self, config, debug_to_console=False):
        self.config = config
        self.api_key = self.config.api_key
        self.api_url = self.config.api_url
        self.websocket = None
        self.logger = logging.getLogger('openai_client')
        # self.setup_logging(debug_to_console)
        self.logger = setup_logging('openai_client')

    # def setup_logging(self, debug_to_console=False):
    #     self.logger.setLevel(logging.CRITICAL)
        
    #     # Ensure the logs directory exists
    #     os.makedirs('logs', exist_ok=True)
        
    #     # File handler
    #     file_handler = RotatingFileHandler('logs/openai_client.log', maxBytes=10000000, backupCount=5)
    #     file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #     file_handler.setFormatter(file_formatter)
    #     self.logger.addHandler(file_handler)

    #     if debug_to_console:
    #         # Console handler for debug mode
    #         console_handler = logging.StreamHandler()
    #         console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    #         console_handler.setFormatter(console_formatter)
    #         console_handler.setLevel(logging.DEBUG)
    #         self.logger.addHandler(console_handler)
    
    async def connect(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
            "Content-Type": "application/json"
        }
        self.websocket = await websockets.connect(self.api_url, extra_headers=headers)
        self.logger.info("Connected to OpenAI API")

    async def initialize_session(self):
        session_update = {
            "event_id": self.generate_event_id(),
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": self.config.instructions,
                "voice": self.config.voice,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                },
                "temperature": self.config.temperature
            }
        }
        await self.websocket.send(json.dumps(session_update))
        self.logger.debug(f"Session update sent: {json.dumps(session_update)}")
        response = await self.websocket.recv()
        self.logger.debug(f"Session initialization response: {response}")

    async def send_audio(self, audio_buffer):
        if not isinstance(audio_buffer, bytes):
            self.logger.error(f"Invalid audio buffer type: {type(audio_buffer)}. Expected bytes.")
            return

        buffer_size = len(audio_buffer)
        self.logger.info(f"Attempting to send audio buffer of size: {buffer_size} bytes")

        if buffer_size == 0:
            self.logger.warning("Attempted to send empty audio buffer. Skipping API call.")
            return

        try:
            encoded_audio = self.encode_audio(audio_buffer)
            message = {
                "event_id": self.generate_event_id(),
                "type": "input_audio_buffer.append",
                "audio": encoded_audio  # Base64-encoded audio string
            }
            await self.websocket.send(json.dumps(message))
            self.logger.debug(f"Sent audio message of size: {len(encoded_audio)} characters")

            # Send commit message immediately after appending audio
            commit_message = {
                "event_id": self.generate_event_id(),
                "type": "input_audio_buffer.commit"
            }
            await self.websocket.send(json.dumps(commit_message))
            self.logger.debug("Sent commit message")

        except Exception as e:
            self.logger.error(f"Error in send_audio: {str(e)}")

    async def receive_response(self):
        try:
            response = await self.websocket.recv()
            parsed_response = json.loads(response)
            self.logger.debug(f"Received response: {parsed_response}")
            return parsed_response
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.error(f"WebSocket connection closed: {e}")
            raise e  # Propagate the exception
        except Exception as e:
            self.logger.error(f"Error receiving response: {str(e)}")
            raise e  # Propagate other exceptions

    def generate_event_id(self):
        return f"event_{os.urandom(3).hex()}"

    def encode_audio(self, audio_buffer):
        try:
            return base64.b64encode(audio_buffer).decode("utf-8")
        except Exception as e:
            self.logger.error(f"Error encoding audio: {str(e)}")
            return ""

    def is_connected(self):
        return self.websocket and not self.websocket.closed

    async def close_connection(self):
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            self.logger.info("Closed connection to OpenAI API")
