from functools import wraps
from flask import request, current_app

def get_cors_headers():
    return {
        
        'Content-Type': "application/json; charset=UTF-8",
        'Access-Control-Allow-Origin': request.environ.get('HTTP_ORIGIN', '*'),
        'Access-Control-Allow-Methods': 'PUT,GET,POST,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Access-Control-Allow-Headers, Authorization, X-API-KEY',
        'Access-Control-Allow-Credentials': 'true'

        # headers['Accept'] = "application/json, text/javascript, */*; q=0.01"
        # headers['Accept-Encoding'] = "gzip, deflate, br"
        # headers['Accept-Language'] = "en-US,en;q=0.9"

    }

def allow_cors(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        headers = {}
        if current_app.config.get('ENABLE_CORS'):
            headers = get_cors_headers()
        
        response = func(*args, **kwargs)
        # override the headers with the ones set by the API function
        # conserve the ones set by the view function
        if len(response) >= 3:
            headers.update(response[2])
        code = response[1] if len(response) > 0 else 200
        return (response[0], code, headers)
    return decorated_view

