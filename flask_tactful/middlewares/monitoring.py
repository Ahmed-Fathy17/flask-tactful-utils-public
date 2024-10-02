import logging
import bugsnag
from bugsnag.flask import handle_exceptions
from ..logger import configure_logger

def init_app(app):
    """ configures default monitoring using busgnag and logging for any flask app"""

    # Configure Bugsnag
    bugsnag.configure(
        api_key=app.config.get('BUGSNAG_KEY', "a250c2a3659a4a81effa97aa7bf30fe6"),
        notify_release_stages=["dstnyengage", "production", "staging", "beta", "alpha", "demo", "test", "qa", "eco", "channels", "eng"],
        release_stage=app.config.get('STAGE', 'development'),
        auto_notify=True,
        # project_root = "/path/to/your/app",
    )
    # Attach Bugsnag to Flask's exception handler

    handle_exceptions(app)

    logging_levels = {
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'DEBUG': logging.DEBUG
    }
    # formatter = logging.Formatter(
    #     '%(asctime)s [%(levelname)s] %(filename)s: %(message)s')

    ########## Logging handler for (WARNING and above) severity ##########
    level = logging_levels.get(app.config['LOG_LEVEL'].upper(), 10000000)

    ############ Logging handler for (debugging and above) severity ######
    # std_handler.setFormatter(formatter)
    # pylint: disable=no-member
    app.logger.setLevel(level)
    configure_logger(app)


# we could use @app.errorhandler(Exception) here, but this will be too broad and will make development harder.
# also all Exceptions will develop to become 500 eventually so in production this will catch all issues anyways

# @app.errorhandler(500)
# def page_not_found(ex):
#     try:
#         bugsnag.notify(ex)
#         app.logger.error("Error 500 %s", ex.message)
#         app.logger.info("Error 500 %s", ex.message)
#         code = ex.code if ex and isinstance(ex, HTTPException) else 500
#         return render_template('error.html', error=ex), code

#     except HTTPException as e:
#         app.logger.info("Exception of the error handler 500")
#         code = e.code if e and isinstance(e, HTTPException) else 500
#         app.logger.info("Error 500 %s", e.message)
#         return render_template('error.html', error=e), code

#     except Exception as e:     # pylint: disable=broad-except
#         app.logger.info("Exception of the error handler 500")
#         code = e.code if e and isinstance(e, HTTPException) else 500
#         app.logger.info("Error 500 %s", e.message)
#         return render_template('error.html', error=e), code

# @app.errorhandler(405)
# def unauthorized(ex):
#     bugsnag.notify(ex)
#     app.logger.error("Error 405 %s", ex.message)
#     code = ex.code if ex and isinstance(ex, HTTPException) else 500
#     return render_template('unauthorized.html', error=ex), code
