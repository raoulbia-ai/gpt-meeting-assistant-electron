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
    transparent: true,
    frame: false,
    backgroundColor: '#00000000',
    hasShadow: false,
    visualEffectState: 'active'
  })

  win.loadFile('index.html')

  // Uncomment the following line to open DevTools by default
  // win.webContents.openDevTools()

  // Make sure the window is always on top
  win.setAlwaysOnTop(true, 'floating')

  // Hide the window from the taskbar
  win.setSkipTaskbar(true)

  // Add these lines to show the window after it's created
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