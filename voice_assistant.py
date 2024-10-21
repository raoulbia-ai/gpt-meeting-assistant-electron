import asyncio
from common_logging import setup_logging

class VoiceAssistant:
    def __init__(self, audio_capture):
        self.is_paused = False
        self.audio_capture = audio_capture
        self.audio_buffer = b''
        self.speech_frames_count = 0
        self.is_sending_audio = False
        self.is_processing = False
        self.stop_event = asyncio.Event()
        self.logger = setup_logging('voice_assistant')

    async def pause(self):
        self.is_paused = True
        self.logger.info("Assistant paused. Stopping capture and processing audio.")
        
        # Stop audio capture
        self.audio_capture.stop_stream()
        
        # If there's audio in the buffer, send it for transcription
        if self.audio_buffer:
            await self.send_audio_to_api(self.audio_buffer)
            self.audio_buffer = b''
            self.speech_frames_count = 0

    async def resume(self):
        self.is_paused = False
        self.logger.info("Assistant resumed")
        # Restart audio capture
        self.audio_capture.start_stream()
        # Reset speech detection state
        self.speech_frames_count = 0
        self.is_sending_audio = False
        self.is_processing = False
        self.audio_buffer = b''  # Clear the audio buffer
        self.audio_capture.reset_vad()  # Reset VAD state if applicable

    async def process_audio(self):
        while not self.stop_event.is_set():
            if self.is_paused:
                await asyncio.sleep(0.1)
                continue
            # Existing audio processing logic

    async def send_audio_to_api(self):
        while not self.stop_event.is_set():
            if self.is_paused or not self.is_sending_audio:
                await asyncio.sleep(0.1)
                continue
            # Existing logic to send audio to API
