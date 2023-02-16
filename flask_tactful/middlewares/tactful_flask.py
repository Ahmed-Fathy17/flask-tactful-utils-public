
from flask import Flask
from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from .bus import TactfulBus

class TactfulFlask(Flask):
    db: SQLAlchemy
    celery: Celery
    bus: TactfulBus