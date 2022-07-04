import typing
from datetime import datetime
from flask_restx import reqparse
from .custom_fields import AnyTypeField

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




ParserLocations = typing.Literal['form', 'headers', 'values', 'args', 'cookies', 'files', 'json']

class RestParser:

    @staticmethod
    def attr_to_parser(attr_type, namespace=None):
        field_type = None
        
        # if generic type
        if hasattr(attr_type, '__origin__'):
            field_type = RestParser.generic_to_parser(attr_type, namespace)
        # not generic and it is a basic type
        elif attr_type == typing.Any:
            field_type = AnyTypeField
        elif attr_type.__name__ in python2type:
            field_type = python2type[attr_type.__name__]
        # a user defined class 
        else:
            field_type = RestParser.complex_to_parser(attr_type, namespace)
        
        return field_type

    @staticmethod
    def complex_to_parser(attr_type, namespace):
        if not namespace:
            raise Exception(f"Type {attr_type} [{attr_type.__name__}] is complex, please provide the Restplus namespace that defines other types")
        if not attr_type.__name__ in namespace.models:
            raise Exception(f"Cannot find restplus model for {attr_type} [{attr_type.__name__}] in namespace {namespace}, make sure it is delcared before this type")
        rest_model = namespace.models.get(attr_type.__name__)
        # field_type = fields.Nested(rest_model)
        raise Exception(f"Parser does not support nested types at the moment {attr_type} [{attr_type.__name__}] in namespace {namespace} is {rest_model}")

    @staticmethod
    def generic_to_parser(attr_type, namespace):
        generic_type = attr_type.__origin__
        generic_args = attr_type.__args__ if attr_type.__args__ else None
        generic_arg = generic_args[0] if generic_args else None

        
        generic_type_mapped = None

        # if the generic is Literal (str)
        if generic_type == typing.Literal:
            field_type = 'str'
            return field_type
        
        if generic_type in [typing.Union, typing.Optional]: 
            # if Optional or Union[Somthing, None]
            if len(generic_args) == 2 and generic_args[1] == type(None) :
                return RestParser.attr_to_parser(generic_args[0], namespace)
            else:
                raise Exception(f"Union types are not supported in API models, use Optional or Union[type, None] instead. found {generic_args}")

        
        generic_type_mapped = generic_type.__name__
        
        if generic_type_mapped:
            # if the generic is simple type
            field_arg = RestParser.attr_to_parser(generic_arg, namespace)
            field_type = generic_type_mapped(field_arg)
        else:
            raise Exception(f"Unknonw Generic type {generic_type}")

        return field_type


# converts Python class (POPO = Plain Old Python Object) to Restuplus Parser, 
# it does not handle Nested items, it leaves this to the caller to append them to the returned dictionary
# it also ingores __protected__ attribute like passwords just add it to Model.__protected__ list
# it assumes the POPO contain class attributes with mypy types or Python type data
def class_to_parser(model, locations: ParserLocations):
    parser = reqparse.RequestParser()
    
    masked = model.__masked__ if hasattr(model, "__masked__") else []

    for (attr_name, attr_type) in model.__annotations__.items():
        # print("decoding", attr_name, attr_type)

        # does not support MyPy types - refer to attr_to_restplus for how it is implemented for models
        field_type = RestParser.attr_to_parser(attr_type)
        if not field_type:
            raise Exception(f"Cannot Map {attr_name} of type {attr_type.__name__} to a Restplus Model")

        if (attr_name not in masked) and field_type:
            # print(f"parser: {attr_name=}, {locations=}, {field_type=}")
            parser.add_argument(attr_name, location=locations, type=field_type)

    return parser
