
from typing import Any, Dict, Iterable, List, Optional
import json
import time
import socket
import logging
from pydantic import parse_obj_as
from flask import Flask
from redis import Redis
from redis.exceptions import RedisError, ConnectionError

from ..ddd import Event
from .bus import TactfulBus


class TactfulRedisStreamBus(TactfulBus):
    """ Bus (Message Queue/Broker) utility class based on Redis Streams

    this implementation utilizes Consumer Groups, so it will allow the following scenarios

    1. Scalable Subscribers (multiple instances of the same service, e.g multiple automation services each recieves different messages that the other instances [load balancing])
    2. Multiple Subscribers Fan-out (multiple services [even if each has multiple instances] each service will recieve a copy of the same messages published)
    3. Multiple topic listening (each instance or service can subscribe to multiple topics and recieve events sent to this topic)
    4. Resilliance: an instance can crash then it will resume reading from where it stopped before crashing (using consumer groups)

    Limitations of this implementation

    1. No Topic semantics, topics does not support patterns (like billing:*) or (test:*) or other pattern based sematics. A topic must be speicifed correctly
        so each service must use 1 topic to publish information
    2. No elastic/automatic-scaling: cosnumer group size is static and does not change based on the clients
    """

    redis: Redis
    """ redis client, for internal use """

    group_name: str
    """ name of consumer_group (detected based on environment variable REDIS_CONSUMER_GROUP) """

    consumer_name: str
    """ name of the server, to use as the consumer name """

    @classmethod
    def from_app(cls, app: Flask, **kw):
        app.after_request
        """Initializes a bus from flask application, it fetches the configuration from flask.config and will use flask.logger for logging
        REDIS_BUS_URL: redis:// formatted url (or BUS_URL for backward compatibility)
        REDIS_CONSUMER_GROUP: name of the consumer group (usually the service name) that will have multiple instances of the same service reading events in a load balanced fashion
        REDIS_CONSUMER_NAME: name of the consumer, must be the same after restarting, if not provided, the hostname will be used
        STAGE: name of the current environment (e.g. test, prod) to be used as a prefix for apps
        Notes about consumer name:

        1. Use Kubernetes StatefulSets, to preserve each client ID (pods will be called bot-1, bot-2)
        2. If Kubernetes ReplicaSets are used, suply a static name in REDIS_CONSUMER_NAME, but only 1 client will be supported in this case 
        (pods will be called bot-xxa1931, bot-ssz1932, which is dynamic naming and changes with each deployment)

        Args:
            app (Flask): Flask application with config initialized
            kw (var arg): Redis client specific parameters

        """
        return cls(
            app=app,
            bus_url=app.config.get("REDIS_BUS_URL", None) or app.config.get("BUS_URL", None),
            group_name=app.config.get("REDIS_CONSUMER_GROUP", None),
            consumer_name=app.config.get("REDIS_CONSUMER_NAME", socket.gethostname()),
            prefix=app.config.get("STAGE", "local:"),
            logger=app.logger,
            busReconnectionTimeout=app.config.get("REDIS_RECONNECTION_TIMEOUT", 120),
            **kw
        )

    def __init__(self, app: Flask, bus_url: str, group_name: str, consumer_name: str, prefix: str = "local:", logger: Optional[logging.Logger] = None, busReconnectionTimeout = 120, **kw):
        super().__init__(app=app, prefix=prefix, logger=logger, **kw)
        self.redis = Redis.from_url(url=bus_url, decode_responses=True)
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.busReconnectionTimeout = busReconnectionTimeout

        if not (group_name and consumer_name):
            raise AttributeError("must provide REDIS consumer group and consumer names. Bus works only in Consumer Groups mode.")

    def _prepare_streams(self):
        """initialized the streams and consumer groups for reading
        if the consumer group already exists (the application just crashed) it will reuse the consumer group
        this will also create the stream (topic) 
        """
        watched_streams = self.get_topics()
        self.logger.debug("preparing handlers for: %s", watched_streams)
        for stream in watched_streams:
            self.logger.info(f"initializing stream {stream}")

            # try creating a consumer group if it does not exist, and make the stream as well
            try:
                self.redis.xgroup_create(name=stream, groupname=self.group_name, mkstream=True)
            except RedisError as e:
                self.logger.error("error creating consumer group %s for stream %s, this means it already exists, continue..", self.group_name, stream)
            finally:
                # dump the stream info for debugging
                stream_info = self.redis.xinfo_stream(stream)
                groups_info = self.redis.xinfo_groups(stream)
                self.logger.info(f"stream info: {stream_info}")
                self.logger.info(f"group info {groups_info}")

    def read(self, count: int = 1) -> List[Event]:
        """ reads from the bus, **dont use directly**, instead use the on() decorator which is more powerful

        Args:
            streams (Iterable[str]): list of streams to read from, if multiple streams are provided the function returns atleast one message 
            count (int, optional): _description_. Defaults to 1.

        Returns:
            List[Event]: _description_
        """
        streams = self.get_topics()
        events: List[Event] = []
        self.logger.debug(f"blocking on streams {streams}")
        streams_results = self.redis.xreadgroup(groupname=self.group_name, consumername=self.consumer_name, streams={s: '>' for s in streams}, count=count, block=50000)
        self.logger.debug(f"read a stream message {streams_results}")
        for (stream_key, stream_messages) in streams_results:
            for (msg_id, msg) in stream_messages:
                events.append(self._format_event(msg_id, msg))

        return events

    def _format_event(self, msg_id: str, msg: Any) -> Event:
        self.logger.debug(f"parsing redis at: {msg_id} message: {msg}")
        # convert json into a dict
        msg_dict = json.loads(msg["message"])
        # convert dict into an event
        event = Event.parse_obj(msg_dict)
        event.msg_id = msg_id
        return event

    def _start_reading(self):
        super()._start_reading()
        connected = False
        while not connected:
            try:
                self._prepare_streams()
                connected = True
                while (True):
                    events = self.read(count=1)
                    for event in events:
                        self._run_handlers(event)
                    self._stop_if_interrupted()
            except ConnectionError as e:
                connected = False
                errorMessage = f"Connection error: {e}. Retrying in {self.busReconnectionTimeout} seconds..."
                if self.logger:
                    self.logger.error(errorMessage)
                else:
                    print(errorMessage)
                time.sleep(self.busReconnectionTimeout)
    
    def shutdown(self, signal: int, frame: Any):
        self.redis.close()

    def send(self, topic: str, raw_msg: Dict, **send_opts) -> str:
        return self.redis.xadd(name=topic, fields=raw_msg, **send_opts)

    def publish(self, event: Event, **send_opts) -> str:
        # convert the event into a dict
        event_dict = event.dict()
        # convert the dict into a json
        event_json = json.dumps(event_dict)
        msg_id = self.send(topic=event.topic, raw_msg={"message": event_json}, **send_opts)
        event.msg_id = msg_id
        return msg_id

    def _on_handler_error(self, e: Exception):
        return super()._on_handler_error(e)

    def _msg_handled(self, msg: Event):
        self.redis.xack(msg.topic, self.group_name, msg.msg_id)

    def delete_all(self):
        watched_streams = self.get_topics()
        self.logger.warn(f"destroying the following streams {watched_streams}")

        for stream in watched_streams:
            try:
                self.redis.xgroup_destroy(name=stream, groupname=self.group_name)
            except RedisError as e:
                self.logger.error("error deleting consumer group %s for stream %s", self.group_name, stream)

        try:
            self.redis.delete(*watched_streams)
        except RedisError as e:
            self.logger.error(f"error deleting streams {watched_streams}")
