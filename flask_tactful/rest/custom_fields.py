import json
from flask_restx import fields, reqparse

relation_includes_parser = reqparse.RequestParser()
relation_includes_parser.add_argument('includes', type=str)


class JsonLoadsField(fields.Raw):
    """ handles JSON fields, loads them as dicts """

    def format(self, value):
        parsed_details = json.loads(value) if value else None
        return parsed_details


class AnyTypeField(fields.Raw):
    """ Handles ANY fields """

    def format(self, value):
        return value


class LoadStringToList(fields.Raw):
    """ handles string lists a,b,c and converts them to native lists """

    def _validate_lists(self, obj_list):
        obj_str = json.dumps(obj_list)
        if obj_str[1] != "[" or obj_str[len(obj_str) - 2] != "]":
            return False
        return True

    def format(self, value):
        """ formatting function """
        obj_list = value
        if not isinstance(value, list):
            if not self._validate_lists(value):
                obj_list = value.split(",")
            else:
                obj_list = json.loads(value) if value else []
        return obj_list
