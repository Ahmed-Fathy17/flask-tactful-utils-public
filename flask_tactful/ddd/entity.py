import uuid
from pydantic import BaseModel

class Entity(BaseModel):

    @classmethod
    def next_id(cls) -> uuid.UUID:
        return uuid.uuid4()

    @classmethod
    def uuid(cls, name: str) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_URL, f"{cls.__name__}/{name}")
