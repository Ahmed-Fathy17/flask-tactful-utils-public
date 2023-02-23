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
        bus_url=TEST_REDIS_DB,
        group_name="tests",
        consumer_name="client1"
    )
    return client1

@pytest.fixture()
def bus_same_group_clients(reset_bus):
    return (
        TactfulRedisStreamBus(bus_url=TEST_REDIS_DB, group_name="tests", consumer_name="sender"),
        TactfulRedisStreamBus(bus_url=TEST_REDIS_DB, group_name="tests", consumer_name="client1"),
        TactfulRedisStreamBus(bus_url=TEST_REDIS_DB, group_name="tests", consumer_name="client2"),
        TactfulRedisStreamBus(bus_url=TEST_REDIS_DB, group_name="tests", consumer_name="client3")
    )

@pytest.fixture()
def bus_many_groups_clients(reset_bus):
    return (
        TactfulRedisStreamBus(bus_url=TEST_REDIS_DB, group_name="test_channels", consumer_name="sender"),
        TactfulRedisStreamBus(bus_url=TEST_REDIS_DB, group_name="test_chat", consumer_name="client1"),
        TactfulRedisStreamBus(bus_url=TEST_REDIS_DB, group_name="test_reports", consumer_name="client2"),
        TactfulRedisStreamBus(bus_url=TEST_REDIS_DB, group_name="test_billing", consumer_name="client3")
    )


def test_flask_initilaization():
    app = Flask("test")
    app.config["REDIS_BUS_URL"] = TEST_REDIS_DB
    app.config["REDIS_CONSUMER_GROUP"] = "tests"

    bus = TactfulRedisStreamBus.from_app(app=app)
    assert bus
    assert bus.consumer_name == socket.gethostname()

def test_redis_client(bus_client: TactfulRedisStreamBus):
    bus_client._add_event_handler("unittest:billing", "CreditCardExpired", None)
    bus_client._preapre_streams()
    event_out = Event(topic="unittest:billing", event="CreditCardExpired", profile_id=1)
    bus_client.publish(event_out)
    event_in = bus_client.read(["unittest:billing"])[0]

    assert event_in == event_out

def test_redis_group_loadbalancing(bus_same_group_clients: Tuple[TactfulRedisStreamBus, ...]):
    (sender, client1, client2, client3) = bus_same_group_clients
 
    # recieve events in each client
    client1._add_event_handler("unittest:billing", "CreditCardExpired", None)
    client1._preapre_streams()

    client2._add_event_handler("unittest:billing", "CreditCardExpired", None)
    client2._preapre_streams()

    client3._add_event_handler("unittest:billing", "CreditCardExpired", None)
    client3._preapre_streams()

    # send some events
    events_out = [
        Event(topic="unittest:billing", event="CreditCardExpired",  profile_id=1),
        Event(topic="unittest:billing", event="CreditCardExpired",  profile_id=1),
        Event(topic="unittest:billing", event="CreditCardExpired",  profile_id=1),
    ]
    [sender.publish(ev) for ev in events_out]


    events_in1 = client1.read(["unittest:billing"])
    events_in2 = client2.read(["unittest:billing"])
    events_in3 = client3.read(["unittest:billing"])

    assert len(events_in1) > 0
    assert len(events_in2) > 0 
    assert len(events_in3) > 0
    assert events_in1 != events_in2
    assert events_in2 != events_in3



def test_redis_group_fanout(bus_many_groups_clients: Tuple[TactfulRedisStreamBus, ...]):
    (sender, client1, client2, client3) = bus_many_groups_clients
 
    # recieve events in each client
    client1._add_event_handler("unittest:billing", "CreditCardExpired", None)
    client1._preapre_streams()

    client2._add_event_handler("unittest:billing", "CreditCardExpired", None)
    client2._preapre_streams()

    client3._add_event_handler("unittest:billing", "CreditCardExpired", None)
    client3._preapre_streams()

    # send some events
    events_out = [
        Event(topic="unittest:billing", event="CreditCardExpired",  profile_id=1),
        Event(topic="unittest:billing", event="CreditCardExpired",  profile_id=1),
        Event(topic="unittest:billing", event="CreditCardExpired",  profile_id=1),
    ]
    [sender.publish(ev) for ev in events_out]


    events_in1 = client1.read(["unittest:billing"])
    events_in2 = client2.read(["unittest:billing"])
    events_in3 = client3.read(["unittest:billing"])

    assert len(events_in1) > 0
    assert len(events_in2) > 0 
    assert len(events_in3) > 0
    assert events_in1 == events_in2 == events_in3
