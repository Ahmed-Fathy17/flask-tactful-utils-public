from typing import Any
from pydantic import BaseModel

class Event(BaseModel):
    # version identifier, if the schema changes, please increment
    version: int = 1

    # Bus topic, or the queue name in the busses that don't support topics (e.g. tactful.billing)
    topic: str = "generic"

    # event that occured in the system (e.g. CreditCardExpired)
    event: str = "something_happened"

    # unique ID of the message pushed in the bus, usually assigned by the bus itself on receiving or sending
    msg_id: str = ""
    
    # profile ID (tenant id) for the workspace that generated the event
    profile_id: int

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.event = self.__class__.__name__
