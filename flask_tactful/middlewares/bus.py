

import json
from threading import Event
import signal
from typing import Any, Dict

from flask import Flask
from flask_kafka import FlaskKafka
from kafka import KafkaProducer

INTERRUPT_EVENT = Event()

class TactfulBus(FlaskKafka):
    """ Bus (Message Queue/Broker) utility class. 
    Allows Flask app to listen to bus events and send events to the bus """
    
    producer: KafkaProducer
    kafka_config: Dict

    def __init__(self, app: Flask, **kw):
        kw.setdefault("bootstrap_servers", app.config.get("KAFKA_SERVERS"))
        kw.setdefault("client_id", app.config.get("KAFKA_CLIENT_ID"))
        kw.setdefault("value_deserializer", lambda m: json.loads(m.decode('ascii')))
        kw.setdefault("value_serializer", lambda m: json.dumps(m).encode('ascii'))
        self.kafka_config = kw
        self.producer = KafkaProducer( **self.kafka_config)
        super().__init__(INTERRUPT_EVENT, **kw)

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
