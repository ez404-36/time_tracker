import argparse
import textwrap

from migrations.migration_applier import MigrationsApplier

parser = argparse.ArgumentParser(
    epilog='''
    Примеры:
    - Создать миграцию: python manage.py new_migration create_some_table
    - Применить все миграции: python manage.py migrate
    - Применить миграции вплоть до 5-ой включительно: python manage.py migrate 5
    - Отменить все миграции вплоть до 2-ой включительно: python manage.py downgrade 2
    - Отменить последние 2 миграции: python manage.py downgrade -2
    ''',
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

migrate_parser = subparsers.add_parser('migrate', help='Применение миграций')
migrate_parser.add_argument('index', type=int, nargs='*', help='Индекс миграции, до которой необходимо применить изменения (включительно)')

downgrade_parser = subparsers.add_parser(
    'downgrade', help='Отмена миграций',
)
downgrade_parser.add_argument(
    'index', type=int, nargs=1,
    help=textwrap.dedent('''
    Индекс миграции, до которой необходимо отменить изменения (включительно).
    ''')
)

new_migration_parser = subparsers.add_parser('new_migration', help='Создать новую миграцию')
new_migration_parser.add_argument('title', type=str, nargs='*', help='Название миграции (англ. язык)')


def migrate(_index: int | None):
    applier = MigrationsApplier()
    applier.migrate(_index)


def downgrade(_index: int):
    applier = MigrationsApplier()
    applier.downgrade(_index)


def create_new_migration(title: str):
    applier = MigrationsApplier()
    applier.create_new(title)


def main():
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'migrate':
        if args.index:
            index = args.index[0]
        else:
            index = None
        migrate(index)
    elif args.command == 'downgrade':
        downgrade(args.index[0])
    elif args.command == 'new_migration':
        if title := args.title:
            title = title[0]
        else:
            title = ''

        create_new_migration(title)


if __name__ == '__main__':
    main()
