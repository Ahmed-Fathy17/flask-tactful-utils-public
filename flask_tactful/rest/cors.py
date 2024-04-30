import os
from flask import Response, request, current_app, Flask

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'PUT,PATCH,GET,POST,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Access-Control-Allow-Headers, Authorization, X-API-KEY',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Max-Age': os.environ.get('CORS_PREFLIGHT_MAX_AGE', '86400'),

    # headers['Accept'] = "application/json, text/javascript, */*; q=0.01"
    # headers['Accept-Encoding'] = "gzip, deflate, br"
    # headers['Accept-Language'] = "en-US,en;q=0.9"
}

def init_app(app: Flask):
    @app.before_request
    def allow_options():
        if request.method == "OPTIONS":
            return Response("OK")

    @app.after_request
    def handle_cors(response: Response) -> Response:
        if current_app.config.get('ENABLE_CORS'):
            response.headers.update(cors_headers)
        return response
