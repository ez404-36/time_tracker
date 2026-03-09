"""1754c198-392f-4c2c-afed-7bf7ca324d2d"""

import peewee

CREATE_APP_SETTINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "settings"
(
    "id" INTEGER NOT NULL PRIMARY KEY,
    "client_timezone" VARCHAR(255) NOT NULL,
    "idle_threshold" INTEGER NOT NULL,
    "enable_pomodoro" INTEGER NOT NULL,
    "pomodoro_work_time" INTEGER,
    "pomodoro_rest_time" INTEGER,
    "enable_task_deadline_sound_notifications" INTEGER NOT NULL,
    "task_deadline_sound" VARCHAR(255),
    "enable_idle_start_sound_notifications" INTEGER NOT NULL,
    "idle_start_sound" VARCHAR(255)
)
"""

CREATE_EVENT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "event"
(
    "id" INTEGER NOT NULL PRIMARY KEY,
    "ts" DATETIME NOT NULL,
    "type" INTEGER NOT NULL,
    "initiator" INTEGER NOT NULL,
    "data" JSON NOT NULL
)
"""

CREATE_IDLE_SESSION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "idle_session"
(
    "id" INTEGER NOT NULL PRIMARY KEY,
    "start_ts" DATETIME NOT NULL,
    "end_ts" DATETIME,
    "duration" INTEGER NOT NULL
)
"""

CREATE_TASK_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "task"
(
    "id" INTEGER NOT NULL PRIMARY KEY,
    "title" VARCHAR(50) NOT NULL,
    "description" TEXT,
    "created_at" DATETIME NOT NULL,
    "parent_id" INTEGER,
    "deadline_date" DATE,
    "deadline_time" TIME,
    "is_done" INTEGER NOT NULL,
    "is_expired" INTEGER NOT NULL,
    FOREIGN KEY ("parent_id") REFERENCES "task" ("id")
)
"""

CREATE_INDEX_TASK_PARENT_ID = """
CREATE INDEX IF NOT EXISTS "task_parent_id" ON "task" ("parent_id")
"""

CREATE_WINDOW_SESSION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "window_session"
(
    "id" INTEGER NOT NULL PRIMARY KEY,
    "start_ts" DATETIME NOT NULL,
    "end_ts" DATETIME,
    "duration" INTEGER NOT NULL,
    "executable_name" VARCHAR(255) NOT NULL,
    "executable_path" VARCHAR(255),
    "window_title" VARCHAR(255)
)
"""

def migrate(db: peewee.Database):
    db.execute_sql(CREATE_APP_SETTINGS_TABLE_SQL)
    db.execute_sql(CREATE_EVENT_TABLE_SQL)
    db.execute_sql(CREATE_IDLE_SESSION_TABLE_SQL)
    db.execute_sql(CREATE_TASK_TABLE_SQL)
    db.execute_sql(CREATE_INDEX_TASK_PARENT_ID)
    db.execute_sql(CREATE_WINDOW_SESSION_TABLE_SQL)


def downgrade(db: peewee.Database):
    db.execute_sql("""DROP TABLE IF EXISTS window_session""")
    db.execute_sql("""DROP TABLE IF EXISTS task""")
    db.execute_sql("""DROP TABLE IF EXISTS idle_session""")
    db.execute_sql("""DROP TABLE IF EXISTS event""")
    db.execute_sql("""DROP TABLE IF EXISTS settings""")
