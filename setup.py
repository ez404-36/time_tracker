from cx_Freeze import Executable, setup

resources = [
    ('./', './'),
]

build_exe_options = {
    "excludes": [
        "ty",
    ],
    "includes": [
        "audioop",
        "dependency_injector.errors",
        "dependency_injector.wiring",
    ],
}

executable = Executable(
    script='main.py',
    target_name="TimeTracker",
    base=None,
    icon='./media/assets/icon.png',  # TODO
)

setup(
    name="TimeTracker",
    version="0.0.3",
    description="TimeTracker — ваш личный помощник в работе без лишнего шума",
    options={"build_exe": build_exe_options},
    executables=[executable],
)
