
import logging
import json
import threading
import signal
from typing import Any, Dict

from flask import Flask
import flask
from kafka import KafkaProducer, KafkaConsumer

from ..ddd import Event

class TactfulBus():
    """ Bus (Message Queue/Broker) utility class. 
    Allows Flask app to listen to bus events and send events to the bus """
    
    producer: KafkaProducer
    kafka_config: Dict
    handlers: Dict
    event_handlers: Dict
    interrupt_event: threading.Event
    logger: logging.Logger

    def __init__(self, app: Flask, **kw):

        kw.setdefault("bootstrap_servers", app.config.get("KAFKA_SERVERS"))
        kw.setdefault("client_id", app.config.get("KAFKA_CLIENT_ID"))
        self.kafka_config = kw
        self.logger = app.logger
        self._create_consumer(**kw)
        self._create_producer(**kw)

    def _create_consumer(self, **kw):
        consumer_config = kw.copy()
        consumer_config.setdefault("value_deserializer", lambda m: json.loads(m.decode('ascii')))

        self.consumer = KafkaConsumer(**consumer_config)
        self.handlers={}
        self.event_handlers={}
        self.interrupt_event = threading.Event()

    def _create_producer(self, **kw):
        producer_config = kw.copy()
        producer_config.setdefault("value_serializer", lambda m: json.dumps(m).encode('ascii'))
        self.producer = KafkaProducer(**producer_config)



    def listen_kill_server(self):
        """ handle termination signals and gracefully shutdown """
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGQUIT, self.shutdown)
        signal.signal(signal.SIGHUP, self.shutdown)

    def shutdown(self):
        """ shutdown the bus listenrs, this will close the consumer first """
        self.logger.info("closing consumer")
        self.consumer.close()
        self.logger.info("Flushing producer")
        self.producer.flush()

    def send(self, topic: str, msg: Any, **send_opts):
        """ sent a message to the bus topic specified """
        self.producer.send(topic, msg, **send_opts)

    def publish(self, event: Event, **send_opts):
        """ sent an event to the event specified topic event.__topic__ """
        self.producer.send(topic=event.__topic__, value=event, **send_opts)

    def on(self, topic: str, event: str):
        """ decorator to listen to a specific event on a topic, function must accept a paremeter of type Event """
        def decorator(f):
            self._add_event_handler(topic, event, f)
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

    def handle(self, topic):
        def decorator(f):
            self._add_handler(topic, f)
            return f
        return decorator

    def _run_handlers(self, msg):
        try:
            handlers = self.handlers(msg.topic)
            event_handlers = []
            if msg.value and 'name' in msg.value:
                event_handlers = self.event_handlers.get(f"{msg.topic} +{msg.value.get('name')}")
            for handler in handlers:
                handler(msg)
            for event_handler in event_handlers:
                event_handler(msg.value)
            self.consumer.commit()
        except Exception as e:
            self.logger.critical(str(e), exc_info=1)
            self.consumer.close()

    def _start(self):
        self.consumer.subscribe(topics=tuple(self.handlers.keys()))
        self.logger.info("starting consumer...registered signterm")

        for msg in self.consumer:
            self.logger.debug(f"TOPIC: {msg.topic}, PAYLOAD: {msg.value}")
            self._run_handlers(msg)
            # stop the consumer
            if self.interrupt_event.is_set():
                self.interrupted_process()
                self.interrupt_event.clear()
  
    def start(self):
        # run the consumer application
        self.logger.info("Consuming Kafka events...")
        t = threading.Thread(target=self._start)
        t.start()
