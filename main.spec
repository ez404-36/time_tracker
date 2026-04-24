# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[
    	os.path.abspath('.')  # корень проекта
    ],
    binaries=[],
    datas=[
    	('./apps', './apps'),
    	('./core', './core'),
    	('./media', './media'),
    	('./migrations', './migrations'),
    	('./ui', './ui'),
    	('pyproject.toml', '.'),
    ],
    hiddenimports=[
    	'dependency_injector.errors',
        'dependency_injector.wiring',
    ],
    hookspath=[
        '.',
    ],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
    	'.venv',
    	'build',
    	'dist',
    	'.idea',
    	'.git',
    	'__pycache__',
    	'tests',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TimeTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    windowed=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='./media/assets/icon.ico'
)
