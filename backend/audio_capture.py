import pyaudio
import webrtcvad
import numpy as np
import logging
from logging.handlers import RotatingFileHandler
import os
import asyncio

class AudioCapture:
    def __init__(self, config, debug_to_console=False):
        self.chunk = config.chunk
        self.format = pyaudio.paInt16
        self.channels = config.channels
        self.rate = config.rate
        self.frame_duration_ms = config.frame_duration_ms
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.vad = webrtcvad.Vad(0)  # Aggressiveness level
        self.device_index = None
        self.logger = logging.getLogger('audio_capture')

        # Speech detection parameters
        self.speech_frames_threshold = int(0.5 * self.rate / self.chunk)
        self.speech_frames_count = 0

        self.setup_logging(debug_to_console)
        self.logger.info("AudioCapture initialized")
        self.logger.info(f"Speech frames threshold set to {self.speech_frames_threshold} frames")

    def setup_logging(self, debug_to_console=False):
        self.logger.setLevel(logging.CRITICAL)
        
        # Ensure the logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # File handler
        file_handler = RotatingFileHandler('logs/audio_capture.log', maxBytes=10000000, backupCount=5)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        if debug_to_console:
            # Console handler for debug mode
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(console_handler)

    def select_audio_device(self):
        self.logger.info("Selecting audio device")
        print("Available audio input devices:")
        input_devices = []
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev.get('maxInputChannels') > 0:
                input_devices.append((i, dev.get('name')))
                print(f"Device {i}: {dev.get('name')}")
        
        while True:
            try:
                device_index_input = input("Enter the device index for your microphone: ")
                self.device_index = int(device_index_input)
                dev_info = self.p.get_device_info_by_index(self.device_index)
                if dev_info.get('maxInputChannels') > 0:
                    print(f"Selected device: {dev_info.get('name')}")
                    self.logger.info(f"Audio device selected: {dev_info.get('name')}")
                    return self.device_index
                else:
                    print("Selected device is not an input device. Please try again.")
            except (ValueError, IndexError):
                print("Invalid input. Please enter a valid device index.")

    def start_stream(self):
        self.logger.info("Starting audio stream")
        if self.device_index is None:
            self.select_audio_device()
        
        try:
            if self.stream is None:
                self.stream = self.p.open(format=self.format,
                                          channels=self.channels,
                                          rate=self.rate,
                                          input=True,
                                          input_device_index=self.device_index,
                                          frames_per_buffer=self.chunk)
                self.logger.info(f"Audio stream started for device {self.device_index}")
            else:
                self.logger.info("Audio stream already started")
        except OSError as e:
            self.logger.error(f"Error opening audio stream: {str(e)}")
            print(f"Error opening audio stream: {str(e)}")
            print("Please ensure the selected device is not in use by another application.")
            raise

    async def read_audio(self):
        if self.stream is None:
            self.logger.error("Audio stream is not initialized")
            raise RuntimeError("Audio stream is not initialized")
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(None, self.stream.read, self.chunk, False)
        
        # Log the audio levels
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        rms = np.sqrt(np.mean(np.square(audio_array.astype(np.float32))))
        self.logger.debug(f"Audio RMS: {rms}")
        
        return audio_data

    async def is_speech(self, audio_segment):
        try:
            is_speech = self.vad.is_speech(audio_segment, self.rate)
            if is_speech:
                self.speech_frames_count += 1
            else:
                self.speech_frames_count = max(0, self.speech_frames_count - 1)

            self.logger.debug(f"VAD speech: {is_speech}, Speech frames: {self.speech_frames_count}, Threshold: {self.speech_frames_threshold}")
            return self.speech_frames_count >= self.speech_frames_threshold
        except Exception as e:
            self.logger.error(f"Error in VAD: {str(e)}")
            return False

    def stop_stream(self):
        if self.stream is not None:
            self.logger.info("Stopping audio stream")
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.logger.info("Audio stream stopped")
        else:
            self.logger.info("Audio stream is not running")

    def __del__(self):
        self.stop_stream()
        self.p.terminate()
        self.logger.info("AudioCapture instance destroyed")

if __name__ == "__main__":
    # This allows you to test the AudioCapture class independently
    import asyncio

    audio_capture = AudioCapture(None, debug_to_console=True)
    audio_capture.select_audio_device()
    audio_capture.start_stream()

    print("Press Ctrl+C to stop the audio capture.")
    try:
        while True:
            audio_chunk = asyncio.run(audio_capture.read_audio())
            is_speech = asyncio.run(audio_capture.is_speech(audio_chunk))
            if is_speech:
                print("Speech detected")
            else:
                print("Silence")
    except KeyboardInterrupt:
        print("\nStopping audio capture.")
    finally:
        audio_capture.stop_stream()
        print("Audio capture stopped.")
