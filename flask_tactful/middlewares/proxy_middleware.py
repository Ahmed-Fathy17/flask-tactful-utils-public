
# pylint: disable=too-few-public-methods
class ReverseProxied:
    """ Wraps app in a middleware that corrects the request context if the app is behind a reverse proxy
    This currently works with AWS Elastic Load Balancer specefic headers
    It extracts the current schema used by the original client from: X-Forwarded-Proto HTTP header
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        scheme = environ.get('X-Forwarded-Proto')
        if scheme:
            environ['wsgi.url_scheme'] = scheme

        # get the client remote address from behind the proxy
        remote_addr = None
        remotes = environ.get('HTTP_X_FORWARDED_FOR', '').split(',')
        if remotes:
            remote_addr = remotes[-1].strip()

        if remote_addr:
            environ['REMOTE_ADDR'] = remote_addr

        return self.app(environ, start_response)
