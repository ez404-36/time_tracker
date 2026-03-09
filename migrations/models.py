from peewee import *

from core.models import BaseModel


class MigrationModel(BaseModel):
    """
    Миграция
    """

    migration_uuid = UUIDField(help_text='ID миграции', index=True)
    index = SmallIntegerField(help_text='Индекс миграции', index=True)

    class Meta:
        table_name = 'migrations'