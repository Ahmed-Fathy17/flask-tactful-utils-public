from typing import Dict
import jwt
import requests
from functools import wraps
from flask import request, current_app, g
from werkzeug.local import LocalProxy

from ..exceptions import InvalidTokenException, UnAuthenticatedException, UnAuthorizedRoleException

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
    decoded_jwt = g.get('_jwt_current_user', None)
    if decoded_jwt is None:
        raise RuntimeError("You must call `@profile_access_permission` or `@is_authorized` before accessing current user")
    return decoded_jwt

current_user: dict = LocalProxy(get_current_user) # type: ignore


def profile_access_permission(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):

        user = decode_token()

        user_profile_id = user.get('profile_id')

        if user_profile_id is not None and (kwargs.get('profile_id') is None and kwargs.get('profile') is None):
            kwargs["profile"] = user_profile_id

        profile = kwargs.get('profile')
        if user_profile_id is not None and profile is not None and int(user_profile_id) != int(profile):
            current_app.logger.error(f"requested profile:{profile} but user has user_profile_id:{user_profile_id}")
            raise UnAuthorizedRoleException("Different profile associated with authentication token")

        if profile is None:
            raise UnAuthorizedRoleException(description="profile_id is None")

        if authorize(decorated_view.__qualname__.lower(), kwargs):
            return func(*args, **kwargs)

    return decorated_view


def is_authorized(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if authorize(decorated_view.__qualname__.lower(), kwargs):
            return func(*args, **kwargs)

    return decorated_view


def authorize(resource: str, kwargs: Dict) -> bool:
    authorized = resource_permission(resource, kwargs)
    g._jwt_current_user = decode_token()
    return authorized


def resource_permission(resource: str, kwargs: Dict) -> bool:
    if current_app.config.get("TESTING", False):
        current_app.logger.info(f"BYPASSING AUTH/AUTHZ - allowing {resource} and {kwargs}")
        return True

    token = str(request.headers.get(current_app.config['JWT_HEADER_NAME']))
    body = {
        "input": {
            "resources": [resource],
            "token": token.split()[-1],
            "query_params": {resource: request.args.to_dict()},
            "path_params": {resource: kwargs},
            "body_params": {resource: request.get_json(silent=True)}
        }
    }

    res = requests.post(url=str(current_app.config.get("AUTHORIZATION_URL")), json=body)
    if not res.ok:
        raise InvalidTokenException()

    auth_result = res.json().get("result").get(resource)
    if auth_result:
        if auth_result.get("allow"):
            return True
        raise UnAuthorizedRoleException(description=auth_result.get('explain'))
    raise UnAuthorizedRoleException()
