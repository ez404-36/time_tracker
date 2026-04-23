from playhouse.migrate import SqliteMigrator
from playhouse.sqlite_ext import SqliteExtDatabase

from core.consts import DB_URL

db = SqliteExtDatabase(DB_URL)
migrator = SqliteMigrator(db)
