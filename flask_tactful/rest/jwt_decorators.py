import json
from typing import Dict
import requests
from functools import wraps
from flask import request, current_app
from ..auth.jwt_manager import get_current_user
from ..exceptions import UnAuthorizedRoleException


def profile_access_permission(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):

        user = get_current_user()
        # Not necessary anymore as the customer token payload will have the profile_id & profile_role so no need to tactful_jwt_validation decorator
        # user =identity if identity and identity.get('role') != 'customer' else kwargs['customer_payload'] #handle case of customer token

        user_profile_role = user.get("profile_role", None)
        user_profile_id = user.get('profile_id', None)  # Using profile name will force making a DB call before the request which is not a ideal case.
        if user_profile_id is not None and (kwargs.get('profile_id') is None and kwargs.get('profile') is None):
            kwargs["profile"] = user_profile_id

        elif user.get("role") == 'admin' and kwargs.get('profile') is None and request.headers.get('Profile'):
            kwargs['profile'] = request.headers.get('Profile')

        if user.get("role") == 'admin':
            return func(*args, **kwargs)


        profile = kwargs.get('profile')
        if user_profile_role is not None and profile is not None and int(user_profile_id) != int(profile):
            current_app.logger.error(f"requested {profile} but user has {user_profile_id}")
            return f"Different profile associated with authentication token", 401

        # Fouad = i disabled permissions checking till we get a better method that is more friendly to microservices
        # if user_profile_role is not None and decorated_view.__qualname__.lower() in ROLES.get(user_profile_role.lower()):
        if resource_permission(decorated_view.__qualname__.lower(), kwargs):
            return func(*args, **kwargs)

        # return 'User profile role doesn\'t have API permission.', 401

    return decorated_view


def is_authorized(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):

        user = get_current_user()
        if user.get("role") == 'admin':
            return func(*args, **kwargs)

        if resource_permission(decorated_view.__qualname__.lower(), kwargs):
            return func(*args, **kwargs)

    return decorated_view


def require_admin(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        user = get_current_user()
        if user.get("role") in ['admin', 'billing_admin', 'system_admin']:
            return func(*args, **kwargs)
        else:
            return 'Token provided does not have permissions to access this resource.', 401

    return decorated_view


def resource_permission(resource: str, kwargs: Dict) -> bool:
    token = str(request.headers.get('X-API-KEY'))
    body = {
        "input": {
            "resources": [resource],
            "token": token.split()[-1],
            "query_params": {resource: request.args.to_dict()},
            "path_params": {resource: kwargs},
            "body_params": {resource: request.json}
        }
    }
    if current_app.config.get("TESTING", False):
        current_app.logger.debug(f"BYPASSING OPA - allowing {resource} and {kwargs}")
        return True

    res = requests.post(url=str(current_app.config.get("AUTHORIZATION_URL")), json=body)
    auth_result = res.json().get("result").get(resource)
    if auth_result:
        if auth_result.get("allow"):
            return True
        raise UnAuthorizedRoleException(description=json.dumps(auth_result.get('explain')))
    raise UnAuthorizedRoleException()
