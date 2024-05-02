
from flask_restx import Model, Namespace, fields, reqparse
from .custom_fields import relation_includes_parser

default_general_namespace = Namespace('default')


pagination_model = default_general_namespace.model("pagination", {
    'page': fields.Integer,
    'per_page': fields.Integer,
    'total': fields.Integer
})

rule_model = default_general_namespace.model("Rule", {
    "modelName": fields.String,
    "fieldKey": fields.String,
    "mathOp": fields.String,
    "value": fields.String,
    "logicalOp": fields.String,
    "valueType": fields.String,
})

pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument('page', type=int, default=1, location='args', help='Page number')
pagination_parser.add_argument('per_page', type=int, default=1, location='args', help='Number of items per page')


def envelop_pagination(namespace: Namespace, model: Model):
    """ adds pagination to returned Rest Model by adding [items] array """
    return namespace.inherit(model.name + "List", pagination_model, {
        'items': fields.Nested(model, as_list=True)
    })
