import importlib
import uuid
from pathlib import Path
from typing import Callable, Generator

from peewee import OperationalError, Database

from core.database import db
from core.consts import MIGRATIONS_DIR
from migrations.models import MigrationModel


class MigrationsApplier:
    def __init__(self):
        self._root = MIGRATIONS_DIR

        try:
            self._applied_migrations: list[MigrationModel] = list(
                MigrationModel.select()
                .order_by(
                    MigrationModel.index.desc(),
                )
            )
        except OperationalError:
            # нулевая миграция, таблица MigrationModel ещё не создана
            self._applied_migrations = []

        self._applied_migrations_map: dict[int, MigrationModel] = {
            it.index: it for it in self._applied_migrations
        }

    @db.atomic()
    def migrate(self, _index: int | None):
        for file in self.traverse():
            file_index = self._get_file_index(file)

            assert file_index is not None

            index_condition = _index is None or file_index <= _index
            applied_condition = file_index not in self._applied_migrations_map

            if applied_condition and index_condition:
                OneMigrationApplier(file).migrate()

    @db.atomic()
    def downgrade(self, _index: int):
        file_index_map: dict[int, Path] = {}
        for file in self.traverse():
            file_index = self._get_file_index(file)
            file_index_map[file_index] = file


        def downgrade_migration(_applied_migration: MigrationModel):
            nonlocal file_index_map
            _file_path = file_index_map.get(_applied_migration.index)

            assert _file_path is not None

            OneMigrationApplier(_file_path).downgrade()


        if _index < 0:
            rest_downgrade_migrations = abs(_index)
            for applied_migration in self._applied_migrations:
                if rest_downgrade_migrations == 0:
                    break

                downgrade_migration(applied_migration)
                rest_downgrade_migrations -= 1

        else:
            for applied_migration in self._applied_migrations:
                if applied_migration.index < _index:
                    break

                downgrade_migration(applied_migration)

    def create_new(self, title: str):
        EXAMPLE = '''"""{migration_uuid}"""

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
    pass
    # paste your migration code here
    

def downgrade(db: peewee.Database):
    pass
    # paste your revert migration code here

        '''

        if self._applied_migrations:
            new_migration_index = self._applied_migrations[0].index + 1
        else:
            new_migration_index = 0

        file_name = f'{new_migration_index}_{title}.py'

        with open(Path(MIGRATIONS_DIR / file_name), 'w') as f_obj:
            f_obj.write(EXAMPLE.format(migration_uuid=uuid.uuid4()))

    def traverse(self) -> Generator[Path]:
        for file in Path(self._root).rglob('*.py'):
            if file.stem != '__init__':
                yield file

    @staticmethod
    def _get_file_index(file: Path) -> int | None:
        file_name_chunks = file.stem.split('_')

        if len(file_name_chunks) < 2:
            return None

        return int(file_name_chunks[0])


class OneMigrationApplier:
    """
    Применяет/отменяет миграции одного конкретного файла
    """

    def __init__(self, file_path: str | Path):
        self.file_path = file_path

        self._module = None
        self._migration_uuid: str | None = None
        self._migration_index: int | None = None

    @db.atomic()
    def migrate(self):
        self.prepare()

        assert self._migration_index is not None

        if self._migration_index > 0:
            migration_row = (
                MigrationModel.select()
                .where(
                    MigrationModel.migration_uuid == self._migration_uuid,
                    MigrationModel.index == self._migration_index,
                )
                .first()
            )
            assert migration_row is None, f'Миграция {self._migration_uuid} уже применена'
        else:
            # Применение нулевой миграции означает создание таблицы migrations
            pass

        migrate_method: Callable[[Database], None] = getattr(self._module, 'migrate')
        migrate_method(db)

        MigrationModel.create(
            migration_uuid=self._migration_uuid,
            index=self._migration_index,
        )

    @db.atomic()
    def downgrade(self):
        self.prepare()

        assert self._migration_index is not None

        migration_row = (
            MigrationModel.select()
            .where(
                MigrationModel.migration_uuid == self._migration_uuid,
                MigrationModel.index == self._migration_index,
            )
            .first()
        )

        assert migration_row is not None, f'Миграция {self._migration_uuid} не применена'

        downgrade_method: Callable[[Database], None] = getattr(self._module, 'downgrade')
        downgrade_method(db)

        if self._migration_index > 0:
            migration_row.delete_instance()

    def prepare(self):
        self._module = importlib.import_module(f'migrations.revisions.{Path(self.file_path).stem}')
        self._migration_uuid = self._module.__doc__
        self._migration_index = int(Path(self.file_path).stem.split('_')[0])
