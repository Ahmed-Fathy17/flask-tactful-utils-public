
import logging
import threading
import signal
from typing import Any, Dict, Callable, Optional, List
import abc

from ..ddd import Event

TactfulBusTopicHandler = Optional[Callable[[Event], None]]
TactfulBusEventHandler = Callable[[Event], None]


class TactfulBus(abc.ABC):
    """ Bus (Message Queue/Broker) utility class. 
    Allows Flask app to listen to bus events and send events to the bus """

    """ Prefix for all keys and topic names including a separator (e.g. test/ prod/ tactful/), 
    allows us to use , set to current STAGE by default e.g. test:KEYNAME
    """
    prefix: str

    """ List of handler callback functions for each topic or stream, use add_handler(), dont use directly"""
    handlers: Dict[str, List[TactfulBusTopicHandler]]

    """ List of callback handler function for each event, use add_event_handler() or on(), dont use directly"""
    event_handlers: Dict[str, List[TactfulBusEventHandler]]
    
    interrupt_event: threading.Event
    logger: logging.Logger

    def __init__(self, prefix: str = "", logger: Optional[logging.Logger] = None, **kw):
        """Initialize the bus (do it once in the application lifetime)

        Note:
            Use TactfulRedisStreamsBus.from_app(Flask) class-method to initalize in a flask environment instead!

        Args:
            bus_url (str): URL of the bus servers (redis:// or kafka://)
            group_name (str): Consumer group name, should be the name of the service family (bot, channels, ..) regardless of how many instances exist
            consumer_name (str): if not provieded, it is extracted from the current machine/pod/vm host name, a consumer is a unique instance of the service, that gets some of the messages sent to the consumer group. 
            logger (Optional[logging.Logger], optional): Python Logger, if not provieded, one will be created. Defaults to None.
        """
        self.prefix = prefix
        self.logger = logger if logger else logging.Logger("redis_bus")
        self.handlers = {}
        self.event_handlers = {}
        self.interrupt_event = threading.Event()

    def listen_kill_server(self):
        """ handle termination signals and gracefully shutdown """
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGQUIT, self.shutdown)
        signal.signal(signal.SIGHUP, self.shutdown)

    @abc.abstractmethod
    def shutdown(self, signal: int, frame: Any):
        """ shutdown the bus listenrs """
        ...

    """ returns list of subscribed topics of the current application """
    def get_topics(self) -> List[str]:
        return [key for key in self.handlers.keys()]
    

    @abc.abstractmethod
    def send(self, topic: str, raw_msg: Dict, **send_opts) -> str:
        """**Low-level** sends a message to the bus topic specified
        the message is specified as native dict object,

        Warning:
            use bus.publish(Event) instead because all Tactful Microservices expect a message in the format `flask_tactful.ddd.event.Event`

        Args:
            topic (str): Name of the topic to publish the message on
            msg (Dict): Dictionary of data to be sent in the message

        Returns:
            (str) unique ID of the message published on the bus
        """
        ...

    @abc.abstractmethod
    def publish(self, event: Event, **send_opts):
        """sends an event to the event specified topic event.__topic__

        Args:
            event (Event): `flask_tactful.ddd.event.Event` Object representing the TactfulEvent message to be sent to the subscribers 

        Returns:
            Event.msg_id will be filled with the Redis/Kafka message uniquly generated identifier 
        """
        ...

    def on(self, topic: str, event: str):
        """ decorator to listen to a specific event on a topic, function must accept a paremeter of type Event

        Args:
            topic (str): name of the topic, usually prefixed by the system and the environment name (e.g. tactful:qa:billing)
            event (str): name of the event, case-insensitive (e.g. InvoiceCreated)
        """
        def decorator(f: TactfulBusEventHandler):
            self.add_event_handler(topic, event, f)
            return f
        return decorator

    def handle(self, topic: str):
        """Decorator to register a handler for a specific topic, this handler will recieve all the events sent to that topic.
        Use on() even handler instead if you want to listen to a specific event (Recommended)

        Args:
            topic (str): name of the topic, usually prefixed by the system and the environment name (e.x. tactful:qa:billing)
        """
        def decorator(f):
            self._add_handler(topic, f)
            return f
        return decorator

    def add_event_handler(self, topic: str, event: str, handler: TactfulBusEventHandler):
        """Registers a function as an event handler for a specific Event on a Topic

        Warning:
            *Low-Level*, use TactfulBus.on instead as a decorator  

        Args:
            topic (str): topic name to subscribe for the events on
            event (str): specific event to filter (a topic might recieve multiple events, this function will be only called on the registered event type)
            handler (TactfulBusEventHandler): a function that will be called when an event message is recieved on the bus matching the specified event name in param
        """
        event_key = f"{topic}+{event}"
        self._add_handler(topic, None)
        if self.event_handlers.get(event_key) is None:
            self.event_handlers[event_key] = []
        self.event_handlers[event_key].append(handler)

    def _add_handler(self, topic: str, handler: TactfulBusTopicHandler):
        if self.handlers.get(topic) is None:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)

    def _run_handlers(self, msg: Event):
        topic = msg.topic
        try:
            handlers = self.handlers.get(topic, [])
            event_handlers = []
            event_handlers = self.event_handlers.get(f"{topic}+{msg.event}", [])

            # if no listners on this topic, report a warning
            if not handlers or not event_handlers:
                self.logger.warn(f"no handlers or event listners for this {topic}")

            for handler in handlers:
                if handler:
                    handler(msg)
            for event_handler in event_handlers:
                if event_handler: 
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
            self.shutdown(signal.SIGTERM, None)
            self.interrupt_event.clear()

    def start(self):
        """ Start consuming messages from the bus, this will open consumers on the specificed topics
            Must be called after the application is completed initialization, and the on() even listeners are registered.
        """
        # run the consumer application
        self.logger.info("Consuming Kafka events...")
        t = threading.Thread(target=self._start_reading)
        t.start()
