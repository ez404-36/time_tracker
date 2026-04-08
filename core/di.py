from dependency_injector import containers, providers
from flet import Page

from apps.app_settings.models import AppSettings
from apps.time_tracker.services.main_tracker import MainTracker
from core.store import SessionStore
from core.system_events.event_bus import EventBus


class _Container(containers.DeclarativeContainer):
    page: Page = providers.Dependency(Page)

    session_store: SessionStore = providers.Singleton(SessionStore)

    event_bus: EventBus = providers.Singleton(EventBus) # Шина событий

    app_settings: AppSettings = providers.Singleton(AppSettings)

    main_tracker: MainTracker = providers.Singleton(MainTracker)


container = _Container()
