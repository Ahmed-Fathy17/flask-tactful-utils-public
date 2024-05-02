
from typing import Dict
from flask import Flask
from flask.globals import _cv_app
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

    def configure(self, app_config: Dict, api_title: str, api_name, api_version):
        """Configures TactfulFlask customized version

        Args:
            app_config (Dict): Dictionary for Flask config, used to initialize all the middlewares
            api_title (str): Title at the top of the Swagger documentation
            api_name (str): name of the API.
            api_version (str): Version of the API.

        Returns:
            _type_: _description_
        """
        # Updates the Flask application configuration
        self.config.update(app_config)

        # initialize middlewares
        self.wsgi_app = ReverseProxied(self.wsgi_app)  # type: ignore
        self.wsgi_app = AuthMiddleware(self.wsgi_app, self.config.get('JWT_HEADER_NAME'))  # type: ignore

        # initialize database
        self.db = database.init_app(self)

        # initialize task queue
        self.celery = worker.init_app(self)

        # initialize rest api
        self.api = RestApi(self, title=api_title, api_name=api_name, api_version=api_version)

        # initialize bus
        self.bus = TactfulRedisStreamBus.from_app(self)

        # initialize JWT manager
        self.jwt_manager = TactfulJwt(app=self).jwt_manager

        # Initialize monitoring
        monitoring.init_app(self)

        self.cli.add_command(worker_cli)

        return self


current_app: TactfulFlask = LocalProxy(_cv_app, "app")  # type: ignore

import click
from flask.cli import AppGroup

############### Bus Worker

worker_cli = AppGroup('worker')

# run the worker in the foreground, independent from the web server
@worker_cli.command('run')
def run_worker():
    current_app.logger.info("running in WORKER mode, starting bus consumer thread ..")
    current_app.bus.start() 

