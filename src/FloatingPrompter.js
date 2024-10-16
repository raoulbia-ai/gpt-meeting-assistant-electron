import React, { useState, useCallback, useRef, useEffect } from 'react';
import Draggable from 'react-draggable';

export default function FloatingPrompter() {
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [displayedResponse, setDisplayedResponse] = useState('');
  const [error, setError] = useState('');
  const [isMinimized, setIsMinimized] = useState(false);
  const [opacity, setOpacity] = useState(0.8);
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

  const handleWebSocketMessage = useCallback((data) => {
    switch (data.type) {
      case 'status':
        setIsListening(data.is_listening);
        if (data.status === 'processing') {
          setCurrentResponse('');
        }
        break;
      case 'response':
        handleAssistantResponse(data.data);
        break;
      case 'error':
        setError(data.error.message);
        setShowAlert(true);
        break;
      default:
        console.warn('Unknown message type:', data.type);
    }
  }, []);

  const handleAssistantResponse = useCallback((responseData) => {
    if (responseData.type === 'response.audio_transcript.delta') {
      setCurrentResponse(prev => prev + (responseData.delta || ''));
    } else if (responseData.type === 'response.complete') {
      setDisplayedResponse(currentResponse);
      setCurrentResponse('');
    }
  }, [currentResponse]);

  const sendWebSocketMessage = useCallback((type, payload) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, ...payload }));
    } else {
      setError('WebSocket is not connected');
      setShowAlert(true);
    }
  }, []);

  const toggleListening = () => {
    if (isListening) {
      sendWebSocketMessage('control', { action: 'stop_listening' });
    } else {
      sendWebSocketMessage('control', { action: 'start_listening' });
    }
    setIsListening(!isListening);
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

  return (
    <Draggable handle=".drag-handle">
      <div ref={containerRef} style={{
        position: 'fixed',
        top: '20px',
        left: '20px',
        width: '600px',
        backgroundColor: `rgba(0, 0, 0, ${opacity})`,
        color: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        fontFamily: 'Arial, sans-serif',
        WebkitAppRegion: 'drag',
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
            <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', margin: 0 }}>Interview Companion</h2>
          </div>
          <div>
            <button onClick={toggleMinimize} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '1rem', marginRight: '8px', WebkitAppRegion: 'no-drag' }}>
              {isMinimized ? '🗖' : '🗕'}
            </button>
            <button onClick={() => window.close()} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '1rem', WebkitAppRegion: 'no-drag' }}>
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
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: isListening ? `rgba(245, 101, 101, ${opacity})` : `rgba(66, 153, 225, ${opacity})`,
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '1rem',
                marginBottom: '16px',
                WebkitAppRegion: 'no-drag',
              }}
            >
              {isListening ? 'Stop Listening' : 'Start Listening'}
            </button>
            
            <div style={{
              height: '200px',
              overflowY: 'auto',
              marginBottom: '16px',
              backgroundColor: `rgba(30, 30, 30, ${opacity * 0.7})`,
              padding: '12px',
              borderRadius: '4px',
              fontSize: '1.1rem',
              lineHeight: '1.5',
            }}>
              <pre style={{ whiteSpace: 'pre-wrap', color: '#63b3ed', margin: 0 }}>
                {displayedResponse}
                {currentResponse && (
                  <>
                    {displayedResponse && '\n\n'}
                    <span style={{ color: '#48bb78' }}>{currentResponse}</span>
                  </>
                )}
              </pre>
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