from core.system_events.types import SystemEvent, SystemEventCallback, SystemEventType


class EventBus:
    """
    Шина событий
    """

    def __init__(self):
        self._subscribers: dict[SystemEventType, list[SystemEventCallback]] = {}

    def subscribe(self, event_type: SystemEventType, callback: SystemEventCallback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: SystemEvent):
        event_type = event.type
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(event.data)
