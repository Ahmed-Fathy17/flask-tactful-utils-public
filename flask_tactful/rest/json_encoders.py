
import decimal
import json


class RESTFULEncoder(json.JSONEncoder):
    """ if you faced a problem with DynamoDB results getting serialized and failing, 
    that is because Dynamo represents numbers as Decimal type, and Restful JSON encoder does not support it
    either convert the numbers to strings in dynamo, or use the encoder below
    """
    #pylint: disable=method-hidden
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)
