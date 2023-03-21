import simplexml

from flask import make_response


def output_xml(data, code, headers=None):
    """ convert output to XML response, used if API client requests XML """
    # WARNING:  cannot handle swagger.json which always fails because browser treats HTML == application/xml
    # so for a workaround always request it with application/json
    resp = make_response(simplexml.dumps(data), code)
    resp.headers.extend(headers)
    return resp
