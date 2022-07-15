""" Abstracts Relational Database and migrations
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

def init_app(app):
    """ initializes sqlalchemy and alembic migrations, call it in the App factory function """
    db.init_app(app)
    app.db = db
    
    app.migrate = Migrate(app, db)
