from dataclasses import dataclass
from typing import Literal, Optional
from datetime import datetime

JWTAudiences = Literal['webchat', 'vdash', 'email']

@dataclass
class JWTPayload:
    """ This class is about the payload of the token """
    email: str
    id: int
    role: str 
    aud: JWTAudiences
    expires_on: datetime


@dataclass
class JWTAccessPayload(JWTPayload):
    profile_id: Optional[int] = None
    profile_name: Optional[str] = None
    profile_role: Optional[str] = None

@dataclass
class JWTWebChatPayload(JWTPayload):
    guid: str
    customer_id: int
    channel_id: int


class JWTCredintial:
    user_access_token: str
    user_refresh_token: str
