from pydub import AudioSegment
import functools
import io
import pyaudio
import webrtcvad
import numpy as np
import logging
from common_logging import setup_logging
import os
import asyncio
from pydub import AudioSegment
import io

class AudioCapture:
    def __init__(self, config, debug_to_console=False):
        self.chunk = config.chunk
        self.format = pyaudio.paInt16
        self.channels = config.channels
        self.rate = config.rate
        self.frame_duration_ms = 30  # Must be 10, 20, or 30
        self.bytes_per_sample = pyaudio.get_sample_size(self.format)
        self.chunk = int(self.rate * self.frame_duration_ms / 1000)  # Frames per buffer
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.vad = webrtcvad.Vad(1)  # Aggressiveness level from 0 to 3
        self.device_index = config.speaker_device_index  # Use speaker device index from config
        self.logger = logging.getLogger('audio_capture')

        # Speech detection parameters
        frames_per_second = 1000 / self.frame_duration_ms
        self.speech_frames_threshold = int(0.3 * frames_per_second)  # Reduced from 0.5 to 0.3 seconds
        self.speech_frames_count = 0

        # self.setup_logging(debug_to_console)
        self.logger = setup_logging('audio_capture')
        self.logger.info("AudioCapture initialized")
        self.logger.info(f"Speech frames threshold set to {self.speech_frames_threshold} frames")


    def select_audio_device(self, is_speaker=False):
        self.logger.info("Selecting audio device")
        print("Available audio devices:")
        devices = []
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if (is_speaker and dev.get('maxOutputChannels') > 0) or (not is_speaker and dev.get('maxInputChannels') > 0):
                devices.append((i, dev.get('name')))
                print(f"Device {i}: {dev.get('name')}")
        
        while True:
            try:
                device_index_input = input("Enter the device index for your device: ")
                self.device_index = int(device_index_input)
                dev_info = self.p.get_device_info_by_index(self.device_index)
                if (is_speaker and dev_info.get('maxOutputChannels') > 0) or (not is_speaker and dev_info.get('maxInputChannels') > 0):
                    print(f"Selected device: {dev_info.get('name')}")
                    self.logger.info(f"Audio device selected: {dev_info.get('name')}")
                    return self.device_index
                else:
                    print("Selected device is not a valid device. Please try again.")
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
                self.logger.info(f"Audio stream started for device {self.device_index} with rate {self.rate} and chunk size {self.chunk}")
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

        try:
            audio_data = self.stream.read(self.chunk, exception_on_overflow=False)
            # Process audio data immediately after reading
        except Exception as e:
            self.logger.error(f"Error reading audio data: {e}")
            return b''  # Return empty bytes to avoid crashing

        # Convert bytes to AudioSegment
        audio_segment = AudioSegment(
            data=audio_data,
            sample_width=pyaudio.get_sample_size(self.format),
            frame_rate=self.rate,
            channels=self.channels
        )
        
        # Ensure mono if necessary
        if self.channels > 1:
            audio_segment = audio_segment.set_channels(1)
        
        # Get raw audio data
        audio_data = audio_segment.raw_data
        # self.rate remains at 48000 Hz
        
        rms = audio_segment.rms
        self.logger.debug(f"Audio RMS: {rms}")

        return audio_data

    async def is_speech(self, audio_segment):
        try:
            self.logger.debug(f"Processing audio segment of length: {len(audio_segment)}")
            self.logger.debug(f"Audio segment sample rate: {self.rate}, channels: {self.channels}")

            frame_duration_ms = self.frame_duration_ms  # 10, 20, or 30 ms
            samples_per_frame = int(self.rate * frame_duration_ms / 1000)
            expected_frame_length = samples_per_frame * self.bytes_per_sample

            # Split the audio segment into frames of the correct size
            frames = [audio_segment[i:i+expected_frame_length] for i in range(0, len(audio_segment), expected_frame_length)]

            is_speech_frame = False
            for frame in frames:
                self.logger.debug(f"Processing frame of length: {len(frame)} bytes (expected: {expected_frame_length} bytes)")
                if len(frame) == expected_frame_length:
                    is_speech_frame = self.vad.is_speech(frame, self.rate)
                    self.logger.debug(f"VAD result for frame: {is_speech_frame}")
                    if is_speech_frame:
                        break  # If any frame is speech, consider the whole segment as speech

            if is_speech_frame:
                self.speech_frames_count += 1
            else:
                self.speech_frames_count = max(0, self.speech_frames_count - 1)

            self.logger.debug(f"VAD speech: {is_speech_frame}, Speech frames: {self.speech_frames_count}, Threshold: {self.speech_frames_threshold}")
            return self.speech_frames_count >= self.speech_frames_threshold

        except Exception as e:
            self.logger.error(f"Error in VAD: {str(e)}", exc_info=True)
            self.logger.debug(f"Audio segment details: length={len(audio_segment)}, first few bytes: {audio_segment[:20]}")
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

    def reset_vad(self):
        self.speech_frames_count = 0
        self.stop_stream()
        # self.p.terminate()
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
    def reset_vad(self):
        self.speech_frames_count = 0
