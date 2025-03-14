import zenoh
import time
import queue
import numpy as np

# Configuration
RESOURCE = "demo/latency"

# Create Zenoh session
session = zenoh.open(zenoh.Config())

# Subscribe to the resource
print(f"Subscriber is subscribing to resource: {RESOURCE}")
packet_count = 0
latency_queue = queue.Queue()

def callback(sample):
    # Convert payload to bytes
    payload = sample.payload.to_bytes()

    # Extract the timestamp and calculate latency
    timestamp = float(payload[:payload.index(b'x')].decode())
    latency = time.time() - timestamp

    # Save the latency in the queue
    latency_queue.put(latency)

    global packet_count
    packet_count += 1

    # Print the results
    print(f"Received packet {packet_count}: Size {len(payload)}, Latency = {latency * 1000:.2f} ms")

subscriber = session.declare_subscriber(RESOURCE, callback)

while packet_count < 10:
    time.sleep(1)

# Calculate average and variance
latencies = list(latency_queue.queue)
average_latency = np.mean(latencies) * 1000  # Convert to milliseconds
variance_latency = np.var(latencies) * 1000  # Convert to milliseconds

print("All packets received.")
print(f"Average Latency: {average_latency:.2f} ms")
print(f"Variance Latency: {variance_latency:.2f} ms")

subscriber.undeclare()
session.close()
