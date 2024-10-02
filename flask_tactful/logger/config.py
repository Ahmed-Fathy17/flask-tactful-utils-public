import logging
import re
from logging.config import dictConfig
from bugsnag.handlers import BugsnagHandler

def configure_logger(app):
    LOG_MODULES = app.config.get("LOG_MODULES", "")
    LOG_LEVEL = app.config.get("LOG_LEVEL", 10000000)

    enabled_modules = [module for module in re.split(r'[\s,]+', LOG_MODULES) if module]
    loggers_to_enable = [name for name in logging.root.manager.loggerDict if any([re.match(regex, name) for regex in enabled_modules])]
    loggers = { logger_name: {'level': LOG_LEVEL, 'handlers': ['default_stream_handler'], 'propagate': False } for logger_name in loggers_to_enable }
    loggers.update({
        app.name:{
            'level': LOG_LEVEL,
            'handlers': ['default_stream_handler', 'bugsnag_handler'],
            'propagate': False
        }
    })

    config_dict = {
        'version': 1,
        'disable_existing_loggers': True,
        'incremental': False,
        'formatters': {
            'custom_formatter': {
                '()': 'flask_tactful.logger.formatter.CustomFormatter',                
                'app_config': app.config
            }
        },
        'handlers': {
            'default_stream_handler': {
                'class': 'logging.StreamHandler',
                'formatter': 'custom_formatter',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'level': LOG_LEVEL,
            },
            'bugsnag_handler': {
                '()': BugsnagHandler,
                'level': logging.WARNING
            }
        },
        'loggers': loggers,
        'root': {
            'level': LOG_LEVEL,
            'handlers': ['default_stream_handler'],
        }
    }
    dictConfig(config_dict)
        
