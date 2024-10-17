const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow () {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    transparent: false, // Change to false
    frame: true,        // Change to true
    backgroundColor: '#FFFFFF', // Set a visible background color
    hasShadow: true,
    visualEffectState: 'active'
  })

  win.loadFile('index.html')

  // Open DevTools by default
  win.webContents.openDevTools()
  
  win.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error(`Failed to load: ${errorDescription} (${errorCode})`);
  });

  // Make sure the window is always on top
  win.setAlwaysOnTop(true, 'floating')

  // Hide the window from the taskbar
  win.setSkipTaskbar(true)

  win.once('ready-to-show', () => {
    win.show()
  })

  // Add this line to focus the window
  win.focus()
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// Add these lines to handle any unhandled exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error)
})

// Add these lines to log when the app is ready
app.on('ready', () => {
  console.log('App is ready')
})
