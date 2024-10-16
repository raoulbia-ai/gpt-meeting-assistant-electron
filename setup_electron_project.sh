#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Function to handle errors
handle_error() {
    echo "An error occurred during setup. Please check the output above for details."
    exit 1
}

# Set up error handling
trap 'handle_error' ERR

# Create project directory
mkdir interview-companion-electron
cd interview-companion-electron

# Create main.js
cat > main.js << EOL
const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow () {
  const win = new BrowserWindow({
    width: 400,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  win.loadFile('index.html')
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})
EOL

# Create index.html
cat > index.html << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Interview Companion</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body>
    <div id="root"></div>
    <script src="renderer.js"></script>
</body>
</html>
EOL

# Create renderer.js
cat > renderer.js << EOL
import React from 'react';
import ReactDOM from 'react-dom';
import FloatingPrompter from './FloatingPrompter';

ReactDOM.render(
  <React.StrictMode>
    <FloatingPrompter />
  </React.StrictMode>,
  document.getElementById('root')
);
EOL

# Create FloatingPrompter.js
cat > FloatingPrompter.js << EOL
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cn } from '../lib/utils';
import Draggable from 'react-draggable';
import { Button, Card, AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogAction, Slider } from '@material-ui/core';
import { Close, Minimize, Maximize, DragHandle } from '@material-ui/icons';

export default function FloatingPrompter() {
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [displayedResponse, setDisplayedResponse] = useState('');
  const [error, setError] = useState('');
  const [isMinimized, setIsMinimized] = useState(false);
  const [opacity, setOpacity] = useState(0.8);
  const [showAlert, setShowAlert] = useState(false);

  const ws = useRef(null);
  const containerRef = useRef(null);

  const connectWebSocket = useCallback(() => {
    ws.current = new WebSocket('ws://localhost:8000');
    
    ws.current.onopen = () => setIsConnected(true);
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

  // Add other functions and useEffect hooks here...

  return (
    <>
      <Draggable handle=".drag-handle">
        <Card ref={containerRef} className="fixed top-0 left-0 w-96 bg-black text-white p-4 rounded-lg shadow-lg" style={{ opacity }}>
          {/* Add your UI components here */}
        </Card>
      </Draggable>

      <AlertDialog open={showAlert} onClose={() => setShowAlert(false)}>
        {/* Add AlertDialog content here */}
      </AlertDialog>
    </>
  );
}
EOL

# Initialize npm project and create package.json
npm init -y

# Modify package.json
npm pkg set main="main.js"
npm pkg set scripts.start="electron ."
npm pkg set scripts.build="electron-builder"

# Install dependencies
npm install react react-dom react-draggable @material-ui/core @material-ui/icons
npm install --save-dev electron electron-builder

echo "Electron app setup complete!"
echo "To run the app, use: npm start"
echo "To build the app, use: npm run build"
echo ""
echo "Next steps for customization:"
echo "1. Review and update FloatingPrompter.js to match your exact component logic"
echo "2. Adjust the WebSocket URL in FloatingPrompter.js if your server isn't running on localhost:8000"
echo "3. Add any additional utility functions or components you're using"
echo "4. Customize the UI in FloatingPrompter.js to match your desired layout and styling"
echo "5. Update main.js if you need to adjust window size, position, or other Electron-specific settings"
echo ""
echo "Refer to the Electron documentation (https://www.electronjs.org/docs) for more advanced customizations."