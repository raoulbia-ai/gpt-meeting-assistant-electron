import asyncio
import subprocess
import os
import signal
from websocket_manager import WebSocketManager

# Function to check if anything is running on port 8000 and kill it
def kill_process_on_port(port):
    try:
        # Get the process running on the specified port
        result = subprocess.run(
            ["lsof", "-t", f"-i:{port}"], capture_output=True, text=True
        )
        pids = result.stdout.strip().split('\n')  # Split by newlines

        if pids and pids[0]:  # Check if the list is not empty
            for pid in pids:
                print(f"Process running on port {port}: PID {pid}")
                # Kill the process
                os.kill(int(pid), signal.SIGKILL)
                print(f"Killed process {pid} running on port {port}.")
        else:
            print(f"No process running on port {port}.")
    except Exception as e:
        print(f"Error occurred while killing the process on port {port}: {e}")

async def main():
    # Kill any process running on port 8000 and 3000 before starting the server
    kill_process_on_port(8000)
    kill_process_on_port(3000)

    # Uncomment the following lines to start the WebSocket server
    # manager = WebSocketManager(host="localhost", port=8000)
    # await manager.start()
    # print("WebSocket server started. Open test/websocket-test-client.html to begin testing.")
    
    # try:
    #     while True:
    #         await asyncio.sleep(1)
    # except KeyboardInterrupt:
    #     print("Shutting down...")
    # finally:
    #     await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
