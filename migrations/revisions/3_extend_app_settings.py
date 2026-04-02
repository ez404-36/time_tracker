"""55943b05-bb1d-4fa4-97b8-ebb886941497"""

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
    apply(migrator.add_column('settings', 'enable_window_tracking', peewee.BooleanField(help_text='Включить отслеживание активных окон', default=False)))
    apply(migrator.add_column('settings', 'enable_idle_tracking', peewee.BooleanField(help_text='Включить отслеживание бездействия', default=False)))


def downgrade(db: peewee.Database):
    apply(migrator.drop_column('settings', 'enable_window_tracking'))
    apply(migrator.drop_column('settings', 'enable_idle_tracking'))

        