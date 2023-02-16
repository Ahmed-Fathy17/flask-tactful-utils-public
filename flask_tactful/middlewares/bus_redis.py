
import json
import threading
import signal
from typing import Any, Dict
import abc

from flask import Flask
from redis import Redis

from ..ddd import Event
from .bus import TactfulBus


class TactfulRedisStreamBus(TactfulBus):
    """ Bus (Message Queue/Broker) utility class. 
    Allows Flask app to listen to bus events and send events to the bus """
    # redis server instance
    redis: Redis
    # name of consumer_group (detected based on environment variable REDIS_CONSUMER_GROUP)
    group_name: str
    
    def __init__(self, app: Flask, **kw):
        super().__init__(app, **kw)
        self.redis = Redis.from_url(url=app.config.get("REDIS_BUS_URL", None))
        self.group_name = app.config.get("REDIS_CONSUMER_GROUP", None)

    def _preapre_stream(self):
        for stream in self.handlers.keys():
            groups = self.redis.xinfo_groups(stream)
            
        

    def _start_reading(self):
        super()._start_reading()
        self._preapre_stream()
