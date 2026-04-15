from cx_Freeze import Executable, setup

resources = [
    ('media/', 'media/'),
]

build_exe_options = {
    "excludes": ["ty"],
    "includes": [
        "pywinctl",
        "audioop",
        "dependency_injector.errors",
        "dependency_injector.wiring",
    ],
}

executable = Executable(
    'main.py',
    target_name="TimeTracker",
    base=None,
    icon='./media/assets/icon.png',  # TODO
)

setup(
    name="TimeTracker",
    version="0.2",
    description="TimeTracker — ваш личный помощник в работе без лишнего шума",
    options={"build_exe": build_exe_options},
    executables=[executable],
)
