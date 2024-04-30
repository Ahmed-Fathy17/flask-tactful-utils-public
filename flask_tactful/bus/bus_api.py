
from flask_restx import Namespace, Resource, fields, Api
from typing import List, Any, Dict

from ..ddd import Event
from ..rest import class_to_restplus

bus_namespace = Namespace('Events', "Events")

def publish_bus_apis(api: Api, expected_events: Dict[str, str], published_events: List[Event]):
    expected_event_fields = dict()
    for (event_name, topic) in expected_events.items():
        expected_event_fields[event_name] = fields.String(description=f"Event {event_name} from topic {topic}", example=f"{topic}")

    published_event_fields = dict()
    for event in published_events:
        
        event_name = event.__name__ # type: ignore[attr-defined]
        published_event_model = bus_namespace.model(event_name, class_to_restplus(event))
        published_event_fields[event_name] = fields.Nested(published_event_model, description=f"Event {event_name}")


    expected_events_model = bus_namespace.model('ExpectedEvents', expected_event_fields)

    published_events_model = bus_namespace.model('PublishedEvents', published_event_fields)

    # because these are dynamic, we cannot use them as decorators at the definition of the class
    bus_namespace.marshal_with(expected_events_model)(ExpectedEvents.get)
    bus_namespace.marshal_with(published_events_model)(PublishedEvents.get)

    ExpectedEvents.reply_with = expected_events;
    PublishedEvents.reply_with = [ ev.__name__ for ev in published_events ]; # type: ignore[attr-defined]

    api.add_namespace(bus_namespace, path="/events")
    

@bus_namespace.route('/expected')
class ExpectedEvents(Resource):
    reply_with: Any = None
    
    def get(self):
        return ExpectedEvents.reply_with, 200


@bus_namespace.route('/published')
class PublishedEvents(Resource):
    reply_with: Any = None

    def get(self):
        return PublishedEvents.reply_with, 200
