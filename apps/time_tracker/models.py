__all__ = (
    'Activity',
    'ActivityTrackActionTrackData',
    'ActivityDayTrack',
    'AppAction',
    'ActivityAppActions',
)

import datetime
from typing import TYPE_CHECKING, TypedDict

from peewee import *
import time

from playhouse.sqlite_ext import JSONField

from core.models import BaseModel


class Activity(BaseModel):
    """
    Активность / Целевое действие (работа, учёба)
    """

    title = CharField(unique=True, max_length=50)
    work_time = SmallIntegerField(help_text='Время непрерывной работы (минут)', null=True)
    rest_time = SmallIntegerField(help_text='Время отдыха (минут)', null=True)

    class Meta:
        table_name = 'activity'

    if TYPE_CHECKING:
        title: str
        work_time: int | None
        rest_time: int | None


class AppAction(BaseModel):
    """
    Действие в каком-либо приложении на ПК
    """

    app_name = CharField(help_text='Название программы')
    app_path = CharField(help_text='Путь до исполняемого файла')
    app_internal_path = CharField(help_text='Путь внутри приложения (например, вкладка браузера)', null=True)

    class Meta:
        table_name = 'app_action'
        indexes = (
            (('app_path', 'app_internal_path'), True),
        )


class ActivityAppActions(BaseModel):
    """
    m2m связь между активностью и действием на ПК
    """

    activity = ForeignKeyField(Activity, backref='app_actions')
    app_action = ForeignKeyField(AppAction, backref='activities')
    is_useful = BooleanField(help_text='Полезное ли действие', null=True)

    class Meta:
        table_name = 'activity_app_actions'


class ActivityTrackActionTrackData(TypedDict):
    application_id: str | int
    timestamp: int


class ActivityDayTrack(BaseModel):
    """
    Отслеживание активности за день.
    Объект создаётся в момент начала работы каждый день.
    """

    activity: Activity = ForeignKeyField(Activity, backref='day_track')
    date: datetime.date = DateField(default=datetime.date.today, help_text='День')

    """
    Здесь будет храниться время каждого фактического действия.
    Представляет собой список объектов { application_id: ID окна | pause, timestamp: Текущий таймпстемп }
    """
    time_track: list[ActivityTrackActionTrackData] = JSONField(default=list, help_text='Затраченное время')

    class Meta:
        table_name = 'activity_day_track'

    def change_action(self, application_id: int | str):
        """Смена действия (фокус на другом приложении)"""

        self.time_track.append(
            ActivityTrackActionTrackData(
                application_id=application_id,
                timestamp=int(time.time()),
            )
        )
        self.save(only=['time_track'])
