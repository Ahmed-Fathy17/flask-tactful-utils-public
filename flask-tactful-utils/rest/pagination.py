
from flask_restx import Namespace, fields
from .custom_fields import relation_includes_parser

default_general_namespace = Namespace('default')


pagination_model = default_general_namespace.model("pagination", {
    "page": fields.Integer,
    "limit": fields.Integer,
    "itemsCount": fields.Integer,
    "pagesCount": fields.Integer,
})

rule_model = default_general_namespace.model("Rule", {
    "modelName": fields.String,
    "fieldKey": fields.String,
    "mathOp": fields.String,
    "value": fields.String,
    "logicalOp": fields.String,
    "valueType": fields.String,
})

pagination_parser = relation_includes_parser.copy()
pagination_parser.add_argument('limit', type=int, default=10000)
pagination_parser.add_argument('page', type=int, default=1)

def envelop_pagination(ns, model):
    
    return ns.inherit(model.name + "List", pagination_model, {
        'items':  fields.List(fields.Nested(model))
    })
