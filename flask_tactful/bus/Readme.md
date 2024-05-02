# Redis Stream Bus

## Table of Contents

- [Redis Stream Bus](#redis-stream-bus)
  - [Table of Contents](#table-of-contents)
  - [Tactful Bus](#tactful-bus)
  - [What is Redis Stream?](#what-is-redis-stream)
  - [Usage?](#usage)

## Tactful Bus

Tactful Bus is a library that provides a simple and easy-to-use API for sending and receiving messages between services. It is designed to be used as a message bus for microservices architectures.

It provides different underlying implementations for the message bus, such as Redis Streams, Redis Pub/Sub, Kafka, etc. This allows you to easily switch between different implementations without having to change your code.

## What is Redis Stream?

Redis Streams is a data structure designed for managing real-time data streams. It's a log-like data structure where data (events) is stored in chronological order -in the order they occurred or were created, from the earliest to the most recent- and can be consumed by multiple consumers. Streams are useful for building applications that handle real-time events and messaging systems.

Streams consist of entries called messages, and each message is associated with a unique ID. Messages are stored in chronological order, and new messages are always appended at the end of the stream.

## Usage?

```Python
# Imports
from flask import Flask
from flask_tactful.ddd import Event
from flask_tactful.bus import TactfulRedisStreamBus

# Configuration & Bus Creation
REDIS_URL = "redis://localhost:6379/0"
bus = TactfulRedisStreamBus(
    app=Flask(__name__),
    bus_url=REDIS_URL,
    group_name="svcName",
    consumer_name="pod-1"
  )
  
# Create your event 
event = Event(
  version= 1
  topic= "tactful.svc", 
  event= "TestEvent", 
  msg_id= '1234567890',
  profile_id= 1
  )

# Publish the event
bus.publish(event)

# Subscribe to a specific event
@bus.on("tactfulTopic", "TestEvent")
def testevent_handler(event: Event):
    # Add your logic here
    pass
    
# Start consuming messages
bus.start() 
```
