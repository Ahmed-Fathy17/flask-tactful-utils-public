
import logging
import json
import threading
import signal
from typing import Any, Dict

from flask import Flask
from kafka import KafkaProducer, KafkaConsumer

from ..ddd import Event
from .bus import TactfulBus

class TactfulKafkaBus(TactfulBus):
    """ Bus (Message Queue/Broker) utility class. 
    Allows Flask app to listen to bus events and send events to the bus """
    
    producer: KafkaProducer
    kafka_config: Dict

    def __init__(self, app: Flask, **kw):
        super().__init__(app, **kw)
        kafka_servers = app.config.get("KAFKA_SERVERS")
        kw.setdefault("bootstrap_servers", kafka_servers)
        kw.setdefault("client_id", app.config.get("KAFKA_CLIENT_ID"))
        self.kafka_config = kw
        self.producer = None


        if not kafka_servers:
            self.logger.warning("no kafka servers defined, will not start broker consumer or producer")
        else:
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
        self.producer.send(topic=event.__topic__, value=event.__dict__, **send_opts)

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
            

    def _msg_handled(self, msg: Any):
        super()._msg_handled(msg)
        self.consumer.commit()

    def _on_handler_error(self, e: Exception):
        super()._on_handler_error(e)
        self.consumer.close()

    def _start_reading(self):
        if not self.consumer:
            self.logger.debug('no consumer defined, skipping bus initialization')
            return
        self.consumer.subscribe(topics=tuple(self.handlers.keys()))
        self.logger.info("starting consumer...registered signterm")

        for msg in self.consumer:
            self.logger.debug(f"TOPIC: {msg.topic}, PAYLOAD: {msg.value}")
            self._run_handlers(msg)
            # stop the consumer
            self._stop_if_interrupted()