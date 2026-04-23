"""e6cc429e-bb3a-45e3-9f1d-28bb39760c4b"""

import peewee
from playhouse.migrate import migrate as apply
from playhouse.sqlite_ext import JSONField
from core.database import migrator


"""
Example using migrator:
- apply(migrator.add_column('table_name', 'field_name', peewee.CharField()))

Example using native SQL:
- db.execute_sql('ALTER TABLE "table_name" RENAME COLUMN $old_name to $new_name')
"""


def migrate(db: peewee.Database):
    apply(migrator.add_column('settings', 'ui_settings', JSONField(default=dict)))
    

def downgrade(db: peewee.Database):
    apply(migrator.drop_column('settings', 'ui_settings'))
