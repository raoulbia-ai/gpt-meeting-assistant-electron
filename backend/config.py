import os
import pyaudio

class Config:
    def __init__(self):
        self.max_api_calls = -1  # Set from environment or parameters
        self.silence_threshold = 10
        self.cooldown_duration = 5
        self.min_buffer_size = 32000
        self.max_buffer_wait_time = 5 
        self.rate = 24000  # Set sample rate to 24kHz as required by the API
        self.frame_duration_ms = 30  # Use 20 ms frames for VAD
        self.channels = 1
        self.format = pyaudio.paInt16  # Add this line
        self.sample_width = pyaudio.get_sample_size(self.format)
        self.chunk = int(self.rate * self.frame_duration_ms / 1000)

        # Removed websocket_host and websocket_port as they are hardcoded in websocket_manager.py
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        self.instructions = """You are a helpful assistant. Provide concise and direct answers.
                                Avoid unnecessary elaboration unless specifically requested."""
        self.voice = "alloy"
        self.temperature = 0.6
        self.question_starters = ['what', 'when', 'where', 'who', 'why', 'how', 'can', 'could', 'would', 'will', 'do', 'does', 'is', 'are']
