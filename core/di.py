from dependency_injector import containers, providers
from flet import Page

from core.store import Store


class _Container(containers.DeclarativeContainer):
    page: Page = providers.Dependency(Page)

    store: Store = providers.Singleton(Store)


container = _Container()
