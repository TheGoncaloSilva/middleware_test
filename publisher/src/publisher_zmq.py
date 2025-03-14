import zmq
import time

# Configuration
ADDRESS = "tcp://0.0.0.0:5555"
PACKET_COUNT = 100
DUMMY_DATA_SIZE = 4056292  # bytes

# Create ZeroMQ context and socket
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(ADDRESS)

time.sleep(5)
print(f"Publisher is instantiated at {ADDRESS}...")

# Generate dummy data
dummy_data = b"x" * DUMMY_DATA_SIZE  # bytes of dummy data

for i in range(PACKET_COUNT):
    # Create a timestamp
    timestamp = time.time()
    
    # Create the message (timestamp + dummy data)
    message = f"{timestamp}".encode() + dummy_data

    # Send the message
    socket.send(message)
    print(f"Sent packet {i + 1}/{PACKET_COUNT}: Size: {len(message)}")

print("All packets sent.")
socket.close()
context.term()
