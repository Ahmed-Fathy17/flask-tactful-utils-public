from celery import Celery, Task

def init_app(app):

    celery = Celery('app')
    celery.conf.update(app.config)
    # this custom task allows the code to use current_app and other flask stuff
    # this allows us to share code between Flask App and Celery worker
    # pylint: disable=abstract-method
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super(FlaskTask, self).__call__(*args, **kwargs)
    
    # make this the default task type
    celery.Task = FlaskTask
    return celery

