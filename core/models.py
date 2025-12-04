from peewee import Model

from playhouse.sqlite_ext import SqliteExtDatabase


db = SqliteExtDatabase('database.db')


class BaseModel(Model):
    class Meta:
        database = db
