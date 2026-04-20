import sys
import os

project_root = os.path.dirname(os.path.abspath(__name__))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
    	('./', './'),
    ],
    hiddenimports=[
        # Добавьте здесь любые скрытые импорты
        'flet',
        'sqlite3',
        'dependency_injector.errors',
        'dependency_injector.wiring',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
    	'.venv',
    	'__pycache__',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TimeTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Установите True если нужно видеть консоль
    windowed=True,  # Для GUI приложений (скрывает окно консоли)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TimeTracker'
)
