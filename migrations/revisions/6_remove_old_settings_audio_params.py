"""cd22c31f-768e-45ed-9e48-453f9a5fa0ed"""

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
    apply(migrator.drop_column('settings', 'enable_task_deadline_sound_notifications'))
    apply(migrator.drop_column('settings', 'task_deadline_sound'))
    apply(migrator.drop_column('settings', 'enable_idle_start_sound_notifications'))
    apply(migrator.drop_column('settings', 'idle_start_sound'))
    apply(migrator.drop_column('settings', 'enable_pomodoro_sound_notifications'))
    apply(migrator.drop_column('settings', 'pomodoro_sound'))


def downgrade(db: peewee.Database):
    pass
    # paste your revert migration code here

