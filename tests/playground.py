from flask import Flask
from redis import Redis

from flask_tactful.bus import TactfulRedisStreamBus
from flask_tactful.ddd import Event

TEST_REDIS_DB = "redis://localhost:6379/11"

# client = Redis.from_url(url=TEST_REDIS_DB)
# client.flushdb(asynchronous=False)
bus_client = TactfulRedisStreamBus(
        app=Flask(__name__),
        bus_url=TEST_REDIS_DB,
        group_name="tests",
        consumer_name="client1"
    )
bus_client.add_event_handler("billing", "CreditCardExpired", None)
bus_client._prepare_streams()
event_out = Event(topic="billing", event="CreditCardExpired", profile_id=1)
bus_client.publish(event_out)
event_in = bus_client.read()[0]
print(event_out)
print(event_in)
