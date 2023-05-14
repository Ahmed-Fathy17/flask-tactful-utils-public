
from typing import Dict
from flask import Flask, redirect
from flask.globals import _find_app
from werkzeug.local import LocalProxy
from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_restx import Api
from flask_migrate import Migrate

from . import database
__all__ = ["TactfulFlask"]

from .bus import TactfulBus, TactfulRedisStreamBus
from .middlewares import worker, ReverseProxied, AuthMiddleware, monitoring
from .rest import RestApi
from .auth.jwt_manager import TactfulJwt


class TactfulFlask(Flask):
    """Tactful flavoured version of Flask, comes with pre-initialized modules like:

    1. SQLAlchemy, as ORM
    2. Migrations, Alembic for managing DB migrations
    3. Celery, for async worker tasks
    4. RestX, for Rest API management, pre-initialized to generate Swagger documentation
    5. Bus, TactfulBus (powered by RedisStreams) 
    6. Logger and Bugsnag, for tracability and error management
    """

    db: SQLAlchemy
    celery: Celery
    bus: TactfulBus
    migrate: Migrate
    api: Api
    jwt_manager: JWTManager

    def configure(self, app_config: Dict, api_title: str, api_name='api', api_prefix=''):
        """Configures TactfulFlask customized version

        Args:
            app_config (Dict): Dictionary for Flask config, used to initialzie all the middlewares
            api_title (str): Title at the top of the Swagger documentation
            api_name (str, optional): name of the API. Defaults to 'api'.
            api_prefix (str, optional): prefix to start all APIs after /api/v3 or /tenants/v1, etc. Defaults to ''.

        Returns:
            _type_: _description_
        """
        self.config.update(app_config)
        self.wsgi_app = ReverseProxied(self.wsgi_app)  # type: ignore
        self.wsgi_app = AuthMiddleware(self.wsgi_app, self.config.get('JWT_HEADER_NAME'))  # type: ignore

        self.db = database.init_app(self)
        self.celery = worker.init_app(self)
        self.api = RestApi(self, title=api_title, api_name=api_name, api_prefix=api_prefix)

        # initialize bus
        self.bus = TactfulRedisStreamBus.from_app(self)

        self.jwt_manager = TactfulJwt(app=self).jwt_manager

        # Initialize monitoring
        monitoring.init_app(self)

        @self.route("/")
        def home():
            return redirect("/docs")

        return self


current_app: TactfulFlask = LocalProxy(_find_app)  # type: ignore
