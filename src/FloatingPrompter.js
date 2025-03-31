import React, { useState, useCallback, useRef, useEffect } from 'react';
import Draggable from 'react-draggable';
import './FloatingPrompter.css'; // Import the CSS file

// --- Constants ---
const WEBSOCKET_URL = 'ws://localhost:8000';
const RECONNECT_DELAY_MS = 5000; // 5 seconds
const MAX_RECONNECT_ATTEMPTS = 5;
const INITIAL_OPACITY = 0.6;

// --- Helper Function ---
const getBackgroundColorWithOpacity = (baseColor, opacity) => {
  // Basic function to apply opacity to an rgba color string base
  // Assumes baseColor is like 'rgba(r, g, b,'
  return `${baseColor} ${opacity})`;
};

// --- Sub-components ---

const PrompterHeader = React.memo(({ opacity, isMinimized, isPaused, onMinimize, onPauseResume, onClose }) => (
  <div
    className="prompter-header"
    style={{ backgroundColor: getBackgroundColorWithOpacity('rgba(50, 50, 50,', opacity * 0.9) }}
  >
    <div style={{ display: 'flex', alignItems: 'center' }}>
      <span className="drag-handle" aria-label="Drag handle">☰</span>
    </div>
    <div className="header-controls">
      <button onClick={onMinimize} aria-label={isMinimized ? "Maximize" : "Minimize"}>
        {isMinimized ? '🗖' : '🗕'}
      </button>
      <button onClick={onPauseResume} aria-label={isPaused ? "Resume Listening" : "Pause Listening"}>
        {isPaused ? 'Resume' : 'Pause'}
      </button>
      <button onClick={onClose} aria-label="Close Prompter" tabIndex="-1">
        ✖
      </button>
    </div>
  </div>
));

const ConnectionStatus = React.memo(({ isConnected, isConnecting, reconnectAttempts }) => {
    if (isConnecting && reconnectAttempts > 0) { // Show attempts only during reconnection
        return <div className="status-bar">Connecting (Attempt {reconnectAttempts})...</div>;
    }
     if (isConnecting && reconnectAttempts === 0) { // Initial connection attempt
        return <div className="status-bar">Connecting...</div>;
    }
    if (!isConnected && !isConnecting) { // Disconnected state
        return <div className="status-bar">Disconnected. Will attempt to reconnect.</div>;
    }
    // Only show "Connected" if actually connected and not in a connecting/reconnecting state
    if (isConnected && !isConnecting) {
       return <div className="status-bar">Connected</div>;
    }
    return null; // Don't show anything if state is inconsistent
});


const ConnectButton = React.memo(({ onClick, isConnecting }) => (
  <button
    className="prompter-button connect-button"
    onClick={onClick}
    disabled={isConnecting}
    aria-label="Connect to Backend"
  >
    {isConnecting ? 'Connecting...' : 'Connect to Backend'}
  </button>
));

const ListeningButton = React.memo(({ isListening, isPaused, onClick, opacity }) => (
  <button
    className={`prompter-button ${isListening ? 'listening-button-active' : 'listening-button-inactive'}`}
    onClick={onClick}
    disabled={isPaused}
    style={{ '--bg-opacity': opacity }} // Pass opacity as CSS variable
    aria-label={isListening ? "Stop Listening" : "Start Listening"}
  >
    {isListening ? 'Stop Listening' : 'Start Listening'}
  </button>
));

const ResponseDisplay = React.memo(({ displayedResponse, currentResponse, opacity }) => (
  <div
    className="response-display"
    style={{ backgroundColor: getBackgroundColorWithOpacity('rgba(30, 30, 30,', opacity * 0.7) }}
    aria-live="polite" // Announce changes to screen readers
  >
    <pre>
      {displayedResponse}
      {currentResponse && (
        <>
          {displayedResponse ? '\n\n' : ''} {/* Add spacing only if there's prior displayed text */}
          <span className="current-response-text">{currentResponse}</span>
        </>
      )}
    </pre>
  </div>
));

const StatusBar = React.memo(({ apiCallCount }) => (
  <div className="status-bar">
    <p>API Calls Made: {apiCallCount}</p>
  </div>
));

const OpacitySlider = React.memo(({ opacity, onChange }) => (
  <div className="opacity-control">
    <label htmlFor="opacity-slider">Opacity</label>
    <input
      id="opacity-slider" // Associate label with input
      type="range"
      min="0.1"
      max="1"
      step="0.1"
      value={opacity}
      onChange={onChange}
      aria-label="Adjust prompter opacity"
    />
  </div>
));

const ErrorAlert = React.memo(({ error, onClose }) => (
  <div className="error-alert" role="alert">
    {error}
    <button
      className="error-alert-close-button"
      onClick={onClose}
      aria-label="Close error message"
    >
      ✖
    </button>
  </div>
));


// --- Main Component ---

export default function FloatingPrompter() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [apiCallCount, setApiCallCount] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [currentResponse, setCurrentResponse] = useState(''); // Streaming response part
  const [displayedResponse, setDisplayedResponse] = useState(''); // Completed response part
  const [error, setError] = useState('');
  const [isMinimized, setIsMinimized] = useState(false);
  const [opacity, setOpacity] = useState(INITIAL_OPACITY);
  const [showAlert, setShowAlert] = useState(false);
  const [backendReady, setBackendReady] = useState(false); // Tracks if initial connection succeeded

  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const containerRef = useRef(null); // Ref for the main draggable container

  // --- WebSocket Message Sending ---
  const sendWebSocketMessage = useCallback((type, payload) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, ...payload }));
    } else {
      console.error('WebSocket is not connected or not ready.');
      setError('WebSocket is not connected. Cannot send message.');
      setShowAlert(true);
      // Optionally attempt to reconnect here if sending fails
      // connectWebSocket();
    }
  }, []); // No dependencies needed as ws.current is a ref

  // --- Response Handling ---
  const handleAssistantResponse = useCallback((responseData) => {
    // Clarified logic: Always append delta, clear displayed on new stream if needed.
    if (responseData?.type === 'response.audio_transcript.delta') {
       // If we start receiving delta and there's already a displayed response,
       // it implies a new response sequence is starting. Clear the old displayed response.
       // However, only clear if currentResponse is also empty, meaning it's truly the start.
      if (!currentResponse && displayedResponse) {
         setDisplayedResponse('');
      }
      setCurrentResponse(prev => prev + (responseData.delta || ''));
    } else if (responseData?.type === 'response.complete') {
      // When complete, move the fully streamed response to displayedResponse
      // and clear the current streaming response.
      setDisplayedResponse(prev => prev + currentResponse); // Append current stream to displayed
      setCurrentResponse(''); // Clear the stream buffer
      console.log('Complete response received.');
      // Optionally pause listening automatically after a complete response:
      // sendWebSocketMessage('control', { action: 'pause_listening' });
      // setIsPaused(true); // Need to manage state correctly if doing this
    }
  }, [currentResponse, displayedResponse]); // Dependencies: currentResponse for logic, displayedResponse for clearing

  // --- WebSocket Message Receiving ---
  const handleWebSocketMessage = useCallback((event) => {
    try {
      const data = JSON.parse(event.data);
      switch (data?.type) {
        case 'status':
          setIsListening(data.is_listening);
          setIsPaused(data.is_paused);
          break;
        case 'transcript': // Assuming transcript might still be used for raw user speech
           // Decide how to display raw transcript if needed, e.g., in a separate area
           // console.log("Transcript:", data.transcript);
           // For now, let's append it to currentResponse for visibility
           // setCurrentResponse(prev => prev + (data.transcript || ''));
          break;
        case 'new_response':
           // Signal that a new response sequence is starting.
           // Clear both displayed and current responses.
           setDisplayedResponse('');
           setCurrentResponse('');
           break;
        case 'response': // This wraps the assistant's response chunks
          handleAssistantResponse(data.data);
          break;
        case 'api_call_count':
          setApiCallCount(data.count);
          break;
        case 'error':
          const errorMsg = data.error?.message || 'An unknown backend error occurred.';
          setError(errorMsg);
          setShowAlert(true);
          console.error('Backend Error:', errorMsg);
          break;
        default:
          console.warn('Unknown message type:', data?.type);
      }
    } catch (parseError) {
      console.error('Failed to parse WebSocket message:', parseError);
      setError('Received malformed data from backend.');
      setShowAlert(true);
    }
  }, [handleAssistantResponse]); // Dependency: handleAssistantResponse

  // --- WebSocket Connection Logic ---
  const connectWebSocket = useCallback(() => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already open.');
      return;
    }
     if (isConnecting) {
      console.log('Connection attempt already in progress.');
      return;
    }

    clearTimeout(reconnectTimeout.current); // Clear any pending reconnect timeout
    setIsConnecting(true);
    setError(''); // Clear previous errors
    setShowAlert(false);

    console.log(`Attempting to connect WebSocket (Attempt ${reconnectAttempts + 1})...`);
    ws.current = new WebSocket(WEBSOCKET_URL);

    ws.current.onopen = () => {
      console.log('WebSocket Connected');
      setIsConnected(true);
      setIsConnecting(false);
      setBackendReady(true); // Mark backend as ready on first successful connect
      setReconnectAttempts(0); // Reset attempts on successful connection
    };

    ws.current.onclose = (event) => {
      console.log('WebSocket Disconnected:', event.reason, `Code: ${event.code}`);
      setIsConnected(false);
      setIsConnecting(false);
      // Don't set backendReady to false here, keep it true once initially connected

      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        setReconnectAttempts(prev => prev + 1);
        console.log(`Scheduling reconnect attempt ${reconnectAttempts + 1} in ${RECONNECT_DELAY_MS / 1000}s`);
        reconnectTimeout.current = setTimeout(connectWebSocket, RECONNECT_DELAY_MS);
      } else {
        console.error('Max reconnect attempts reached.');
        setError('Failed to connect to the backend after multiple attempts.');
        setShowAlert(true);
      }
    };

    ws.current.onerror = (errorEvent) => {
      console.error('WebSocket Error:', errorEvent);
      // onclose will usually be called after onerror, triggering reconnect logic
      // Only set error if not already trying to reconnect
      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
         setError('WebSocket connection error.');
         setShowAlert(true);
      }
       setIsConnecting(false); // Ensure connecting state is reset on error
    };

    ws.current.onmessage = handleWebSocketMessage;

  }, [reconnectAttempts, isConnecting, handleWebSocketMessage]); // Dependencies for connection logic

  // --- Effects ---

  // Initial connection and cleanup
  useEffect(() => {
    connectWebSocket(); // Attempt initial connection on mount

    return () => {
      clearTimeout(reconnectTimeout.current); // Clear timeout on unmount
      if (ws.current) {
        ws.current.close(); // Close WebSocket connection
        console.log('WebSocket connection closed on component unmount.');
      }
    };
  }, [connectWebSocket]); // connectWebSocket has its own dependencies

  // Keyboard listener for Space bar (Pause/Resume)
  const togglePauseResume = useCallback(() => {
    const newIsPaused = !isPaused;
    // Optimistically update UI, then send message
    setIsPaused(newIsPaused);
    sendWebSocketMessage('control', { action: newIsPaused ? 'pause_listening' : 'resume_listening' });
  }, [isPaused, sendWebSocketMessage]); // Dependencies: isPaused, sendWebSocketMessage

  useEffect(() => {
    const handleKeyDown = (event) => {
      // Use event.key for modern browsers, fallback to event.code if needed
      if (event.key === ' ' || event.code === 'Space') {
        // Check if the event target is an input field or similar, to avoid interfering
        const targetTagName = event.target?.tagName?.toLowerCase();
        if (targetTagName !== 'input' && targetTagName !== 'textarea' && targetTagName !== 'select') {
            event.preventDefault(); // Prevent default space bar behavior (e.g., scrolling)
            event.stopPropagation(); // Stop the event from bubbling up
            togglePauseResume();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [togglePauseResume]); // Dependency: togglePauseResume callback

  // --- UI Event Handlers ---
  const handleToggleListening = useCallback(() => {
    // Optimistically update UI? Maybe not best here, wait for status update?
    // Let's send the command and let the status message update the state.
    if (isListening) {
      sendWebSocketMessage('control', { action: 'stop_listening' });
    } else {
      sendWebSocketMessage('control', { action: 'start_listening' });
    }
    // setIsListening(!isListening); // Avoid optimistic update for listening state
  }, [isListening, sendWebSocketMessage]);

  const handleToggleMinimize = useCallback(() => setIsMinimized(prev => !prev), []);
  const handleOpacityChange = useCallback((e) => setOpacity(parseFloat(e.target.value)), []);
  const handleCloseError = useCallback(() => setShowAlert(false), []);
  const handleCloseWindow = useCallback(() => window.close(), []);


  // --- Render ---
  return (
    <Draggable handle=".drag-handle" nodeRef={containerRef}>
      <div
        ref={containerRef}
        className="prompter-container"
        style={{ backgroundColor: getBackgroundColorWithOpacity('rgba(0, 0, 0,', opacity) }}
      >
        <PrompterHeader
          opacity={opacity}
          isMinimized={isMinimized}
          isPaused={isPaused}
          onMinimize={handleToggleMinimize}
          onPauseResume={togglePauseResume} // Use the stable callback
          onClose={handleCloseWindow}
        />

        {!backendReady && !isConnecting && reconnectAttempts >= MAX_RECONNECT_ATTEMPTS && (
             <div className="prompter-content">
                <ConnectButton onClick={connectWebSocket} isConnecting={isConnecting} />
             </div>
        )}

         {/* Show connection status indicator */}
         <ConnectionStatus
            isConnected={isConnected}
            isConnecting={isConnecting}
            reconnectAttempts={reconnectAttempts}
         />


        {backendReady && !isMinimized && (
          <div className="prompter-content">
            <ListeningButton
              isListening={isListening}
              isPaused={isPaused}
              onClick={handleToggleListening}
              opacity={opacity}
            />
            <ResponseDisplay
              displayedResponse={displayedResponse}
              currentResponse={currentResponse}
              opacity={opacity}
            />
            <StatusBar apiCallCount={apiCallCount} />
            <OpacitySlider opacity={opacity} onChange={handleOpacityChange} />
          </div>
        )}

        {showAlert && (
          <ErrorAlert error={error} onClose={handleCloseError} />
        )}
      </div>
    </Draggable>
  );
}
