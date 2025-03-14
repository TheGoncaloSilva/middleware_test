import fastdds
from typing import Optional 
from threading import Condition
import build.SimpleMessage as SimpleMessage

class WriterListener(fastdds.DataWriterListener):
    """
    Default DDS writer listener class for FastDDS.

    Attributes:
        _writer: The associated DDS writer.
    """

    def __init__(self, writer) -> None:
        """
        Initialize the DDS writer listener.

        :param writer: The associated DDS writer.
        """
        self._writer = writer
        super().__init__()

    def on_publication_matched(self, datawriter, info) -> None:
        """
        Callback when a publication is matched by a subscriber.

        :param datawriter: The DDS data writer.
        :param info: Information about the matched publication.
        """
        if (0 < info.current_count_change):
            print ("Publisher matched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader += 1
            self._writer.participant_handles.push_back(info.last_subscription_handle)
            self._writer._cvDiscovery.notify()
            self._writer._cvDiscovery.release()
            
        else:
            print ("Publisher unmatched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader += 1
            # Attempt to remove the handle correctly
            try:
                # Find the index of the handle to remove
                index = [i for i, handle in enumerate(self._writer.participant_handles) if handle == info.last_subscription_handle][0]
                # Convert index to iterator and erase
                it = self._writer.participant_handles.begin()
                for _ in range(index):
                    it.next()
                self._writer.participant_handles.erase(it)
                self._writer._matched_reader -= 1
                self._writer._cvDiscovery.notify()
            except (IndexError, Exception) as e:
                print(f"Failed to remove participant handle due to: {str(e)}")
            self._writer._cvDiscovery.release()
        

class Writer:
    """
    Default DDS writer class for FastDDS using SimpleMessage or WarningPayload.

    Attributes:
        _matched_reader (int): Count of matched readers.
        _cvDiscovery (Condition): Condition variable for discovery synchronization.
        alive (bool): Flag to indicate if the writer is alive.
        participant_qos: Quality of Service settings for the DDS participant.
        participant: The DDS participant.
        topic_data_type: Data type for the DDS topic.
        type_support: DDS type support.
        topic_qos: Quality of Service settings for the DDS topic.
        topic: The DDS topic.
        publisher_qos: Quality of Service settings for the DDS publisher.
        publisher: The DDS publisher.
        listener: Listener for DDS writer events.
        writer_qos: Quality of Service settings for the DDS data writer.
        writer: The DDS data writer.
    """

    def __init__(self, profile: str, data_name: str) -> None:
        """
        Initialize the DDS data writer.

        :param profile: The DDS profile name.
        :param data_name: The name of the DDS data.
        """
        self._matched_reader = 0
        self._cvDiscovery = Condition()
        self.alive = True
        self.participant_handles = fastdds.InstanceHandleVector()  # Store handles here

        # Create a DDS participant
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant_qos = fastdds.DomainParticipantQos()
        factory.get_default_participant_qos(self.participant_qos)
        participant = factory.create_participant_with_profile(profile)
        self.participant = participant
        
        # Register the DDS data type
        if data_name == "SimpleMessage":
            self.topic_data_type = SimpleMessage.SimpleMessagePubSubType()
        else:
            raise ValueError("Invalid data name")
        
        self.topic_data_type.setName(data_name)
        self.type_support = fastdds.TypeSupport(self.topic_data_type)
        self.participant.register_type(self.type_support)

        # Create a DDS topic
        self.topic_qos = fastdds.TopicQos()
        self.participant.get_default_topic_qos(self.topic_qos)
        self.topic = self.participant.create_topic(data_name + "Topic", self.topic_data_type.getName(), self.topic_qos)

        # Create a DDS publisher
        self.publisher_qos = fastdds.PublisherQos()
        self.participant.get_default_publisher_qos(self.publisher_qos)
        self.publisher = self.participant.create_publisher(self.publisher_qos)

        # Create a writer listener
        self.listener = WriterListener(self)

        # Create a DDS data writer
        self.writer_qos = fastdds.DataWriterQos()
        self.publisher.get_default_datawriter_qos(self.writer_qos)
        self.writer = self.publisher.create_datawriter(self.topic, self.writer_qos, self.listener)

    def print_locator_info(self, locator_list):
        """
        Helper function to print information from a LocatorList.
        Assumes that locator_list provides a method to access its size and elements by index.
        """
        for i in range(locator_list.size()):
            locator = locator_list.get_locator_at(i)
            if locator.kind == fastdds.LOCATOR_KIND_TCPv4 or locator.kind == fastdds.LOCATOR_KIND_UDPv4:
                ip = '.'.join(str(octet) for octet in locator.address[:4])
                port = locator.port
                print(f"Locator IP: {ip}, Port: {port}")
            else:
                print("Non-IPv4 locator found.")

    def discover_and_print_participants(self):
        """
        Discover and print locator information for participants.
        """

        # Accessing the metatraffic locator lists
        metatraffic_multicast = self.participant_qos.wire_protocol().default_multicast_locator_list
        metatraffic_unicast = self.participant_qos.wire_protocol().default_unicast_locator_list

        print("Metatraffic Multicast Locators:")
        self.print_locator_info(metatraffic_multicast)

        print("Metatraffic Unicast Locators:")
        self.print_locator_info(metatraffic_unicast)
        
    # def discover_and_print_participants(self) -> None:
    #     """
    #     Discover and print attributes of all participants.
    #     """
    #     self.participant.get_discovered_participants(self.participant_handles)
    #     print(f"Number of discovered participants: {len(self.participant_handles)}")

    #     builtin_attributes = self.participant_qos.wire_protocol().builtin
    #     locators = builtin_attributes.metatrafficMulticastLocatorList

    #     # for i in range(len(self.participant_handles)):
    #     #     handle = self.participant_handles[i]
    #     #     participant_data = fastdds.ParticipantBuiltinTopicData()
    #     #     print(f"HANDLE: {handle}")
    #     #     self.participant.get_discovered_participant_data(participant_data, handle)

    def write(self) -> None:
        """
        Placeholder for writing data using the DDS data writer.
        """
        pass

    def wait_discovery(self) -> None:
        """
        Wait for DDS discovery to complete.
        """
        self._cvDiscovery.acquire()
        print ("Writer is waiting discovery...")
        self._cvDiscovery.wait_for(lambda : self._matched_reader != 0)
        self._cvDiscovery.release()
        print("Writer discovery finished...")

    def run(self) -> None:
        """
        Placeholder for running the DDS writer.
        """
        pass

    def stop(self) -> None:
        """
        Set the alive flag to False to handle the DDS writer shutdown.
        """
        self.alive = False
    
    def delete(self):
        """
        Delete the DDS writer and participant.
        """
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)


class ReaderListener(fastdds.DataReaderListener):
    """
    Default DDS reader listener class for FastDDS.

    Attributes:
        None
    """

    def __init__(self) -> None:
        """
        Initialize the DDS reader listener.
        """
        super().__init__()
    
    def on_subscription_matched(self, datareader, info) -> None:
        """
        Callback when a subscription is matched by a publisher.

        :param datareader: The DDS data reader.
        :param info: Information about the matched subscription.
        """
        if (0 < info.current_count_change) :
            print ("Subscriber matched publisher {}".format(info.last_publication_handle))
        else :
            print ("Subscriber unmatched publisher {}".format(info.last_publication_handle))
    
    def on_data_available(self, reader) -> None:
        """
        Placeholder for data avaliable in the DDS reader listener.
        """
        pass


class Reader:
    """
    Default DDS reader class for FastDDS using SimpleMessage or WarningPayload.

    Attributes:
        alive (bool): Flag to indicate if the reader is alive.
        participant_qos: Quality of Service settings for the DDS participant.
        participant: The DDS participant.
        topic_data_type: Data type for the DDS topic.
        type_support: DDS type support.
        topic_qos: Quality of Service settings for the DDS topic.
        topic: The DDS topic.
        subscriber_qos: Quality of Service settings for the DDS subscriber.
        subscriber: The DDS subscriber.
        listener: Listener for DDS reader events.
        reader_qos: Quality of Service settings for the DDS data reader.
        reader: The DDS data reader.
    """

    def __init__(self, profile: str, data_name: str, topic_name: str, listener: Optional[ReaderListener] = None) -> None:
        """
        Initialize the DDS data reader.

        :param profile: The DDS profile name.
        :param data_name: The name of the DDS data.
        :param topic_name: The name of the DDS topic.
        :param listener: Listener for DDS reader events.
        """
        self.alive = True

        # Create a DDS participant
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant_qos = fastdds.DomainParticipantQos()
        factory.get_default_participant_qos(self.participant_qos)
        participant = factory.create_participant_with_profile(profile)
        self.participant = participant

        # Register the DDS data type
        if data_name == "SimpleMessage":
            self.topic_data_type = SimpleMessage.SimpleMessagePubSubType()
        else:
            raise ValueError("DDS Reader data name specified not supported")
        
        self.topic_data_type.setName(data_name)
        self.type_support = fastdds.TypeSupport(self.topic_data_type)
        self.participant.register_type(self.type_support)

        # Create a DDS topic
        self.topic_qos = fastdds.TopicQos()
        self.participant.get_default_topic_qos(self.topic_qos)
        if data_name == "SimpleMessage":
            self.topic = self.participant.create_topic(topic_name, self.topic_data_type.getName(), self.topic_qos)
        else:
            raise ValueError("DDS Reader data name specified not supported")

        # Create a DDS subscriber
        self.subscriber_qos = fastdds.SubscriberQos()
        self.participant.get_default_subscriber_qos(self.subscriber_qos)
        self.subscriber = self.participant.create_subscriber(self.subscriber_qos)

        # Set a custom listener if provided
        if listener is None:
            self.listener = ReaderListener()
        else:
            self.listener = listener
        
        # Create a DDS data reader
        self.reader_qos = fastdds.DataReaderQos()
        self.subscriber.get_default_datareader_qos(self.reader_qos)
        self.reader = self.subscriber.create_datareader(self.topic, self.reader_qos, self.listener)

    def run(self) -> None:
        """
        Placeholder for running the DDS reader.
        """
        pass

    def stop(self) -> None:
        """
        Set the alive flag to False to handle the DDS reader shutdown.
        """
        self.alive = False
    
    def delete(self):
        """
        Delete the DDS reader and participant.
        """
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)
