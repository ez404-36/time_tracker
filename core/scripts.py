from apps.time_tracker.models import Action, Activity, ActivityTrack
from core.models import db


def drop_tables():
    db.drop_tables([
        Activity,
        Action,
        ActivityTrack,
    ])


def create_tables():
    db.create_tables([
        Activity,
        Action,
        ActivityTrack,
    ])


def run_migration():
    migrator = SqliteMigrator(db)

    # Код для миграций
    migrate(

    )
