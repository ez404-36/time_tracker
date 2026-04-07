import asyncio
import inspect

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
                callback_signature = inspect.signature(callback)
                params_len = len(callback_signature.parameters)
                if params_len == 0:
                    result = callback()
                else:
                    result = callback(event.data)

                if inspect.isawaitable(result):
                    asyncio.get_event_loop().create_task(result)
