import zmq
import time
import queue
import numpy as np

# Configuration
ADDRESS = "tcp://0.0.0.0:5555"
N_PACKETS = 100

# Create ZeroMQ context and socket
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect(ADDRESS)

# Subscribe to all topics
socket.setsockopt_string(zmq.SUBSCRIBE, "")

print(f"Subscriber connected to {ADDRESS}...")

latency_queue = queue.Queue()

for i in range(N_PACKETS):
    # Receive the message
    message = socket.recv()

    # Extract the timestamp and calculate latency
    timestamp = float(message[:message.index(b'x')].decode())
    latency = time.time() - timestamp

    # Save the latency in the queue
    latency_queue.put(latency)

    # Print the results
    print(f"Received Packet {i + 1}: Latency = {latency * 1000:.2f} ms, length = {len(message)} bytes")

# Calculate average and variance
latencies = list(latency_queue.queue)
average_latency = np.mean(latencies) * 1000  # Convert to milliseconds
variance_latency = np.var(latencies) * 1000  # Convert to milliseconds

print("All packets received.")
print(f"Average Latency: {average_latency:.2f} ms")
print(f"Variance Latency: {variance_latency:.2f} ms")

socket.close()
context.term()
