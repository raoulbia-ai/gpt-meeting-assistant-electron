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

  // Add a Pause/Resume button
  const pauseResumeButton = document.createElement('button')
  pauseResumeButton.textContent = 'Pause'
  pauseResumeButton.style.position = 'absolute'
  pauseResumeButton.style.top = '10px'
  pauseResumeButton.style.right = '10px'
  document.body.appendChild(pauseResumeButton)

  pauseResumeButton.addEventListener('click', () => {
    if (pauseResumeButton.textContent === 'Pause') {
      pauseResumeButton.textContent = 'Resume'
      win.webContents.send('togglePause', { action: 'pause_listening' })
    } else {
      pauseResumeButton.textContent = 'Pause'
      win.webContents.send('togglePause', { action: 'resume_listening' })
    }
  })
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
