import zenoh
import time

# Configuration
RESOURCE = "demo/latency"
PACKET_COUNT = 100
DUMMY_DATA_SIZE = 4056292  # bytes

# Create Zenoh session
session = zenoh.open(zenoh.Config())
publisher = session.declare_publisher(RESOURCE)

print(f"Publisher is sending data to resource: {RESOURCE}")

# Generate dummy data
dummy_data = b"x" * DUMMY_DATA_SIZE  # bytes of dummy data

time.sleep(5)
for i in range(PACKET_COUNT):
    # Create a timestamp
    timestamp = time.time()

    # Create the message (timestamp + dummy data)
    message = f"{timestamp}".encode() + dummy_data

    # Publish the message
    publisher.put(message)
    print(f"Sent packet {i + 1}/{PACKET_COUNT}: Size: {len(message)}")

print("All packets sent.")
publisher.undeclare()
session.close()
