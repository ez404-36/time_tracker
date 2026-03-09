from playhouse.migrate import SqliteMigrator
from playhouse.sqlite_ext import SqliteExtDatabase

from core.settings import DB_URL

db = SqliteExtDatabase(DB_URL)
migrator = SqliteMigrator(db)