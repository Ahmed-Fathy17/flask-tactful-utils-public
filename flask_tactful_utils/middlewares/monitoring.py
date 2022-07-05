import bugsnag
from bugsnag.flask import handle_exceptions
from bugsnag.handlers import BugsnagHandler


def init_bugsnag(app):
    # Configure Bugsnag
    bugsnag.configure(
        api_key=app.config.get('BUGSNAG_KEY',"a250c2a3659a4a81effa97aa7bf30fe6"),
        notify_release_stages=["production", "staging", "beta", "alpha", "demo", "test","qa", "eco","channels","eng"],
        release_stage=app.config.get('STAGE', 'development'),
        auto_notify=True,
        #project_root = "/path/to/your/app",
    )
    # Attach Bugsnag to Flask's exception handler

    handle_exceptions(app)
