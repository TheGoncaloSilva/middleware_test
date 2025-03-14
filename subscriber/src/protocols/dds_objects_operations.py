import build.SimpleMessage as SimpleMessage


def BuildSimpleMessage(object_info: dict) -> SimpleMessage.SimpleMessage:
    """
    Build a SimpleMessage DDS object from a dictionary.

    :param object_info: The dictionary containing the object information.
    :return: The SimpleMessage DDS object.
    """
    dds_object = SimpleMessage.SimpleMessage() 
    dds_object.message(object_info['message'])
    return dds_object


def ReadSimpleMessage(dds_object: SimpleMessage.SimpleMessage) -> dict:
    """
    Read a SimpleMessage DDS object and return a dictionary.

    :param dds_object: The SimpleMessage DDS object.
    :return: The dictionary containing the object information.
    """
    object_info = {}
    object_info['message'] = dds_object.message()

    return object_info
