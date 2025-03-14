import signal
import time
import queue
import numpy as np
import fastdds
import build.SimpleMessage as SimpleMessage

# Variables
packet_count: int = 0
PROFILE: str = "SHMParticipant"

# To capture ctrl+C
def signal_handler(sig, frame):
    print('Interrupted!')
    
class ReaderListener(fastdds.DataReaderListener):

    def __init__(self):
        super().__init__()
        self.latency_queue = queue.Queue()

    def on_subscription_matched(self, datareader, info):
        if 0 < info.current_count_change:
            print(f"Subscriber matched publisher {info.last_publication_handle}")
        else:
            print(f"Subscriber unmatched publisher {info.last_publication_handle}")

    def on_data_available(self, reader):
        info = fastdds.SampleInfo()
        data = SimpleMessage.SimpleMessage()
        reader.take_next_sample(data, info)

        message = data.message().encode()
        # Extract the timestamp and calculate latency
        timestamp = float(message[:message.index(b'x')].decode())
        latency = time.time() - timestamp

        # Save the latency in the queue
        self.latency_queue.put(latency)

        global packet_count
        packet_count += 1

        # Print the results
        print(f"Received packet {packet_count}: Size {len(message)}, Latency = {latency * 1000:.2f} ms")

    def calculate_statistics(self):
        # Calculate average and variance
        latencies = list(self.latency_queue.queue)
        average_latency = np.mean(latencies) * 1000  # Convert to milliseconds
        variance_latency = np.var(latencies) * 1000  # Convert to milliseconds

        print(f"Average Latency: {average_latency:.2f} ms")
        print(f"Variance Latency: {variance_latency:.2f} ms")

class Reader:

    def __init__(self):
        # Create a DDS participant
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant_qos = fastdds.DomainParticipantQos()
        factory.get_default_participant_qos(self.participant_qos)
        global PROFILE
        print(f"Creating participant with profile: {PROFILE}")
        participant = factory.create_participant_with_profile(PROFILE)
        self.participant = participant

        self.topic_data_type = SimpleMessage.SimpleMessagePubSubType()
        self.topic_data_type.setName("SimpleMessage")
        self.type_support = fastdds.TypeSupport(self.topic_data_type)
        self.participant.register_type(self.type_support)

        self.topic_qos = fastdds.TopicQos()
        self.participant.get_default_topic_qos(self.topic_qos)
        self.topic = self.participant.create_topic("SimpleMessageTopic", self.topic_data_type.getName(), self.topic_qos)

        self.subscriber_qos = fastdds.SubscriberQos()
        self.participant.get_default_subscriber_qos(self.subscriber_qos)
        self.subscriber = self.participant.create_subscriber(self.subscriber_qos)

        self.listener = ReaderListener()
        self.reader_qos = fastdds.DataReaderQos()
        self.subscriber.get_default_datareader_qos(self.reader_qos)
        self.reader = self.subscriber.create_datareader(self.topic, self.reader_qos, self.listener)

    def delete(self):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)

    def run(self):
        signal.signal(signal.SIGINT, signal_handler)
        print('Press Ctrl+C to stop')
        signal.pause()
        self.listener.calculate_statistics()
        self.delete()

if __name__ == '__main__':
    print('Creating subscriber.')
    reader = Reader()
    reader.run()
    exit()
