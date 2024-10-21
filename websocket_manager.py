async def process_message(self, data, websocket):
    action = data.get('action')
    if action == 'pause_listening':
        await self.assistant.pause()
        await self.broadcast_status("Pausado", is_listening=False)
    elif action == 'resume_listening':
        await self.assistant.resume()
        await self.broadcast_status("En funcionamiento", is_listening=True)
