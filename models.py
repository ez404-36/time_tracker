import datetime
from typing import TypedDict

from peewee import *
import time

from playhouse.sqlite_ext import JSONField, SqliteExtDatabase


db = SqliteExtDatabase('database.db')

class CONSTS:
    PAUSE_ACTION_ID = 'pause'
    STOP_ACTION_ID = 'stop'


class BaseModel(Model):
    class Meta:
        database = db


class Activity(BaseModel):
    """
    Активность / Целевое действие (работа, учёба)
    """

    title = CharField(unique=True, max_length=50)

    class Meta:
        table_name = 'activity'


class Action(BaseModel):
    """
    Действие, которое может быть выполнено во время активности
    """

    activity = ForeignKeyField(Activity, backref='actions')
    title = CharField(max_length=50)
    is_target = BooleanField(help_text='Является ли действие целевым для данной активности')
    is_useful = BooleanField(help_text='Является ли действие полезным для данной активности')

    class Meta:
        table_name = 'action'


class ActivityTrackActionTrackData(TypedDict):
    action_id: str | int
    timestamp: int


class ActivityTrack(BaseModel):
    """
    Отслеживание активности за день.
    Объект создаётся в момент начала работы каждый день.
    """

    activity = ForeignKeyField(Activity, backref='activity_track')
    date: datetime.date = DateField(default=datetime.date.today, help_text='День')

    """
    Здесь будет храниться время каждого фактического действия.
    Представляет собой список объектов { action_id: ID действия | pause, timestamp: Текущий таймпстемп }
    """
    time_track: list[ActivityTrackActionTrackData] = JSONField(default=list, help_text='Затраченное время')

    class Meta:
        table_name = 'activity_track'

    def change_action(self, action_id: int | str):
        """Смена действия"""

        self.time_track.append(
            ActivityTrackActionTrackData(
                action_id=action_id,
                timestamp=int(time.time()),
            )
        )
        self.save(only=['time_track'])


if __name__ == '__main__':
    db.create_tables([
        Activity,
        Action,
        ActivityTrack,
    ])
