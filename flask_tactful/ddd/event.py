from pydantic import BaseModel


class Event(BaseModel, extra='allow'):
    """ Event to be sent on the bus, represents an event happening in one microservice,
    other microservices can recieve this event by listening to the topic named after the sender service
    events are usually profile/tenant based (must contain a profile ID)
    """

    """ version identifier, if the schema changes, please increment """
    version: int = 2

    """ Bus topic, or the queue name in the busses that don't support topics (e.g. tactful.billing) """
    topic: str

    """ event that occured in the system (e.g. CreditCardExpired) """
    event: str

    """ unique ID of the message pushed in the bus, usually assigned by the bus itself on receiving or sending """
    msg_id: str = ""

    """ profile ID (tenant id) for the workspace that generated the event """
    profile_id: int

    """max length of the stream, if the number of entries exceeds this, the oldest entries will be trimmed"""
    max_stream_len: int = 10*1000*1000
