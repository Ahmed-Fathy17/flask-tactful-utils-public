""" Some preprocessing for API authenitcation """
# pylint: disable=too-few-public-methods
class AuthMiddleware:
    """ Wraps app in a middleware that corrects the request for the sake of appsumo that expects us to use
    JWT Header Authourization, while we use X-API-KEY
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        jwt_header: str = self.app.config.get('JWT_HEADER_NAME')
        if jwt_header:
            jwt_header = jwt_header.replace("-", "_").upper()

            token = environ.get('HTTP_AUTHORIZATION')
            if token:
                environ[f"HTTP_{jwt_header}"] = token

        return self.app(environ, start_response)
