"""50bf02b8-a24c-400f-85bc-bb836efae6bc"""

import peewee


def migrate(db: peewee.Database):
    sql = """
    ALTER TABLE "event"
        RENAME COLUMN initiator to actor;
    """
    db.execute_sql(sql)
    

def downgrade(db: peewee.Database):
    sql = """
    ALTER TABLE "event"
        RENAME COLUMN actor to initiator;
    """
    db.execute_sql(sql)

