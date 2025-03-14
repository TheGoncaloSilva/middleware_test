from threading import Condition
import time

import fastdds
import build.SimpleMessage as SimpleMessage

# Configuration
PACKET_COUNT = 100
DUMMY_DATA_SIZE = 4056292  # bytes
PROFILE: str = "SHMParticipant"

# Generate dummy data
dummy_data = b"x" * DUMMY_DATA_SIZE 

class WriterListener (fastdds.DataWriterListener) :
    def __init__(self, writer) :
        self._writer = writer
        super().__init__()


    def on_publication_matched(self, datawriter, info) :
        if (0 < info.current_count_change) :
            print ("Publisher matched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader += 1
            self._writer._cvDiscovery.notify()
            self._writer._cvDiscovery.release()
        else :
            print ("Publisher unmatched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader -= 1
            self._writer._cvDiscovery.notify()
            self._writer._cvDiscovery.release()


class Writer:


    def __init__(self):
        self._matched_reader = 0
        self._cvDiscovery = Condition()

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

        self.publisher_qos = fastdds.PublisherQos()
        self.participant.get_default_publisher_qos(self.publisher_qos)
        self.publisher = self.participant.create_publisher(self.publisher_qos)

        self.listener = WriterListener(self)
        self.writer_qos = fastdds.DataWriterQos()
        self.publisher.get_default_datawriter_qos(self.writer_qos)
        self.writer = self.publisher.create_datawriter(self.topic, self.writer_qos, self.listener)
        

    def write(self):
        # Create a timestamp
        timestamp = time.time()
        # Create the message (timestamp + dummy data)
        message: bytes = f"{timestamp}".encode() + dummy_data
        
        # convert bytes to utf-8 string
        message = message.decode('utf-8')
        data = SimpleMessage.SimpleMessage()
        data.message(message)
        self.writer.write(data)
    
        print(f"Sent packet {self.index + 1}/{PACKET_COUNT}")


    def wait_discovery(self) :
        self._cvDiscovery.acquire()
        print ("Writer is waiting discovery...")
        self._cvDiscovery.wait_for(lambda : self._matched_reader != 0)
        self._cvDiscovery.release()
        print("Writer discovery finished...")


    def run(self):
        self.wait_discovery()
        time.sleep(3)
        for self.index in range(PACKET_COUNT) :
            self.write()
        time.sleep(1)
        self.delete()


    def delete(self):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)


if __name__ == '__main__':
    print('Starting publisher.')
    time.sleep(2)
    writer = Writer()
    writer.run()
    exit()