#!/bin/bash

# Step 1: Identify the process using the sound devices
echo "Identifying processes using sound devices..."
fuser_output=$(sudo fuser /dev/snd/* 2>/dev/null)

if [ -z "$fuser_output" ]; then
  echo "No processes are using the sound devices."
else
  # Extract the PID from the fuser output
  pids=$(echo $fuser_output | tr ' ' '\n' | grep -o '[0-9]*')
  echo "Processes using sound devices: $pids"

  # Step 2: Kill the processes using the sound devices
  for pid in $pids; do
    echo "Killing process with PID: $pid"
    sudo kill $pid
  done

  # Verify if the processes were successfully stopped
  fuser_check=$(sudo fuser /dev/snd/* 2>/dev/null)
  if [ -z "$fuser_check" ]; then
    echo "All sound device processes have been stopped."
  else
    echo "Some processes are still using sound devices. Please check manually."
    exit 1
  fi
fi

# Step 3: Reload ALSA
echo "Reloading ALSA sound drivers..."
sudo alsa force-reload

# Step 4: Test using arecord
echo "Testing microphone with arecord..."
arecord -D plughw:2,0 -f S16_LE -r 48000 -d 5 test.wav

if [ -f "test.wav" ]; then
  echo "Recording completed. You can play back the test.wav file."
else
  echo "Recording failed. Please check the microphone settings."
fi

# Final message
echo "Script completed. Test the microphone and your Python script."
