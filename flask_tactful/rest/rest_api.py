from flask_swagger_ui import get_swaggerui_blueprint 
from flask import Blueprint, Flask, current_app, render_template, render_template_string
from flask_restx import Api

from .docs_template import template
from .json_encoders import RESTFULEncoder
from .pagination import default_general_namespace

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

def RestApi(app: Flask, title:str, api_name:str='api', api_prefix='/api/v3', swagger_docs_url: str='/api/docs',docs_url:str='/docs') -> Api:
    app.config.update(RESTPLUS_JSON={'cls': RESTFULEncoder})
    app.config.update(SWAGGER_SUPPORTED_SUBMIT_METHODS=["get", "post", "delete", "put"])
    app.config.update(RESTPLUS_MASK_SWAGGER=False)

    swagger_url = f"{api_prefix}/swagger.json"

    swaggerui_blueprint = get_swaggerui_blueprint(
        base_url=swagger_docs_url,
        # hides the modules and control SwaggerUI js plugin
        # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
        config=dict(
            app_name=title, layout='BaseLayout',
            defaultModelsExpandDepth=1,
            docExpansion='none', 
        ),
        api_url=swagger_url,
        blueprint_name="swagger_ui"+api_name
    )

    api_blueprint = Blueprint(api_name, __name__, url_prefix=api_prefix)
    rest_api= Api(app=api_blueprint, 
        url_prefix=api_prefix,
        authorizations=authorizations,
        security='apikey',
        title=title)
    rest_api.add_namespace(default_general_namespace)


    app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_docs_url)

    app.register_blueprint(api_blueprint, url_prefix=api_prefix)
    
    #---------------------------------------------------------------------------------------

    app.add_url_rule('/favicon.ico', view_func=favicon, methods=['GET'])

    @app.route(docs_url, methods=['GET'])
    def show_api_docs():
        """Redirects to the homepage in our case it is the orders page."""
        return render_template_string(template, swagger_url=swagger_url)


    return rest_api

        
def favicon():
    """Redirects to the homepage in our case it is the orders page."""
    return current_app.send_static_file("favicon.ico")
