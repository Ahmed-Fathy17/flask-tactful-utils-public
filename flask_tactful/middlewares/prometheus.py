import os

from flask import Flask
from flask_restx import Api

from prometheus_flask_exporter import RESTfulPrometheusMetrics


def init_metrics(app: Flask, api: Api) -> None:
    if os.environ.get('FLASK_PROMETHEUS_ENABLED', 'false').lower() == 'true':
        app.logger.info("prometheus init")
        RESTfulPrometheusMetrics(app, api, group_by='url_rule')
