# Voice Assistant Application

Welcome to the **Voice Assistant Application**! This open-source project is a real-time voice assistant that leverages OpenAI's API to process and respond to user speech. Using your microphone input, it captures audio, processes it, and provides intelligent responses, making it versatile for applications like transcription, voice commands, and interactive dialogues.

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
  - [Interacting with the Assistant](#interacting-with-the-assistant)
- [Configuration](#configuration)
- [Logging](#logging)
- [Testing](#testing)
- [Utilities](#utilities)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features

- **Real-time Audio Capture**: Captures audio from your microphone with adjustable settings for channels, rate, and chunk size.
- **OpenAI Integration**: Sends audio data to OpenAI's API for processing and receives responses.
- **WebSocket Communication**: Utilizes WebSockets for real-time communication between the backend and frontend.
- **Electron Frontend**: Provides a desktop application interface built with Electron and React.
- **Draggable Floating Prompter**: A customizable and movable UI component for displaying assistant responses.
- **Error Handling and Logging**: Comprehensive logging and error handling mechanisms for robust performance.
- **Extensible Architecture**: Modular design for easy extension and integration with other services.

## Screenshots

*(Include screenshots of the application in action.)*

## Prerequisites

- **Python 3.7+**
- **Node.js 14+**
- **npm**
- **An OpenAI API Key**: You need to have an API key from OpenAI to use their services.
- **PortAudio**: Required for PyAudio installation.
- **PyAudio**: For audio input/output in Python.
- **Electron**: For running the frontend application.

## Installation

### Backend Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/voice-assistant-application.git
   cd voice-assistant-application/backend
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Python Dependencies**

   Ensure you have PortAudio installed on your system, which is required for PyAudio.

   - On **Ubuntu/Debian**:

     ```bash
     sudo apt-get install libportaudio2
     ```

   - On **macOS** (using Homebrew):

     ```bash
     brew install portaudio
     ```

   Then install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Configuration**

   - **Environment Variables**:

     Set the `OPENAI_API_KEY` environment variable:

     - On **Linux/macOS**:

       ```bash
       export OPENAI_API_KEY='your_openai_api_key'
       ```

     - On **Windows**:

       ```cmd
       set OPENAI_API_KEY='your_openai_api_key'
       ```

   - **Configuration File**:

     The `config.py` file contains settings you can adjust:

     - `max_api_calls`: Maximum number of API calls (`-1` for unlimited).
     - `silence_threshold`, `cooldown_duration`: Silence detection settings.
     - `rate`, `channels`, `frame_duration_ms`: Audio settings.

### Frontend Setup

1. **Navigate to the Root Directory**

   ```bash
   cd ../  # Assuming you're in the backend directory
   ```

2. **Install Node.js Dependencies**

   ```bash
   npm install
   ```

3. **Build the Frontend**

   ```bash
   npm run build
   ```

4. **Ensure Electron is Installed**

   If Electron is not installed globally, you can install it as a dev dependency (already included in `package.json`):

   ```bash
   npm install electron --save-dev
   ```

## Usage

### Running the Application

#### Start the Backend Server

```bash
cd backend
python voice_assistant.py
```

- The application will prompt you to enter the maximum number of API calls. Enter `-1` for unlimited calls.
- The assistant will initialize and start listening for audio input.

#### Start the Frontend Application

In a new terminal window at the root of the project:

```bash
npm start
```

- This will build the frontend and launch the Electron application.
- The floating prompter UI should appear on your screen.

### Interacting with the Assistant

- **Voice Input**: Speak into your microphone; the assistant processes your speech in real-time.
- **Pause/Resume Listening**: Use the spacebar or the pause/resume button in the interface to control listening.
- **View Transcripts**: The assistant displays real-time transcripts of your speech.
- **Receive Responses**: Get responses from the OpenAI API based on your input.
- **Adjust Opacity**: Use the opacity slider to adjust the transparency of the floating prompter.
- **Move the Prompter**: Click and drag the top bar to reposition the floating prompter on your screen.

## Configuration

The application can be customized using the `config.py` file in the `backend` directory.

### Configuration Options

- **API Key and URL**: Set your OpenAI API key and endpoint URL.
- **Audio Settings**:
  - `rate`: Sample rate (default is 48000 Hz).
  - `channels`: Number of audio channels (default is 1).
  - `frame_duration_ms`: Duration of each audio frame in milliseconds.
- **Assistant Settings**:
  - `max_api_calls`: Maximum number of API calls (`-1` for unlimited).
  - `silence_threshold`: Threshold for detecting silence.
  - `cooldown_duration`: Duration to wait before listening again after a response.
  - `instructions`: Instructions or guidelines for the assistant's responses.

### Frontend Configuration

- **Opacity**: Adjusted within the UI using the slider.
- **Keyboard Shortcuts**:
  - **Spacebar**: Toggle pause/resume listening.
- **Window Behavior**:
  - The Electron window is set to always be on top and is transparent, providing an unobtrusive overlay.

## Logging

Logging is configured using the `common_logging.py` module in the `backend` directory. It sets up both file and console logging with options for rotation and formatting.

### Adjusting Logging Levels

You can adjust the logging level in your scripts when initializing the logger:

```python
from common_logging import setup_logging

logger = setup_logging('your_module_name', debug_to_console=True)
```

- **Parameters**:
  - `name`: Name of the logger.
  - `debug_to_console` (bool): If `True`, logs will also output to the console.
  - `filter_response_done` (bool): If `True`, applies a filter to only log specific messages.

### Log Files

- Logs are stored in the `logs` directory within `backend`.
- Each module has its own log file, e.g., `voice_assistant.log`, `openai_client.log`.

## Testing

The `tests` directory contains scripts to verify the functionality of audio devices and API interactions.

### Running Audio Tests

```bash
cd tests
python test_audio.py
```

- This script tests audio recording from your microphone and saves it to `output.wav`.
- Ensure your microphone is properly connected and recognized by the system.
- The script searches for a "Blue Yeti" microphone by default. Modify the device search in the script if you have a different microphone.

### Additional Tests

- **PulseAudio and PyAudio Tests**: `test_pulseaudio_and_pyaudio.py` can help diagnose audio issues on systems using PulseAudio.

## Utilities

### Kill Ports Script

The `utils/kill_ports.py` script checks for processes running on specific ports (e.g., 8000 and 3000) and terminates them. This is useful for ensuring that the required ports are free before starting the application.

#### Usage

```bash
cd utils
python kill_ports.py
```

- The script uses `lsof` to find and kill processes. It may require elevated permissions depending on your system configuration.
- Modify the script if you need to check different ports.

## Contributing

We welcome contributions from the community! To contribute:

1. **Fork the Repository**

2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/YourFeature
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add your message"
   ```

4. **Push to Your Fork**

   ```bash
   git push origin feature/YourFeature
   ```

5. **Create a Pull Request**

   - Navigate to the original repository and open a pull request.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- **OpenAI**: For providing the API that powers the assistant.
- **Electron**: For enabling the cross-platform desktop application.
- **Contributors**: Thanks to everyone who has contributed to this project.
- **Community**: For the support and feedback.

---

*Feel free to open an issue if you have questions or need assistance!*

---

If you have any other files or information you'd like to include or if there are specific sections you'd like to expand upon, please let me know, and I'll update the README accordingly.
