"""e15dcc82-65d8-4fad-9f70-b1cb020c32b0"""

import peewee
from playhouse.migrate import migrate as apply
from core.database import migrator


"""
Example using migrator:
- apply(migrator.add_column('table_name', 'field_name', peewee.CharField()))

Example using native SQL:
- db.execute_sql('ALTER TABLE "table_name" RENAME COLUMN $old_name to $new_name')
"""


def migrate(db: peewee.Database):
    apply(migrator.add_column('settings', 'enable_pomodoro_sound_notifications', peewee.BooleanField(default=False)))
    apply(migrator.add_column('settings', 'pomodoro_sound', peewee.CharField(null=True, max_length=255)))


def downgrade(db: peewee.Database):
    apply(migrator.drop_column('settings', 'enable_pomodoro_sound_notifications'))
    apply(migrator.drop_column('settings', 'pomodoro_sound'))
