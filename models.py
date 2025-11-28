import datetime
from typing import TypedDict

from peewee import *
import time

from playhouse.sqlite_ext import JSONField, SqliteExtDatabase


db = SqliteExtDatabase('database.db')

class CONSTS:
    PAUSE_ACTION_ID = 'pause'


class BaseModel(Model):
    class Meta:
        database = db


class Action(BaseModel):
    """
    Любое действие
    """

    title = CharField(unique=True, max_length=50)

    class Meta:
        table_name = 'action'


class Activity(BaseModel):
    """
    Активность / Целевое действие (работа, учёба)
    """

    title = CharField(unique=True, max_length=50)

    class Meta:
        table_name = 'activity'


class ActivityActions(BaseModel):
    """
    Связь активности с остальными действиями.
    Определяет, какими действиями может заниматься пользователем во время выполнения целевого действия.
    """

    activity = ForeignKeyField(Activity, backref='actions')
    action = ForeignKeyField(Action, backref='activities')
    is_target = BooleanField(help_text='Является ли действие целевым для данной активности')

    class Meta:
        table_name = 'activity_actions'
        indexes = (
            (('activity', 'action'), True),  # уникальный индекс
        )


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
    start: int = IntegerField(default=time.time, help_text='Начало работы (таймпстемп)')
    stop: int | None = IntegerField(help_text='Окончание работы (таймпстемп)', null=True)

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
        Action,
        Activity,
        ActivityActions,
        ActivityTrack,
    ])
