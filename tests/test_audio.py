import pyaudio
import wave
import sys

# Audio stream configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 48000  # Blue Yeti supports 48kHz
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

try:
    p = pyaudio.PyAudio()

    # Find the index of the Blue Yeti microphone
    blue_yeti_index = None
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if "Blue Microphones" in dev_info["name"]:
            blue_yeti_index = i
            break

    if blue_yeti_index is None:
        print("Blue Yeti microphone not found")
        p.terminate()
        sys.exit(1)

    print(f"Using Blue Yeti microphone (index {blue_yeti_index})")

    # Open the audio stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=blue_yeti_index,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    # Record audio in chunks and store in frames
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio to a WAV file
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"* audio saved to {WAVE_OUTPUT_FILENAME}")

except OSError as e:
    print(f"Error: {e}")
    print("There might be an issue with your audio configuration.")
    print("Please ensure your Blue Yeti microphone is properly connected and recognized by the system.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)