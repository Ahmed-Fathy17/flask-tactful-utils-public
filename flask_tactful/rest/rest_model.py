
import typing
from datetime import datetime
import flask_sqlalchemy
import sqlalchemy
from flask_restx import Namespace, fields, reqparse
from .custom_fields import AnyTypeField


ParserLocations = typing.Literal['form', 'headers', 'values', 'args', 'cookies', 'files', 'json']

# this gist might be useful to handle loading and serializing for models https://gist.github.com/alanhamlett/6604662
python2restplus = {
    'str': fields.String,
    'datetime': fields.DateTime,
    'time': fields.String,
    'bool': fields.Boolean,
    'int': fields.Integer,
    'float': fields.Float,
    'relation': fields.Nested,
    'list': fields.List,
    'dict': AnyTypeField,
    'KT': AnyTypeField,   # typing.Dict
    'UUID': fields.String,
}


python2type = {
    'str': str,
    'datetime': datetime,
    'time': str,
    'bool': bool,
    'int': int,
    'float': float,
    'relation': None,
    'list': list,
    'dict': dict,
    'KT': dict,   # typing.Dict
}


class RestModel:
    """ converts Python class (POPO = Plain Old Python Object) to Restuplus Field types, 
    it does not handle Nested items, it leaves this to the caller to append them to the returned dictionary
    it also ingores __protected__ attribute like passwords just add it to Model.__protected__ list
    it assumes the POPO contain class attributes with mypy types or Python type data
    """
    type_mapper: typing.Dict

    def __init__(self, mapper: typing.Dict) -> None:
        self.type_mapper = mapper

    def attr_to_restplus(self, attr_type, namespace: Namespace = None):
        """ parses simple class attributes to restplus fields """
        field_type = None
        # if generic type
        if hasattr(attr_type, '__origin__'):
            field_type = self.generic_to_restplus(attr_type, namespace)
        # not generic and it is a basic type
        elif attr_type == typing.Any:
            field_type = AnyTypeField
        elif attr_type.__name__ in self.type_mapper:
            field_type = self.type_mapper.get(attr_type.__name__)
        # a user defined class
        else:
            field_type = self.complex_to_restplus(attr_type, namespace)

        return field_type

    def complex_to_restplus(self, attr_type, namespace: Namespace):
        """ parses complex types (classes) to sub-models in restplus """
        if not namespace:
            raise Exception(f"Type {attr_type} [{attr_type.__name__}] is complex, please provide the Restplus namespace that defines other types")
        if not attr_type.__name__ in namespace.models:
            raise Exception(f"Cannot find restplus model for {attr_type} [{attr_type.__name__}] in namespace {namespace}, make sure it is delcared before this type")
        rest_model = namespace.models.get(attr_type.__name__)
        field_type = fields.Nested(rest_model)

        return field_type

    def generic_to_restplus(self, attr_type, namespace: Namespace):
        """ parses generic types Union, Literal, etc and converts them to restplus model """
        generic_type = attr_type.__origin__
        generic_args = attr_type.__args__ if attr_type.__args__ else None
        generic_arg = generic_args[0] if generic_args else None

        generic_type_mapped = None

        # if the generic is Literal (str)
        if generic_type == typing.Literal:
            field_type = self.type_mapper.get('str')
            return field_type

        if generic_type in [typing.Union, typing.Optional]:
            # if Optional or Union[Somthing, None]
            if len(generic_args) == 2 and generic_args[1] == type(None):
                return self.attr_to_restplus(generic_args[0], namespace)

            raise Exception(f"Union types are not supported in API models, use Optional or Union[type, None] instead. found {generic_args}")

        generic_type_mapped = self.type_mapper.get(generic_type.__name__)

        if generic_type_mapped:
            # if the generic is simple type
            field_arg = self.attr_to_restplus(generic_arg, namespace)
            field_type = generic_type_mapped(field_arg)
        else:
            raise Exception(f"Unknonw Generic type {generic_type}")

        return field_type


def class_to_restplus(model: typing.Any, namespace=None):
    """ converts a python mypy class to a restplus model """
    masked = model.__masked__ if hasattr(model, "__masked__") else []
    ret = {}
    for (attr_name, attr_type) in model.__annotations__.items():
        # print("decoding", attr_name, attr_type)

        field_type = RestModel(mapper=python2restplus).attr_to_restplus(attr_type, namespace)
        if not field_type:
            raise Exception(f"Cannot Map {attr_name} of type {attr_type.__name__} to a Restplus Model")

        if (attr_name not in masked) and field_type:
            ret[attr_name] = field_type
    return ret


def model_to_restplus(model: flask_sqlalchemy.Model):
    """ converts model class to Restuplus Field types, 
    it does not handle Nested items, it leaves this to the caller to append them to the returned dictionary
    it also ingores __protected__ columns like passwords just add it to Model.__protected__ list
    """
    masked = model.__masked__ if hasattr(model, "__masked__") else []
    ret = {}
    for column in sqlalchemy.inspect(model).mapper.columns:
        # skip if primary key
        # if not c.primary_key:
        column_type = 'UUID' if isinstance(column.type, sqlalchemy.dialects.postgresql.base.UUID) else column.type.python_type.__name__
        field_type = python2restplus.get(column_type)
        # pprint(str.format("mapping {0}({1}) => {2}", c.key, column_type, field_type))
        if (column.key not in masked) and field_type:
            if column_type != "list":
                ret[column.key] = field_type(description=column.doc)
            else:
                ret[column.key] = field_type(python2restplus.get("str"), description=column.doc)
    return ret


def class_to_parser(model: typing.Any, locations: ParserLocations):
    """ converts Python class (POPO = Plain Old Python Object) to Restuplus Parser, 
    it does not handle Nested items, it leaves this to the caller to append them to the returned dictionary
    it also ingores __protected__ attribute like passwords just add it to Model.__protected__ list
    it assumes the POPO contain class attributes with mypy types or Python type data
    """
    parser = reqparse.RequestParser()

    masked = model.__masked__ if hasattr(model, "__masked__") else []

    for (attr_name, attr_type) in model.__annotations__.items():
        # print("decoding", attr_name, attr_type)

        # does not support MyPy types - refer to attr_to_restplus for how it is implemented for models
        field_type = RestModel(mapper=python2type).attr_to_restplus(attr_type)
        if not field_type:
            raise Exception(f"Cannot Map {attr_name} of type {attr_type.__name__} to a Restplus Model")

        if (attr_name not in masked) and field_type:
            # print(f"parser: {attr_name=}, {locations=}, {field_type=}")
            parser.add_argument(attr_name, location=locations, type=field_type)

    return parser
