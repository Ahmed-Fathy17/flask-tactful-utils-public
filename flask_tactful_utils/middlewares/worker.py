""" Adds Celery worker support to flask, also enabled tasks to access flask app context
"""

from celery import Celery, Task

def init_app(app):
    """ initialize celery support """
    celery = Celery('app')
    celery.conf.update(app.config)
    
    # pylint: disable=abstract-method
    class FlaskTask(Task):
        """ this custom task allows the code to use current_app and other flask stuff
        this allows us to share code between Flask App and Celery worker
        """
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)
    
    # make this the default task type
    celery.Task = FlaskTask
    return celery
