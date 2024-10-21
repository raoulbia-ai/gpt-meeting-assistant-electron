function togglePauseResume() {
  const newIsPaused = !isPaused;
  setIsPaused(newIsPaused);
  sendWebSocketMessage('control', { action: newIsPaused ? 'pause_listening' : 'resume_listening' });
