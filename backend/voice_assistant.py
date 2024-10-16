import asyncio
import time
import websockets
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
        self.is_running = False  # Change from True to False
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

    async def run(self):
        try:
            await self.websocket_manager.start()
            await self.openai_client.connect()
            await self.openai_client.initialize_session()

            self.audio_capture.select_audio_device()
            self.logger.info("Voice Assistant is ready.")
            await self.websocket_manager.broadcast_status("ready", False)

            # Start process_audio task
            # self.is_running = True
            self.process_audio_task = asyncio.create_task(self.process_audio())
            
            # Start handle_api_responses task
            api_task = asyncio.create_task(self.handle_api_responses())

            # Wait for both tasks
            await asyncio.gather(self.process_audio_task, api_task)

        except websockets.exceptions.ConnectionClosed as e:
            self.logger.error(f"WebSocket connection closed: {str(e)}")
            self.waiting_for_response = False
            self.logger.debug("waiting_for_response set to False")
            await self.websocket_manager.broadcast_status("disconnected", False)
            
            # Attempt to reconnect
            await self.reconnect_openai_client()
        except Exception as e:
            self.logger.error(f"Error in main loop: {str(e)}", exc_info=True)
        finally:
            await self.cleanup()

    async def process_audio(self):
        self.logger.info("Started audio processing")
        try:
            while self.is_running:
                try:
                    audio_chunk = await self.audio_capture.read_audio()
                except Exception as e:
                    self.logger.error(f"Error reading audio: {str(e)}", exc_info=True)
                    break  # Exit the loop if we can't read audio
                is_speech = await self.audio_capture.is_speech(audio_chunk)

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
        except asyncio.CancelledError:
            self.logger.info("Audio processing task cancelled")
        finally:
            self.logger.info("Stopped audio processing")

    async def send_buffer_to_api(self):
        if len(self.audio_buffer) == 0:
            self.logger.info("Audio buffer is empty. Not sending to API.")
            self.audio_buffer = b""
            self.buffer_ready.clear()
            return
        
        try:
            self.waiting_for_response = True
            api_call_made = await self.send_audio_to_api(self.audio_buffer)
            if api_call_made:
                self.audio_buffer = b""
                self.buffer_ready.clear()
                self.cooldown_active = True
                asyncio.create_task(self.cooldown_timer())
            else:
                self.logger.info("Audio buffer was not sent to API. Clearing buffer.")
                self.audio_buffer = b""
                self.buffer_ready.clear()
        except Exception as e:
            self.logger.error(f"Error in send_buffer_to_api: {str(e)}", exc_info=True)
        finally:
            self.waiting_for_response = False
            self.logger.debug("waiting_for_response set to False after send_buffer_to_api")

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
            await self.websocket_manager.broadcast_status("processing", False)
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
