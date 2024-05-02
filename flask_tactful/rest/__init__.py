"""Utilities to support document and generating RESTful APIs

    1. Pagination utilities, adds pagination to any response (eg. page, total)
    2. Type annotations for API Resources (Json, Any, String array)
    3. Filteration query parameters
    4. Converters for MyPy classes and SQL ALchemy models to Restful Models (Swagger)
    5. Documentation docorators
    6. Authentication and authorization decorators based on JWT tokens
    7. CORS support
"""

__all__ = ['default_general_namespace', 'envelop_pagination', 'pagination_model', 'pagination_parser', 'rule_model',
           'AnyTypeField', 'JsonLoadsField', 'LoadStringToList', 'relation_includes_parser',
           'RestFilter',
           'class_to_restplus', 'model_to_restplus', 'class_to_parser',
           'parser_doc', 'doc',
           'RestApi',
           'profile_access_permission', 'require_admin', 'is_authorized',
           'allow_cors'
           ]

from .pagination import default_general_namespace, envelop_pagination, pagination_model, pagination_parser, rule_model
from .custom_fields import AnyTypeField, JsonLoadsField, LoadStringToList, relation_includes_parser
from .filters import RestFilter
from .rest_model import class_to_restplus, model_to_restplus, class_to_parser
from .parser_doc import parser_doc
from . import doc
from .rest_api import RestApi
from .jwt_decorators import profile_access_permission, require_admin, is_authorized
from .cors import allow_cors
