import os

class Config:
    def __init__(self):
        self.max_api_calls = -1  # Set from environment or parameters
        self.silence_threshold = 10
        self.cooldown_duration = 5
        self.min_buffer_size = 32000
        self.max_buffer_wait_time = 5 
        self.rate = 48000 #32000
        self.frame_duration_ms = 30
        self.chunk = int(self.rate * self.frame_duration_ms / 1000)
        self.channels = 1

        # Removed websocket_host and websocket_port as they are hardcoded in websocket_manager.py
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        self.instructions = """You are a helpful assistant. Provide concise and direct answers.
                                Avoid unnecessary elaboration unless specifically requested."""
        self.voice = "alloy"
        self.temperature = 0.6
        self.question_starters = ['what', 'when', 'where', 'who', 'why', 'how', 'can', 'could', 'would', 'will', 'do', 'does', 'is', 'are']
