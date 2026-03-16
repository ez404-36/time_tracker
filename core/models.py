from peewee import AutoField, Model

from core.database import db


class BaseModel(Model):
    id: int = AutoField(primary_key=True, index=True)

    class Meta:
        database = db
