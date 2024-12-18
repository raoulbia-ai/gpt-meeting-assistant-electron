import React, { useState, useCallback, useRef, useEffect } from 'react';
import Draggable from 'react-draggable';

export default function FloatingPrompter() {
  const [isConnected, setIsConnected] = useState(false);
  const [apiCallCount, setApiCallCount] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [displayedResponse, setDisplayedResponse] = useState('');
  const [error, setError] = useState('');
  const [isMinimized, setIsMinimized] = useState(false);
  const [opacity, setOpacity] = useState(0.4);
  const [showAlert, setShowAlert] = useState(false);
  const [backendReady, setBackendReady] = useState(false);

  const ws = useRef(null);
  const containerRef = useRef(null);

  const connectWebSocket = useCallback(() => {
    ws.current = new WebSocket('ws://localhost:8000');
    
    ws.current.onopen = () => {
      setIsConnected(true);
      setBackendReady(true);
    };
    ws.current.onclose = () => setIsConnected(false);
    ws.current.onerror = () => {
      setError('WebSocket error occurred');
      setShowAlert(true);
    };
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
  }, []);

  const [lastStatus, setLastStatus] = useState({ is_listening: false, is_paused: false });

  const handleWebSocketMessage = useCallback(
    (data) => {
      switch (data.type) {
        case 'status':
          setIsListening(data.is_listening);
          setIsPaused(data.is_paused);
          break;
          
          case 'transcript':
            // Handle transcript message
            setCurrentResponse(prev => prev + (data.transcript || ''));
            break;
          case 'new_response':
          setDisplayedResponse('');
          setCurrentResponse('');
          break;
          
        case 'response':
          handleAssistantResponse(data.data);
          break;

        case 'api_call_count':
          setApiCallCount(data.count);  // Update the API call count state
          break;
          
        case 'error':
          setError(data.error.message);
          setShowAlert(true);
          break;
          
        default:
          console.warn('Unknown message type:', data.type);
      }
    },
    [lastStatus, handleAssistantResponse]
  );
  

  const handleAssistantResponse = useCallback((responseData) => {
    if (responseData.type === 'response.audio_transcript.delta') {
      if (!currentResponse && displayedResponse) {
        setDisplayedResponse('');
      }
      setCurrentResponse(prev => prev + (responseData.delta || ''));
    } else if (responseData.type === 'response.complete') {
      setDisplayedResponse(currentResponse);
      setCurrentResponse('');
      console.log('Complete response received. Pausing listening...');
    }
  }, [currentResponse]);
  
  
    
    const toggleListening = () => {
      if (isListening) {
        sendWebSocketMessage('control', { action: 'stop_listening' });
      } else {
        sendWebSocketMessage('control', { action: 'start_listening' });
      }
      setIsListening(!isListening);
    };
  

  const sendWebSocketMessage = useCallback((type, payload) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, ...payload }));
    } else {
      setError('WebSocket is not connected');
      setShowAlert(true);
    }
  }, []);



  const togglePauseResume = () => {
    const newIsPaused = !isPaused;
    setIsPaused(newIsPaused);  // Update the state immediately
    sendWebSocketMessage('control', { action: newIsPaused ? 'pause_listening' : 'resume_listening' });
  };

  const toggleMinimize = () => setIsMinimized(!isMinimized);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connectWebSocket]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.code === 'Space') {
        event.preventDefault(); // Prevent default behavior like scrolling
        event.stopPropagation();   // Prevent the event from triggering other handlers
        togglePauseResume();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    // Cleanup the event listener on unmount
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isPaused]); // Include isPaused in the dependency array

  return (
    <Draggable handle=".drag-handle">
      <div ref={containerRef} style={{
        position: 'fixed',
        top: '20px',
        left: '20px',
        width: '600px',
        backgroundColor: `rgba(0, 0, 0, ${opacity})`, // Use opacity state
        color: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        fontFamily: 'Arial, sans-serif',
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px',
          backgroundColor: `rgba(50, 50, 50, ${opacity * 0.9})`,
          borderTopLeftRadius: '8px',
          borderTopRightRadius: '8px',
          WebkitAppRegion: 'drag',
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span className="drag-handle" style={{ cursor: 'move', marginRight: '8px', WebkitAppRegion: 'drag' }}>☰</span>

          </div>
          <div>
            <button onClick={toggleMinimize} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '1rem', marginRight: '8px', WebkitAppRegion: 'no-drag' }}>
              {isMinimized ? '🗖' : '🗕'}
            </button>
            <button
              onClick={togglePauseResume}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                fontSize: '1rem',
                marginRight: '8px',
                WebkitAppRegion: 'no-drag',
              }}
            >
              {isPaused ? 'Resume' : 'Pause'}
            </button>

            <button tabIndex="-1" onClick={() => window.close()} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '1rem', WebkitAppRegion: 'no-drag' }}>
              ✖
            </button>
          </div>
        </div>
        
        {!backendReady && (
          <div style={{ padding: '16px' }}>
            <button 
              onClick={connectWebSocket}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: `rgba(66, 153, 225, ${opacity})`,
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '1rem',
                WebkitAppRegion: 'no-drag',
              }}
            >
              Connect to Backend
            </button>
          </div>
        )}

        {backendReady && !isMinimized && (
          <div style={{ padding: '16px' }}>
          <button 
            onClick={toggleListening}
            disabled={isPaused}  // Disable when paused
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: isListening ? `rgba(245, 101, 101, ${opacity})` : `rgba(66, 153, 225, ${opacity})`,
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '1rem',
              marginBottom: '16px',
              WebkitAppRegion: 'no-drag',
            }}
          >
            {isListening ? 'Stop Listening' : 'Start Listening'}
          </button>

            
            <div style={{ 
              height: '200px',
              overflowY: 'auto', // Enable vertical scrolling
              marginBottom: '16px',
              backgroundColor: `rgba(30, 30, 30, ${opacity * 0.7})`,
              padding: '12px',
              borderRadius: '4px',
              fontSize: '18px',
              color: 'white',
              lineHeight: '1.5',
              }}>
              <pre style={{ whiteSpace: 'pre-wrap', color: 'white', margin: 0 }}>
                {displayedResponse}
                {currentResponse && (
                  <>
                    {displayedResponse && '\n\n'}
                    <span style={{ color: 'white' }}>{currentResponse}</span>
                  </>
                )}
              </pre>
            </div>
            
            <div style={{ padding: '2px', color: 'white' }}>
              <p>API Calls Made: {apiCallCount}</p>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px' }}>Opacity</label>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={opacity}
                onChange={(e) => setOpacity(parseFloat(e.target.value))}
                style={{ width: '100%', WebkitAppRegion: 'no-drag' }}
              />
            </div>
          </div>
        )}

        {showAlert && (
          <div style={{
            position: 'absolute',
            bottom: '20px',
            left: '20px',
            right: '20px',
            backgroundColor: 'rgba(254, 215, 215, 0.9)',
            color: '#9b2c2c',
            padding: '12px',
            borderRadius: '4px',
            fontSize: '0.875rem',
          }}>
            {error}
            <button
              onClick={() => setShowAlert(false)}
              style={{
                background: 'none',
                border: 'none',
                color: '#9b2c2c',
                cursor: 'pointer',
                float: 'right',
                fontSize: '1rem',
              }}
            >
              ✖
            </button>
          </div>
        )}
      </div>
    </Draggable>
  );
}
