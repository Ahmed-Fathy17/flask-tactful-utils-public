from functools import wraps


def get_parser_schema(parser):
    body_schema = {}
    other_schema = {}
    for arg in parser.args:
        if arg.location == 'json':
            body_schema[arg.name] = arg.__schema__
        else:
            other_schema[arg.name] = arg.__schema__
    return body_schema ,other_schema

def get_parser_doc(parser):
    body_params,other_params=get_parser_schema(parser)
    params =  {
        "payload" : {
            "name": "payload",
            "in": "body",
            "required": False,
            "schema": {
                "type": "object",
                "properties": body_params
                }
            }
    } if body_params else {}
    params.update(other_params)
    return params

     
def parser_doc(parser,namespace):
    
    def decorator(func):
        params = get_parser_doc(parser)
        @wraps(func)
        @namespace.doc(params=params)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
