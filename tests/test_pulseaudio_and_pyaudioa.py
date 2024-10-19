import pyaudio
import subprocess
import os
import time

def check_pulseaudio_status():
    """Check if PulseAudio is running."""
    try:
        subprocess.run(["pulseaudio", "--check"], check=True)
        print("PulseAudio is running.")
    except subprocess.CalledProcessError:
        print("PulseAudio is NOT running.")
        return False
    return True

def list_pulseaudio_sources():
    """List PulseAudio sources (microphones, etc.)."""
    print("Listing PulseAudio sources (microphones):")
    subprocess.run(["pactl", "list", "short", "sources"])

def record_with_parecord():
    """Test recording with PulseAudio's parecord."""
    test_file = "test_pulse_audio.wav"
    print(f"Recording audio with parecord... (5 seconds)")
    try:
        subprocess.run(["parecord", "--device=alsa_input.usb-Generic_Blue_Microphones_LT_230112082441AD02000F_111000-00.analog-stereo", test_file], timeout=5)
        print(f"Recording completed: {test_file}")
        return True
    except subprocess.TimeoutExpired:
        print("parecord completed.")
        return True
    except Exception as e:
        print(f"Error during parecord: {e}")
        return False

def playback_with_paplay():
    """Test playback of the recorded file."""
    test_file = "test_pulse_audio.wav"
    if os.path.exists(test_file):
        print(f"Playing back the recorded file: {test_file}")
        subprocess.run(["paplay", test_file])
    else:
        print(f"No recorded file found at {test_file}")

def test_pyaudio_capture():
    """Test capturing audio using PyAudio."""
    print("Testing audio capture using PyAudio...")
    
    # Configure PyAudio settings
    chunk = 1024  # Buffer size
    format = pyaudio.paInt16  # 16-bit PCM
    channels = 1  # Mono channel
    rate = 44100  # Sample rate
    
    p = pyaudio.PyAudio()
    
    # Try listing available audio input devices
    print("Listing available PyAudio devices:")
    device_count = p.get_device_count()
    for i in range(device_count):
        dev_info = p.get_device_info_by_index(i)
        print(f"{i}: {dev_info['name']} - Channels: {dev_info['maxInputChannels']}")

    # Try opening the stream for recording
    try:
        stream = p.open(format=format, 
                        channels=channels, 
                        rate=rate, 
                        input=True, 
                        frames_per_buffer=chunk)

        print("Recording 5 seconds of audio with PyAudio...")
        frames = []
        for i in range(0, int(rate / chunk * 5)):
            data = stream.read(chunk)
            frames.append(data)

        # Stop the stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save the recorded audio to a WAV file
        with open("test_pyaudio_capture.raw", "wb") as f:
            f.write(b"".join(frames))
        print("Recording saved to test_pyaudio_capture.raw")
        return True
    except Exception as e:
        print(f"Error in PyAudio capture: {e}")
        return False

if __name__ == "__main__":
    # Check if PulseAudio is running
    if not check_pulseaudio_status():
        print("PulseAudio must be running for this test. Please start PulseAudio.")
        exit(1)

    # List PulseAudio sources
    list_pulseaudio_sources()

    # Test recording using PulseAudio's parecord
    if record_with_parecord():
        # Test playback using PulseAudio's paplay
        playback_with_paplay()
    else:
        print("Skipping playback due to recording failure.")

    # Test capturing audio using PyAudio
    test_pyaudio_capture()
