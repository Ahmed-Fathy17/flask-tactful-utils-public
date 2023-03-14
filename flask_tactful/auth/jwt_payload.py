from dataclasses import dataclass
from typing import Literal, Optional
from datetime import datetime

JWTAudiences = Literal['webchat', 'vdash', 'email']

@dataclass
class JWTPayload:
    """ This class is about the payload of the token """
    email: str
    role: str
    aud: JWTAudiences
    id: Optional[int] = None
    sub: Optional[str] = None
    expires_on: Optional[datetime] = None

    def from_dict(self,payload):
        for field in self.__dataclass_fields__:
            setattr(self, field, payload.get(field))


@dataclass
class JWTAccessPayload(JWTPayload):
    profile_id: Optional[int] = None
    profile_role: Optional[str] = None

@dataclass
class JWTWebChatPayload(JWTPayload):
    guid: Optional[str] = None
    customer_id: Optional[int] = None
    channel_id: Optional[int] = None

@dataclass
class JWTCredintial:
    user_access_token: str
    user_refresh_token: str
