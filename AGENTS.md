# AGENTS.md

TimeTracker — desktop time/activity tracker built with **Flet 0.82**, **peewee** (SQLite),
**dependency-injector**, Python **3.13+**. Package manager: **uv**.

## Commands

```bash
uv sync                          # install deps (creates .venv)
source .venv/bin/activate        # activate before any python command
python main.py                   # run the app
python manage.py migrate         # apply all migrations
python manage.py migrate 5       # apply up to revision 5 (inclusive)
python manage.py downgrade 2     # revert down to revision 2 (inclusive)
python manage.py downgrade -2    # revert last 2 migrations
python manage.py new_migration create_some_table   # scaffold migrations/revisions/N_title.py
```

### Type check

```bash
ty check                         # config in ty.toml; checks apps/, core/, migrations/, ui/
```

`ty check` currently reports ~39 pre-existing diagnostics (mostly peewee descriptor typing).
Do not "fix" them with `# type: ignore` or by widening types — compare the diagnostic count
before and after your change and only ensure you add none.

### Tests

`unittest` only — there is **no pytest** in this project. Tests live in `tests/`.

```bash
python -m unittest discover tests -v      # all tests
python -m unittest tests.test_github_releases_parser -v            # single module
python -m unittest tests.test_github_releases_parser.TestGitHubReleaseParser -v   # single class
python -m unittest tests.test_github_releases_parser.TestGitHubReleaseParser.test_network_failure   # single test
```

Async tests use `unittest.IsolatedAsyncioTestCase` + `unittest.mock.AsyncMock`/`patch`.

### Build (only when explicitly asked)

```bash
pyinstaller main.spec            # single-file executable
python setup.py build            # cx_Freeze build
```

## Architecture

- `main.py` — entrypoint; wires the DI container, runs `migrate(None)`, starts `ft.run`.
- `core/` — infrastructure: `di.py` (container), `database.py` (peewee `db`, `migrator`),
  `models.py` (`BaseModel`), `store.py` (`SessionStore`), `system_events/` (event bus + typed events),
  `consts.py`, `settings.py`, `mixins/`, `utils/`.
- `apps/<domain>/` — feature modules: `models.py`, `services/`, `controls/` (Flet UI), `subscribers.py`.
  Domains: `app_settings`, `events`, `notifications`, `tasks`, `time_tracker`.
- `ui/` — reusable presentation layer: `ui/base/` (generic components, styles, mixins),
  `ui/components/`, `ui/consts.py` (`Colors`, `Icons`, `FontSize`, `FontWeight`), `ui/utils.py`.
- `migrations/revisions/` — numbered peewee migrations. `scripts/` — standalone helpers.

**Event bus is the backbone.** Services publish `SystemEvent(type=..., data=...)`;
subscribers (`apps/*/subscribers.py`) and UI controls call `event_bus.subscribe(<type>, callback)`
in their `__init__`. Never call another domain's UI directly — publish an event.

**Dependency access**: always `from core.di import container` then `container.event_bus`,
`container.app_settings`, `container.session_store`, `container.page`, `container.main_tracker`,
`container.ui_settings`. Do not instantiate singletons yourself.

## Code style

### Imports
- Order: stdlib → third-party → first-party (`apps`, `core`, `ui`, `scripts`), blank line between groups.
- Absolute imports from the project root. Relative imports only inside a tightly coupled package
  (e.g. `apps/time_tracker/services/main_tracker.py` imports `.idle_tracker`).
- Import the module, not the symbol, when a module holds many event dataclasses:
  `from core.system_events import types as system_event_type`.
- `from peewee import *` is the established convention **in `models.py` files only**; elsewhere import explicitly.
- Break import cycles with `if TYPE_CHECKING:` + quoted annotations, or a function-local import
  (see `main()` in `main.py`, `refresh_tasks_tab` in `apps/tasks/helpers.py`).
- Public API of a model module is declared via `__all__ = ('Task',)` at the top of the file.

### Formatting
- 4 spaces, single quotes `'...'` for strings (double quotes only in `scripts/` and tests).
- No hard line limit; long lines (~120+) are acceptable and common.
- Two blank lines between top-level definitions, one between methods.
- Group related model fields with `# region Название` / `# endregion` comments.

### Naming
- `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` module constants.
- Private attributes/methods prefixed `_` (`self._event_bus`, `def _on_click`).
- Unused callback params prefixed `_` (`def on_change_settings(_data: ...)`).
- Event handlers: `on_<domain>_<action>` for subscribers, `_on_<widget_event>` for internal UI handlers.
- Flet control classes end in `Button`, `Modal`, `Form`, `View`, `Control`, `Tab`, or `List`.
- Event type strings are dotted `'<domain>.<action>'` and must be added to the
  `SystemEventType` `Literal` in `core/system_events/types.py`.

### Types
- Annotate function params and return types. Use `X | None`, `list[X]`, `dict[K, V]` (PEP 604/585) —
  not `Optional`/`List`/`Dict`.
- Event payloads are `@dataclass`es in `core/system_events/types.py`, added to the `SystemEventData` union.
- Cross-platform contracts use `abc.ABC` + `@abc.abstractmethod` (`window_control/abstract.py`);
  structural UI contracts use `typing.Protocol` (`ui/base/components/mixins.py`).
- Peewee model fields carry an explicit annotation when the Python type matters:
  `title: str = CharField(max_length=50, help_text='Название задачи')`.
- `Literal` for closed string sets (`Theme`, `AvailableOS`, `PomodoroTimerStatus`, `SystemEventType`).

### Docstrings & comments
- Class/module docstrings are written **in Russian**, triple-quoted, describing responsibility.
  User-facing strings (labels, tooltips, snackbars, errors) are Russian too.
- Do not add inline comments unless the logic is genuinely non-obvious.

### Error handling
- Domain errors: define a module-level `Exception` subclass (`GitHubReleaseError`) and raise it
  with a descriptive Russian message; never let library exceptions leak across layers.
- Recoverable runtime failures publish `SystemEvent(type='error.system' | 'error.wrong_config' |
  'error.file_not_found', data=SystemEventAppError(...))` — the subscribers persist an `Event`
  row, log via `logging.getLogger(__name__)`, and show a snackbar.
- `EventBus.publish` already wraps every callback in try/except and republishes as `error.system`;
  do not add another blanket try/except inside a subscriber.
- Use `assert` only for migration invariants (`migrations/migration_applier.py`), never for user input.
- Never write a bare `except: pass`. Trace why the failure occurs and handle it at its origin.

### Database
- All models inherit `core.models.BaseModel` (auto `id`, bound to `db`); set `class Meta: table_name = '...'`.
- Every schema change needs a migration created via `python manage.py new_migration <title>` with both
  `migrate(db)` and `downgrade(db)` implemented. Never edit an already-applied revision.
- Partial saves use `save(only=['field'])`. Migrations run automatically on app start.

### UI (Flet)
- Subclass Flet controls (`ft.IconButton`, `ft.TextButton`, `ft.Control`) and configure in
  `__init__` or `build()`; mix in `ShowHideMixin` for `show()`/`hide()`.
- Use `ui.consts.Colors` / `Icons` / `FontSize` / `FontWeight` — never raw `ft.Colors.*` in `apps/`.
- Controls that must be reachable from elsewhere extend `SessionStoredComponent` and are fetched
  via `container.session_store.get('<ClassName>')`.
- Call `self.update()` after mutating a mounted control's state.

## Notes

- No Cursor rules (`.cursor/rules/`, `.cursorrules`) or Copilot instructions exist in this repo.
- No linter/formatter is configured — match surrounding code manually.
- Never commit or stage changes unless explicitly asked.
