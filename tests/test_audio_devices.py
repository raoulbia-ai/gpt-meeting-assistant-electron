import pyaudio

p = pyaudio.PyAudio()

print("Available audio devices:")
for i in range(p.get_device_count()):
    dev_info = p.get_device_info_by_index(i)
    print(f"Device {i}: {dev_info['name']}")
    print(f"  Max Input Channels: {dev_info['maxInputChannels']}")
    print(f"  Max Output Channels: {dev_info['maxOutputChannels']}")
    print(f"  Default Sample Rate: {dev_info['defaultSampleRate']}")
    print(f"  Input Latency: {dev_info['defaultLowInputLatency']} - {dev_info['defaultHighInputLatency']}")
    print(f"  Output Latency: {dev_info['defaultLowOutputLatency']} - {dev_info['defaultHighOutputLatency']}")
    print()

p.terminate()