""" Abstracts Relational Database and migrations
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


def init_app(app: Flask):
    """initializes sqlalchemy and alembic migrations, call it in the App factory function

    Args:
        app (Flask): _description_

    Returns:
        _type_: _description_
    """
    
    db = SQLAlchemy()
    db.init_app(app)
    app.db = db
    
    app.migrate = Migrate(app, db)

    return db
    
