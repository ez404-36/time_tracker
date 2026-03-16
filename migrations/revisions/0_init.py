"""fbef9a86-957d-4c5e-a941-a26fa1739331"""

import peewee


CREATE_MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "migrations"
(
    "id" INTEGER NOT NULL PRIMARY KEY,
    "migration_uuid" UUID NOT NULL,
    "index" INTEGER NOT NULL
)
"""


def migrate(db: peewee.Database):
    db.execute_sql(CREATE_MIGRATIONS_TABLE_SQL)


def downgrade(db: peewee.Database):
    db.execute_sql("""DROP TABLE IF EXISTS migrations""")
