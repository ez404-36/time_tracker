from dependency_injector import containers, providers
from flet import Page

from apps.app_settings.models import AppSettings
from core.store import Store


class _Container(containers.DeclarativeContainer):
    page: Page = providers.Dependency(Page)

    store: Store = providers.Singleton(Store)

    app_settings: AppSettings = providers.Singleton(AppSettings)


container = _Container()
