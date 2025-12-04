from peewee import Model

from playhouse.sqlite_ext import SqliteExtDatabase

from core.consts import BASE_DIR

db = SqliteExtDatabase(BASE_DIR / 'database.db')


class BaseModel(Model):
    class Meta:
        database = db
