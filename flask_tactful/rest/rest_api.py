from flask_swagger_ui import get_swaggerui_blueprint 
from flask import Blueprint, Flask, current_app
from flask_restx import Api

from .json_encoders import RESTFULEncoder

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

def RestApi(app: Flask, title:str, api_name:str='api', api_prefix='/v3', docs_url: str='/docs') -> Api:
    app.config.update(RESTPLUS_JSON={'cls': RESTFULEncoder})
    app.config.update(SWAGGER_SUPPORTED_SUBMIT_METHODS=["get", "post", "delete", "put"])
    app.config.update(RESTPLUS_MASK_SWAGGER=False)

    swaggerui_blueprint = get_swaggerui_blueprint(
        base_url=docs_url,
        # hides the modules and control SwaggerUI js plugin
        # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
        config=dict(
            app_name=title, layout='BaseLayout',
            defaultModelsExpandDepth=1,
            docExpansion='none', 
        ),
        api_url=f"{api_prefix}/swagger.json",
        blueprint_name="swagger_ui"+api_name
    )

    api_blueprint = Blueprint(api_name, __name__, url_prefix=api_prefix)
    rest_api_v3= Api(blueprint=api_blueprint, url_prefix=api_prefix, authorizations=authorizations, security='apikey',title=title)


    app.register_blueprint(swaggerui_blueprint, url_prefix=api_prefix)

    app.register_blueprint(api_blueprint, url_prefix=api_prefix)

    #---------------------------------------------------------------------------------------
    app.route('/docs', methods=['GET'])

    app.add_url_rule('/favicon.ico', favicon,methods=['GET'])

    return rest_api_v3

def show_api_docs():
    """Redirects to the homepage in our case it is the orders page."""
    return current_app.send_static_file("api-reference.html")

        
def favicon():
    """Redirects to the homepage in our case it is the orders page."""
    return current_app.send_static_file("favicon.ico")
