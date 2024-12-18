import asyncio
import time
import websockets
import pyaudio
from audio_capture import AudioCapture
from openai_client import OpenAIClient
from websocket_manager import WebSocketManager
from response_processor import ResponseProcessor
from config import Config
from common_logging import setup_logging

class VoiceAssistant:
    def __init__(self, config: Config, audio_capture: AudioCapture, openai_client: OpenAIClient,
                 websocket_manager: WebSocketManager, response_processor: ResponseProcessor):
        self.config = config
        self.max_api_calls = config.max_api_calls
        self.api_calls_made = 0
        self.is_running = False
        self.waiting_for_response = False
        self.audio_buffer = b""
        self.silence_threshold = config.silence_threshold
        self.cooldown_active = False
        self.cooldown_duration = config.cooldown_duration
        self.min_buffer_size = config.min_buffer_size
        self.max_buffer_wait_time = config.max_buffer_wait_time
        self.buffer_ready = asyncio.Event()
        self.last_audio_time = 0

        self.audio_capture = audio_capture
        self.openai_client = openai_client
        self.websocket_manager = websocket_manager
        self.response_processor = response_processor

        self.logger = setup_logging('voice_assistant')
        self.logger.info("VoiceAssistant initialized")

        self.process_audio_task = None
        self.is_paused = False
        self._is_idle = True
        self._is_recording = False
        self._is_processing = False

    async def pause(self):
        if self.is_paused:
            return  # Already paused
        self.is_paused = True  # Set the paused flag
        self.audio_capture.stop_stream()  # Stop the audio stream
        self.logger.info("Assistant paused")

        # If there's audio in the buffer, send it to the API
        if self.audio_buffer:
            await self.send_buffer_to_api()
            # Clear the buffer and reset variables
            self.audio_buffer = b''
            self.buffer_ready.clear()

        # Broadcast paused status
        await self.websocket_manager.broadcast_status("paused", False)

    async def resume(self):
        if not self.is_paused:
            return  # Already running
        self.is_paused = False  # Reset the paused flag
        self.audio_buffer = b''  # Clear the audio buffer
        self.audio_capture.reset_vad()  # Reset VAD state
        self.last_audio_time = time.time()  # Reset the last audio time
        self.waiting_for_response = False  # Ensure not waiting for a response
        self.cooldown_active = False  # Reset cooldown if necessary
        self.audio_capture.start_stream()  # Start the audio stream
        await self.websocket_manager.broadcast_status("listening", True)  # Broadcast listening status
        self.logger.info("Assistant resumed")

    @property
    def is_idle(self):
        return (not self._is_recording and 
                not self._is_processing and 
                not self.waiting_for_response and 
                not self.cooldown_active)

    async def run(self):
        try:
            await self.websocket_manager.start()
            await self.openai_client.connect()

            self.audio_capture.select_audio_device()
            self.audio_capture.start_stream()  # Ensure the audio stream starts
            self.logger.info("Voice Assistant is ready.")
            await self.websocket_manager.broadcast_status("ready", False)

            self.process_audio_task = asyncio.create_task(self.process_audio())
            api_task = asyncio.create_task(self.handle_api_responses())

            while True:
                if self.is_idle and self.openai_client.reset_pending:
                    await self.openai_client.reset_session()
                
                await asyncio.sleep(1)  # Check every second

        except websockets.exceptions.ConnectionClosed as e:
            self.logger.error(f"WebSocket connection closed: {str(e)}")
            self.waiting_for_response = False
            self.logger.debug("waiting_for_response set to False")
            await self.websocket_manager.broadcast_status("disconnected", False)
            
            # Attempt to reconnect
            await self.reconnect_openai_client()
        except Exception as e:
            self.logger.exception(f"Error in main loop: {str(e)}")
        finally:
            await self.cleanup()

    async def process_audio(self):
        self.logger.info("Started audio processing")
        try:
            while self.is_running:
                if self.is_paused:
                    await asyncio.sleep(0.01)
                    continue
                try:
                    self._is_recording = True
                    audio_chunk = await self.audio_capture.read_audio()
                    self._is_recording = False
                    self._is_processing = True
                    is_speech = await self.audio_capture.is_speech(audio_chunk)
                    self._is_processing = False

                    await self.websocket_manager.broadcast_status("listening" if is_speech else "idle", is_speech)

                    if is_speech:
                        self.audio_buffer += audio_chunk
                        self.last_audio_time = time.time()
                        self.logger.debug(f"Speech detected. Buffer size: {len(self.audio_buffer)}")

                        if len(self.audio_buffer) >= self.min_buffer_size:
                            self.buffer_ready.set()

                    if not is_speech and self.buffer_ready.is_set():
                        if not self.waiting_for_response and not self.cooldown_active:
                            if len(self.audio_buffer) >= self.min_buffer_size:
                                await self.send_buffer_to_api()
                            else:
                                self.logger.info("Audio buffer is too small or empty. Not sending to API.")
                                self.audio_buffer = b""
                                self.buffer_ready.clear()

                    # Check for timeout
                    if time.time() - self.last_audio_time > self.max_buffer_wait_time and len(self.audio_buffer) >= self.min_buffer_size:
                        self.logger.info("Buffer wait time exceeded. Sending available audio.")
                        if not self.waiting_for_response and not self.cooldown_active:
                            await self.send_buffer_to_api()

                    await asyncio.sleep(0.01)
                except Exception as e:
                    self.logger.exception(f"Error in audio processing: {str(e)}")
        except asyncio.CancelledError:
            self.logger.info("Audio processing task cancelled")
        finally:
            self._is_recording = False
            self._is_processing = False
            self.logger.info("Stopped audio processing")

    async def send_buffer_to_api(self):
        if len(self.audio_buffer) == 0:
            self.logger.info("Audio buffer is empty. Not sending to API.")
            self.audio_buffer = b""
            self.buffer_ready.clear()
            return
        
        import io
        from pydub import AudioSegment

        try:
            self.waiting_for_response = True  # Set before sending to prevent new API calls
            await self.websocket_manager.broadcast_new_response()

            # Resample audio to 24000 Hz before sending to the API
            audio_segment = AudioSegment(
                data=self.audio_buffer,
                sample_width=pyaudio.get_sample_size(self.audio_capture.format),
                frame_rate=self.audio_capture.rate,
                channels=self.audio_capture.channels
            )
            audio_segment = audio_segment.set_frame_rate(24000)
            audio_segment = audio_segment.set_channels(1)
            resampled_audio_buffer = audio_segment.raw_data

            await self.send_audio_to_api(resampled_audio_buffer)
            self.audio_buffer = b""
            self.buffer_ready.clear()
            self.cooldown_active = True
            asyncio.create_task(self.cooldown_timer())
        except Exception as e:
            self.logger.error(f"Error in send_buffer_to_api: {str(e)}", exc_info=True)

    async def send_audio_to_api(self, buffer):
        if self.max_api_calls != -1 and self.api_calls_made >= self.max_api_calls:
            self.logger.info("Maximum number of API calls reached. Initiating graceful shutdown.")
            await self.websocket_manager.broadcast_status("max_calls_reached", False)
            return False

        self.logger.info(f"Sending audio buffer to API (size: {len(buffer)} bytes)")
        self.logger.debug(f"waiting_for_response: {self.waiting_for_response}, cooldown_active: {self.cooldown_active}")

        try:
            await self.openai_client.send_audio(buffer)
            self.api_calls_made += 1
            self.logger.info(f"API call made. Total calls: {self.api_calls_made}")
            await self.websocket_manager.broadcast_api_call_count(self.api_calls_made)
            await self.websocket_manager.broadcast_status("processing", False)
            await self.pause()  # Automatically pause the assistant
            return True
        except Exception as e:
            self.logger.error(f"Error sending audio to API: {str(e)}", exc_info=True)
            await self.websocket_manager.broadcast_error(str(e), e.__class__.__name__)
            return False
        finally:
            self.logger.debug("Exiting send_audio_to_api")

    async def cooldown_timer(self):
        self.logger.debug(f"Cooldown started for {self.cooldown_duration} seconds")
        await asyncio.sleep(self.cooldown_duration)
        self.cooldown_active = False
        self.logger.debug("Cooldown period ended")

    async def handle_api_responses(self):
        self.logger.info("Started handling API responses")
        try:
            while True:
                response = await self.openai_client.receive_response()

                if not isinstance(response, dict):
                    self.logger.error(f"Invalid API response type: {type(response)}")
                    continue

                if response['type'] == 'session_reset':
                    self.logger.info("Session was reset. Restarting the conversation.")
                    self.waiting_for_response = False
                    await self.websocket_manager.broadcast_status("ready", False)
                    continue

                # Forward the response to the frontend
                await self.websocket_manager.broadcast_response(response)

                if response['type'] == 'response.audio_transcript.delta':
                    delta = self.response_processor.process_transcript_delta(response.get('delta', ''))
                    await self.websocket_manager.broadcast_transcript(delta)
                    if self.response_processor.is_question(self.response_processor.get_full_transcript()):
                        self.logger.debug("Question detected")
                elif response['type'] == 'response.complete':
                    self.logger.info("Response complete")
                    self.waiting_for_response = False
                    self.logger.debug("waiting_for_response set to False")
                    await self.websocket_manager.broadcast_status("idle", False)
                    self.response_processor.clear_transcript()
                elif response['type'] == 'error':
                    error_message = response.get('error', {}).get('message', 'Unknown error')
                    error_code = response.get('error', {}).get('code', 'Unknown code')
                    self.logger.error(f"API Error: Code: {error_code}, Message: {error_message}")
                    self.waiting_for_response = False
                    self.logger.debug("waiting_for_response set to False")
                    await self.websocket_manager.broadcast_status("error", False)
                    if error_code == 'session_expired':
                        self.logger.info("Session expired. Attempting to reconnect.")
                        await self.openai_client.reset_session()
                        await self.websocket_manager.broadcast_status("ready", False)
                else:
                    self.logger.debug(f"Received response type: {response['type']}")
        except asyncio.CancelledError:
            self.logger.info("API response handling task cancelled")
        except Exception as e:
            self.logger.error(f"Error handling API response: {str(e)}", exc_info=True)
            self.waiting_for_response = False
            self.logger.debug("waiting_for_response set to False")
            await self.websocket_manager.broadcast_error(str(e), e.__class__.__name__)

    async def reconnect_openai_client(self):
        self.logger.info("Attempting to reconnect to OpenAI API")
        reconnect_attempts = 0
        max_reconnect_attempts = 3

        while reconnect_attempts < max_reconnect_attempts:
            try:
                await self.openai_client.connect()
                await self.openai_client.initialize_session()
                self.logger.info("Reconnected to OpenAI API")
                return
            except Exception as e:
                reconnect_attempts += 1
                self.logger.error(f"Reconnection attempt {reconnect_attempts} failed: {str(e)}")
                await asyncio.sleep(2)

        self.logger.error("Maximum reconnection attempts reached. Stopping assistant.")
        await self.graceful_shutdown()

    async def graceful_shutdown(self):
        self.logger.info("Initiating graceful shutdown...")
        await self.websocket_manager.broadcast_status("shutting_down", False)

        # Close the OpenAI client connection
        await self.openai_client.close_connection()

        await self.cleanup()
        self.logger.info("Graceful shutdown complete")

    async def start_listening(self):
        if not self.is_running:
            self.is_running = True
            self.logger.info("VoiceAssistant started listening")
            # Start the audio stream
            self.audio_capture.start_stream()
            self.process_audio_task = asyncio.create_task(self.process_audio())
            # Broadcast status update
            await self.websocket_manager.broadcast_status("listening", True)

    async def stop_listening(self):
        if self.is_running:
            self.is_running = False
            self.logger.info("VoiceAssistant stopped listening")
            # Cancel the process_audio task
            if self.process_audio_task:
                self.process_audio_task.cancel()
                try:
                    await self.process_audio_task
                except asyncio.CancelledError:
                    self.logger.info("process_audio_task successfully cancelled")
                self.process_audio_task = None
            # Stop the audio stream
            self.audio_capture.stop_stream()
            # Broadcast status update
            await self.websocket_manager.broadcast_status("idle", False)

    async def cleanup(self):
        # Add any cleanup operations here
        pass

    def stop(self):
        self.is_running = False
        self.logger.info("Voice Assistant stopped")
        # Cancel the process_audio task if it's running
        if self.process_audio_task:
            self.process_audio_task.cancel()
            self.process_audio_task = None

if __name__ == "__main__":
    config = Config()
    logger = setup_logging('voice_assistant')

    # Prompt user for max number of API calls
    max_api_calls_input = input("Enter maximum number of API calls (-1 for unlimited): ")
    try:
        config.max_api_calls = int(max_api_calls_input)
        logger.info(f"Max API calls set to: {config.max_api_calls}")
    except ValueError:
        print("Invalid input. Using unlimited API calls.")
        config.max_api_calls = -1
        logger.info("Max API calls set to unlimited")

    audio_capture = AudioCapture(config)
    openai_client = OpenAIClient(config)
    response_processor = ResponseProcessor(config)
    assistant = VoiceAssistant(config, audio_capture, openai_client, None, response_processor)
    websocket_manager = WebSocketManager(assistant)
    assistant.websocket_manager = websocket_manager
    asyncio.run(assistant.run())
