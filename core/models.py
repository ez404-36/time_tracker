from peewee import AutoField, Model
from playhouse.sqlite_ext import SqliteExtDatabase

from core.consts import BASE_DIR

db = SqliteExtDatabase(BASE_DIR / 'database.db')


class BaseModel(Model):
    id: int = AutoField(primary_key=True, index=True)

    class Meta:
        database = db
