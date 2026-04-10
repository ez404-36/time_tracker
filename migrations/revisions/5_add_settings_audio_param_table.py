"""0c59c3dd-c745-4a2d-81a6-4c70d1f0e8a6"""

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
    db.execute_sql(
        """
        CREATE TABLE "settings_audio_param" (
            "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            "disabled" BOOLEAN DEFAULT 0,
            "sound" VARCHAR(255),
            "volume_offset" DECIMAL(3, 1) DEFAULT 0.0
        );
        """
    )
    db.execute_sql(
        """
        ALTER TABLE "settings" ADD COLUMN "task_deadline_sound_config_id" INTEGER;
        """
    )
    db.execute_sql(
        """
        ALTER TABLE "settings"
            ADD COLUMN "idle_sound_config_id" INTEGER;
        """
    )
    db.execute_sql(
        """
        ALTER TABLE "settings"
            ADD COLUMN "pomodoro_sound_config_id" INTEGER;
        """
    )
    db.execute_sql(
        """
        CREATE INDEX "settings_task_deadline_sound_config_id" ON "settings" ("task_deadline_sound_config_id");
        """
    )
    db.execute_sql(
        """
        CREATE INDEX "settings_idle_sound_config_id" ON "settings" ("idle_sound_config_id");
        """
    )
    db.execute_sql(
        """
        CREATE INDEX "settings_pomodoro_sound_config_id" ON "settings" ("pomodoro_sound_config_id");
        """
    )


def downgrade(db: peewee.Database):
    db.execute_sql(
        """
        DROP INDEX "settings_task_deadline_sound_config_id";
        """
    )
    db.execute_sql(
        """
        DROP INDEX "settings_idle_sound_config_id";
        """
    )
    db.execute_sql(
        """
        DROP INDEX "settings_pomodoro_sound_config_id";
        """
    )

    apply(migrator.drop_column('settings', 'task_deadline_sound_config_id'))
    apply(migrator.drop_column('settings', 'idle_sound_config_id'))
    apply(migrator.drop_column('settings', 'pomodoro_sound_config_id'))

    db.execute_sql(
        """
        DROP TABLE settings_audio_param;
        """
    )


