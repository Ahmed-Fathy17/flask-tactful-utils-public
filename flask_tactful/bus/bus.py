
import logging
import threading
import signal
from typing import Any, Dict, Callable, Optional
import abc

from flask import Flask

from ..ddd import Event

class TactfulBus(abc.ABC):
    """ Bus (Message Queue/Broker) utility class. 
    Allows Flask app to listen to bus events and send events to the bus """
    
    handlers: Dict[str, Any]
    event_handlers: Dict[str, Any]
    interrupt_event: threading.Event
    logger: logging.Logger

    def __init__(self, bus_url:str, group_name: str, consumer_name:str, logger:Optional[logging.Logger]=None, **kw):
        self.logger =  logger if logger else logging.Logger("redis_bus")
        self.handlers={}
        self.event_handlers={}
        self.interrupt_event = threading.Event()

    def listen_kill_server(self):
        """ handle termination signals and gracefully shutdown """
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGQUIT, self.shutdown)
        signal.signal(signal.SIGHUP, self.shutdown)

    @abc.abstractmethod
    def shutdown(self, signal:int, frame: Any):
        """ shutdown the bus listenrs """
        ...
    @abc.abstractmethod
    def send(self, topic: str, msg: Event, **send_opts):
        """ sent a message to the bus topic specified """
        ...

    @abc.abstractmethod
    def publish(self, event: Event, **send_opts):
        """ sent an event to the event specified topic event.__topic__ """
        ...

    def on(self, topic: str, event: str):
        """ decorator to listen to a specific event on a topic, function must accept a paremeter of type Event """
        def decorator(f: Callable[[str, str, Event], None]):
            self._add_event_handler(topic, event, f)
            return f
        return decorator

    def handle(self, topic: str):
        def decorator(f):
            self._add_handler(topic, f)
            return f
        return decorator



    def _add_event_handler(self, topic: str, event: str, handler):
        if self.handlers.get(topic) is None:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)

    def _add_handler(self, topic, handler):
        if self.handlers.get(topic) is None:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)

    
    def _run_handlers(self, msg: Event):
        try:
            handlers = self.handlers.get(msg.topic, [])
            event_handlers = []
            event_handlers = self.event_handlers.get(f"{msg.topic} +{msg.event}", [])
            
            # if no listners on this topic, report a warning
            if not handlers or not event_handlers:
                self.logger.warn(f"no handlers or event listners for this {msg.topic}")
            
            for handler in handlers:
                handler(msg)
            for event_handler in event_handlers:
                event_handler(msg)
            self._msg_handled(msg)
        except Exception as e:
            self.logger.critical(str(e), exc_info=e)
            self._on_handler_error(e)

    @abc.abstractmethod
    def _on_handler_error(self, e: Exception):
        ...

    @abc.abstractmethod
    def _msg_handled(self, msg: Event):
        ...

    @abc.abstractmethod
    def _start_reading(self):
        ...

    def _stop_if_interrupted(self):
        # stop the consumer
        if self.interrupt_event.is_set():
            self.shutdown()
            self.interrupt_event.clear()  

    def start(self):
        # run the consumer application
        self.logger.info("Consuming Kafka events...")
        t = threading.Thread(target=self._start_reading)
        t.start()
