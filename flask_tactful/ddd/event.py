from pydantic import BaseModel

class Event(BaseModel):
    __topic__: str = "other"
    version: int = 1
    profile_id: int
    
