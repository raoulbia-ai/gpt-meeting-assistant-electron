import asyncio
import websockets
import json
from common_logging import setup_logging

class WebSocketManager:
    def __init__(self, assistant):
        self.assistant = assistant
        self.clients = set()
        self.server = None
        self.logger = setup_logging('websocket_manager')
        self.is_paused = False

    async def start(self):
        self.server = await websockets.serve(self.handler, 'localhost', 8000)
        self.logger.info("WebSocket server started on ws://localhost:8000")

    async def handler(self, websocket, path):
        self.clients.add(websocket)
        self.logger.info(f"Client connected: {websocket.remote_address}")
        # Send initial status message
        await websocket.send(json.dumps({
            'type': 'status',
            'status': 'ready',
            'is_listening': self.assistant.is_running  # This should be False at startup
        }))
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.process_message(data, websocket)
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            self.logger.error(f"Error: {e}")
        finally:
            # Check if websocket is still in the set before removing
            if websocket in self.clients:
                self.clients.remove(websocket)
            self.logger.info(f"Client removed: {websocket.remote_address}")


    async def process_message(self, data, websocket):
        if data['type'] == 'control':
            action = data['action']
            if action == 'start_listening':
                await self.assistant.start_listening()
            elif action in ['pause', 'pause_listening']:
                await self.assistant.pause()  # Call the assistant's pause method
                self.logger.info("Listening paused")
                await self.broadcast_status("paused", False)  # Broadcast the pause status
            elif action in ['resume', 'resume_listening']:
                await self.assistant.resume()  # Call the assistant's resume method
                self.logger.info("Listening resumed")
            else:
                self.logger.warning(f"Unknown action received: {action}")

    async def broadcast_new_response(self):
        message = json.dumps({
            'type': 'new_response'
        })
        await self.broadcast(message)

    async def broadcast_status(self, status, is_listening):
        message = json.dumps({
            'type': 'status',
            'status': status,
            'is_listening': is_listening,
            'is_paused': self.assistant.is_paused
        })
        await self.broadcast(message)

    async def broadcast_transcript(self, transcript_delta):
        message = json.dumps({
            'type': 'transcript',
            'delta': transcript_delta
        })
        await self.broadcast(message)

    async def broadcast_response(self, response):
        message = json.dumps({
            'type': 'response',
            'data': response
        })
        await self.broadcast(message)

    async def broadcast_api_call_count(self, count):
        message = json.dumps({
            'type': 'api_call_count',
            'count': count
        })
        await self.broadcast(message)

    async def broadcast_error(self, error_message, error_code=None):
        message = json.dumps({
            'type': 'error',
            'error': {
                'message': error_message,
                'code': error_code or 'unknown_error'
            }
        })
        await self.broadcast(message)

    async def broadcast(self, message):
        disconnected_clients = []
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
        for client in disconnected_clients:
            self.clients.remove(client)
            self.logger.info(f"Removed disconnected client: {client.remote_address}")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")
