from playhouse.migrate import SqliteMigrator, migrate

from apps.time_tracker.models import *
from apps.to_do.models import *
from core.models import db


def drop_tables():
    db.drop_tables([
        PomodoroTimer,
        Event,
        IdleSession,
        WindowSession,
        # ToDo,
    ])


def create_tables():
    db.create_tables([
        PomodoroTimer,
        Event,
        IdleSession,
        WindowSession,
        # ToDo,
    ])


def run_migration():
    migrator = SqliteMigrator(db)

    # Код для миграций
    migrate(

    )


if __name__ == '__main__':
    create_tables()
