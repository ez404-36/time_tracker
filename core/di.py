from dependency_injector import containers, providers
from flet import Page

from apps.app_settings.models import AppSettings
from core.store import PersistentStore, SessionStore
from core.system_events.event_bus import EventBus


class _Container(containers.DeclarativeContainer):
    page: Page = providers.Dependency(Page)

    session_store: SessionStore = providers.Singleton(SessionStore)

    persistent_store: PersistentStore = providers.Singleton(PersistentStore)

    event_bus: EventBus = providers.Singleton(EventBus) # Шина событий

    app_settings: AppSettings = providers.Singleton(AppSettings)


container = _Container()
