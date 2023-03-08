from dataclasses import dataclass
from typing import Literal
from xmlrpc.client import DateTime


@dataclass
class JWTPayload:
    """ This class is about the payload of the token """
    email: str = None
    id: int = None
    role: str = None 
    aud: Literal['webchat', 'vdash', 'email'] = None
    expires_on: DateTime = None

@dataclass
class JWTProfilePayload(JWTPayload):
    profile_id: int = None
    profile_role: str  = None

@dataclass
class JWTWebChatPayload(JWTPayload):
    guid: str = None
    customer_id: int = None
    channel_id: int = None

@dataclass
class JWTCredintial:
    user_access_token: str
    user_refresh_token: str
