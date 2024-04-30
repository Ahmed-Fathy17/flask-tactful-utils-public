from flask_swagger_ui import get_swaggerui_blueprint
from flask import Blueprint, Flask, current_app, render_template_string, redirect
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


def RestApi(app: Flask, title: str, api_name: str, api_version: str) -> Api:
    """Creates a Flask Restful API with Swagger UI documentation.

    Args:
        app (Flask):Flask app instance
        title (str): Title at the top of the Swagger documentation
        api_name (str, optional): Title of the API.
        api_version (str, optional): Version of the API.

    Returns:
        Api: Flask-RESTPlus rest_api instance, which can be used to define and manage API namespaces and resources.
    """
    # Updates the Flask application configuration
    app.config.update(RESTPLUS_JSON={'cls': RESTFULEncoder}) # specify a JSON encoder class (RESTFULEncoder) to handle objects that aren't serializable by default
    app.config.update(SWAGGER_SUPPORTED_SUBMIT_METHODS=["get", "post", "delete", "put"]) # specify the supported HTTP methods for Swagger documentation
    app.config.update(RESTPLUS_MASK_SWAGGER=False) # disable masking of sensitive information in Swagger documentation

    # Define API prefix
    api_prefix = f'/{api_name}/{api_version}'
    # Define docs prefix
    docs_prefix = f"/{api_name}/{api_version}"
    
    # Define Routes
    swagger_url = f"{docs_prefix}/swagger.json"
    swagger_docs_url = f"{docs_prefix}/swagger"
    docs_url = f"{docs_prefix}/docs"

    # Creates a Swagger UI blueprint and configures the Swagger UI for displaying API documentation.
    swaggerui_blueprint = get_swaggerui_blueprint(
        base_url=swagger_docs_url,
        # hides the modules and control SwaggerUI js plugin
        # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
        config=dict(
            app_name=title, layout='BaseLayout',
            defaultModelsExpandDepth=1,
            docExpansion='none',
            queryConfigEnabled=False,
            displayOperationId=True,
            persistAuthorization=True,
        ),
        oauth_config=dict(  # OAuth config. See https://github.com/swagger-api/swagger-ui/blob/master/docs/usage/oauth2.md.
            clientId="connectme",
            # clientSecret="NEVER FILL THIS or it will be exposed in the browser",
            realm="your-realms",
            appName="swagger",
            scopeSeparator=" ",
            additionalQueryStringParams={'profile': "0"}
        ),
        api_url=swagger_url,
        blueprint_name="swagger_ui" + api_name
    )

    # Creates a Flask Blueprint for the API 
    api_blueprint = Blueprint(api_name, __name__, url_prefix=api_prefix)

    # Creates an instance of Flask-RESTPlus's Api class
    rest_api = Api(app=api_blueprint,
                   url_prefix=api_prefix,
                   authorizations=authorizations,
                   security='apikey',
                   title=title)
    rest_api.add_namespace(default_general_namespace)

    # Register the Swagger UI blueprint and the API blueprint with the Flask application
    app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_docs_url)
    app.register_blueprint(api_blueprint, url_prefix=api_prefix)

    # ---------------------------------------------------------------------------------------

    # adds a URL rule for serving a favicon.ico file
    app.add_url_rule('/favicon.ico', view_func=favicon, methods=['GET'])

    # Defines a route for serving API documentation when a GET request is made to the URL specified by docs_url.
    @app.route(docs_url, methods=['GET'])
    def show_api_docs():
        """Redirects to the homepage in our case it is the orders page."""
        return render_template_string(template, swagger_url=swagger_url)
    
    @app.route(api_prefix)
    def docs():
        return redirect(docs_url)
    return rest_api


def favicon():
    """Redirects to the homepage in our case it is the orders page."""
    return current_app.send_static_file("favicon.ico")
