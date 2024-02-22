import jwt
from flask import request, current_app, g
from werkzeug.local import LocalProxy
from .jwt_payload import JWTPayload
from ..exceptions import InvalidTokenException, UnAuthenticatedException


def decode_token():
    header_name = current_app.config['JWT_HEADER_NAME']

    auth_header = request.headers.get(header_name, "").strip().strip(",")
    if not auth_header:
        raise UnAuthenticatedException()

    parts = auth_header.split()
    if len(parts) != 2:
        raise InvalidTokenException()

    return jwt.decode(parts[1], options={"verify_signature": False})


def get_current_user() -> dict:
    # _jwt_current_user value is set in flask_tactful/rest/jwt_decorators.py:authorize with decoded user token
    decoded_jwt = g.get('_jwt_current_user', None)
    if decoded_jwt is None:
        raise RuntimeError("You must call `@profile_access_permission` or `@is_authorized` before accessing current user")
    return decoded_jwt


current_user: dict = LocalProxy(get_current_user) # type: ignore


def get_jwt_identity() -> JWTPayload:
    jwt_user = get_current_user()
    return JWTPayload(id=jwt_user.get("id"), sub=jwt_user.get("sub"), email=jwt_user.get("email"), role=jwt_user.get("role"), aud=jwt_user.get("aud"))
