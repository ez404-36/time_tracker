from playhouse.migrate import SqliteMigrator, migrate

from apps.time_tracker.models import *
from apps.to_do.models import *


def drop_tables(_db):
    _db.drop_tables([
        PomodoroTimer,
        Event,
        IdleSession,
        WindowSession,
        ToDo,
    ])


def create_tables(_db):
    _db.create_tables([
        PomodoroTimer,
        Event,
        IdleSession,
        WindowSession,
        ToDo,
    ])


def run_migration(_db):
    migrator = SqliteMigrator(_db)

    # Код для миграций
    migrate(

    )


if __name__ == '__main__':
    from core.models import db
    create_tables(db)
