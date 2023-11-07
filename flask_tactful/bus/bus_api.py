
from flask_restx import Namespace, Resource, fields, Api
from ..rest import class_to_restplus , allow_cors
from . import TactfulBus

bus_namespace = Namespace('events', "Events")

def publish_bus_apis(api: Api,  bus: TactfulBus):

    expected_events = bus.event_handlers.keys()
    expected_event_fields = dict()
    for event_name in expected_events:
        ev = event_name.split("+")
        expected_event_fields[ev[1]] = fields.String(description=f"Event {ev[1]} from tipic {ev[0]}", example=f"{ev[0]}")

    published_events = bus.published_events
    published_event_fields = dict()
    for event in published_events:
        event_name = event.__class__.__name__
        published_event_model = bus_namespace.model(event_name, class_to_restplus(event))
        published_event_fields[event_name] = fields.Nested(published_event_model, description=f"Event {event_name}")


    expected_events_model = bus_namespace.model('ExpectedEvents', expected_event_fields)

    published_events_model = bus_namespace.model('PublishedEvents', published_event_fields)

    # because these are dynamic, we cannot use them as decorators at the definition of the class
    bus_namespace.marshal_with(expected_events_model)(ExpectedEvents.get)
    bus_namespace.marshal_with(published_events_model)(PublishedEvents.get)

    api.add_namespace(bus_namespace, path="/events")
    

@bus_namespace.route('/expected')
class ExpectedEvents(Resource):
    @allow_cors
    def get(self):
        return 200
    
    @allow_cors
    @bus_namespace.doc(False)
    def options(self):
        return "OK", 200
    

@bus_namespace.route('/published')
class PublishedEvents(Resource):
    @allow_cors
    def get(self):
        return 200
    
    @allow_cors
    @bus_namespace.doc(False)
    def options(self):
        return "OK", 200