import json
from flask_restx import fields, reqparse

relation_includes_parser = reqparse.RequestParser()
relation_includes_parser.add_argument('includes', type=str)


def validate_lists(obj_list):
    obj_str = json.dumps(obj_list)
    if obj_str[1] != "[" or obj_str[len(obj_str) - 2] != "]":
        return False
    return True


class JsonLoadsField(fields.Raw):
    def format(self, value):
        parsed_details = json.loads(value) if value else None
        return parsed_details


class AnyTypeField(fields.Raw):
    def format(self, value):
        return value

class LoadStringToList(fields.Raw):
    def format(self, value):
        obj_list = value
        if not isinstance(value, list):
            if not validate_lists(value):
                obj_list = value.split(",")
            else:
                obj_list = json.loads(value) if value else []
        return obj_list        
