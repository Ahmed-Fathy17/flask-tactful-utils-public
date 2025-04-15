import logging
import bugsnag
from bugsnag.flask import handle_exceptions
from bugsnag.handlers import BugsnagHandler


def init_app(app):
    """ configures default monitoring using Bugsnag and logging for any Flask app """

    # Get BUGSNAG_KEY from env or config

    api_key = app.config.get('BUGSNAG_MONITORING_KEY')
 
    print("Monitoring key:", api_key)

    if not api_key:
        raise RuntimeError("BUGSNAG_KEY is not set. Please set it in the environment or app config.")

    # Configure Bugsnag
    bugsnag.configure(
        api_key=api_key,
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
    level = logging_levels.get(app.config['LOG_LEVEL'].upper(), '')

    ############ Logging handler for (debugging and above) severity ######
    # std_handler.setFormatter(formatter)
    # pylint: disable=no-member
    app.logger.setLevel(level)
    # app.logger.addHandler(std_handler)    # already configured by flask, this causes duplicated logs
    # pylint: disable=no-member

    bugsnag_handler = BugsnagHandler()
    # send only WARNING-level logs and above
    bugsnag_handler.setLevel(logging.WARNING)
    app.logger.addHandler(bugsnag_handler)


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
