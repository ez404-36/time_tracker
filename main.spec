import sys
import os

project_root = os.path.dirname(os.path.abspath(__name__))

a = Analysis(
    ['main.py'],
    pathex=[
        project_root,
        os.path.join(project_root, 'apps'),
        os.path.join(project_root, 'core'),
    ],
    binaries=[],
    datas=[
        ('apps/**/*', 'apps/'),
        ('core/**/*', 'core/'),
    ],
    hiddenimports=[
        # Добавьте здесь любые скрытые импорты
        'flet',
        'sqlite3',
        # 'pywin32', # Для Windows
        # 'pywinctl', # Для Linux
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
