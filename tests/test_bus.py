import pytest
import socket
from typing import Tuple
from redis import Redis
from flask import Flask
from flask_tactful.bus import TactfulRedisStreamBus
from flask_tactful.ddd import Event

TEST_REDIS_DB = "redis://localhost:6379/11"


@pytest.fixture()
def reset_bus():
    client = Redis.from_url(url=TEST_REDIS_DB)
    client.flushdb(asynchronous=False)


@pytest.fixture()
def bus_client(reset_bus):
    client1 = TactfulRedisStreamBus(
        app=Flask(__name__),
        bus_url=TEST_REDIS_DB,
        group_name="tests",
        consumer_name="client1",
        approximate_trimming=False # To get exact length trimming. Check: https://stackoverflow.com/a/67526831/14043328
    )
    return client1


@pytest.fixture()
def bus_same_group_clients(reset_bus):
    return (
        TactfulRedisStreamBus(app=Flask(__name__), bus_url=TEST_REDIS_DB, group_name="tests", consumer_name="sender"),
        TactfulRedisStreamBus(app=Flask(__name__), bus_url=TEST_REDIS_DB, group_name="tests", consumer_name="client1"),
        TactfulRedisStreamBus(app=Flask(__name__), bus_url=TEST_REDIS_DB, group_name="tests", consumer_name="client2"),
        TactfulRedisStreamBus(app=Flask(__name__), bus_url=TEST_REDIS_DB, group_name="tests", consumer_name="client3")
    )


@pytest.fixture()
def bus_many_groups_clients(reset_bus):
    return (
        TactfulRedisStreamBus(app=Flask(__name__), bus_url=TEST_REDIS_DB, group_name="test_channels", consumer_name="sender"),
        TactfulRedisStreamBus(app=Flask(__name__), bus_url=TEST_REDIS_DB, group_name="test_chat", consumer_name="client1"),
        TactfulRedisStreamBus(app=Flask(__name__), bus_url=TEST_REDIS_DB, group_name="test_reports", consumer_name="client2"),
        TactfulRedisStreamBus(app=Flask(__name__), bus_url=TEST_REDIS_DB, group_name="test_billing", consumer_name="client3")
    )


def test_flask_initilaization():
    app = Flask("test")
    app.config["REDIS_BUS_URL"] = TEST_REDIS_DB
    app.config["REDIS_CONSUMER_GROUP"] = "tests"

    bus = TactfulRedisStreamBus.from_app(app=app)
    assert bus
    assert bus.consumer_name == socket.gethostname()

def test_redis_client(bus_client: TactfulRedisStreamBus):
    bus_client.add_event_handler("billing", "CreditCardExpired", None)
    bus_client._prepare_streams()
    event_out = Event(topic="billing", event="CreditCardExpired", profile_id=1)
    bus_client.publish(event_out)
    event_in = bus_client.read()[0]

    assert event_in == event_out

def test_redis_group_loadbalancing(bus_same_group_clients: Tuple[TactfulRedisStreamBus, ...]):
    (sender, client1, client2, client3) = bus_same_group_clients

    # recieve events in each client
    client1.add_event_handler("billing", "CreditCardExpired", None)
    client1._prepare_streams()

    client2.add_event_handler("billing", "CreditCardExpired", None)
    client2._prepare_streams()

    client3.add_event_handler("billing", "CreditCardExpired", None)
    client3._prepare_streams()

    # send some events
    events_out = [
        Event(topic="billing", event="CreditCardExpired", profile_id=1),
        Event(topic="billing", event="CreditCardExpired", profile_id=1),
        Event(topic="billing", event="CreditCardExpired", profile_id=1),
    ]
    [sender.publish(ev) for ev in events_out]

    events_in1 = client1.read()
    events_in2 = client2.read()
    events_in3 = client3.read()

    assert len(events_in1) > 0
    assert len(events_in2) > 0
    assert len(events_in3) > 0
    assert events_in1 != events_in2
    assert events_in2 != events_in3

def test_redis_group_fanout(bus_many_groups_clients: Tuple[TactfulRedisStreamBus, ...]):
    (sender, client1, client2, client3) = bus_many_groups_clients

    # recieve events in each client
    client1.add_event_handler("billing", "CreditCardExpired", None)
    client1._prepare_streams()

    client2.add_event_handler("billing", "CreditCardExpired", None)
    client2._prepare_streams()

    client3.add_event_handler("billing", "CreditCardExpired", None)
    client3._prepare_streams()

    # send some events
    events_out = [
        Event(topic="billing", event="CreditCardExpired", profile_id=1),
        Event(topic="billing", event="CreditCardExpired", profile_id=1),
        Event(topic="billing", event="CreditCardExpired", profile_id=1),
    ]
    [sender.publish(ev) for ev in events_out]

    events_in1 = client1.read()
    events_in2 = client2.read()
    events_in3 = client3.read()

    assert len(events_in1) > 0
    assert len(events_in2) > 0
    assert len(events_in3) > 0
    assert events_in1 == events_in2 == events_in3

def test_max_stream_length(bus_client: TactfulRedisStreamBus):
    bus_client.approximate_trimming = False  # Enable approximate trimming
    max_stream_len = 4  # Define the maximum stream length
    extra_events = 2  # Define the number of extra events to publish

    # Add event handlers and prepare streams for the client
    bus_client.add_event_handler("billing", "CreditCardExpired", None)
    bus_client._prepare_streams()

    # Publish more events than the maximum stream length
    events_out = [
        Event(version = 2, topic="billing", event="CreditCardExpired", profile_id=i, max_stream_len=max_stream_len)
        for i in range(max_stream_len + extra_events)
    ]
    for event in events_out:
        bus_client.publish(event)

    # Read events from the stream
    events_in = bus_client.read(count=max_stream_len+extra_events)

    # Assert that the length of received events is equal to max_stream_len
    assert len(events_in) == max_stream_len

    # Assert that the oldest messages are trimmed
    expected_profiles = set(range(extra_events, max_stream_len + extra_events))
    received_profiles = {event.profile_id for event in events_in}
    assert expected_profiles == received_profiles
