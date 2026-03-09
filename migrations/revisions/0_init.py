"""fbef9a86-957d-4c5e-a941-a26fa1739331"""

from migrations.migration_applier import OneMigrationApplier

CREATE_MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "migrations"
(
    "id" INTEGER NOT NULL PRIMARY KEY,
    "migration_uuid" UUID NOT NULL,
    "index" INTEGER NOT NULL
)
"""


def migrate(db):
    db.execute_sql(CREATE_MIGRATIONS_TABLE_SQL)


def downgrade(db):
    db.execute_sql("""DROP TABLE IF EXISTS migrations""")


if __name__ == '__main__':
    OneMigrationApplier(__file__).migrate()