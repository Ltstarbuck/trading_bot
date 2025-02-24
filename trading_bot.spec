# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Add all config files
config_files = [
    ('app/config/*.yaml', 'app/config'),
    ('LICENSE', '.'),
    ('README.md', '.'),
]

# Add all necessary Qt files for the GUI
added_files = [
    ('app/config', 'app/config'),
    ('app/core/gui/components/*.py', 'app/core/gui/components'),
]

a = Analysis(
    ['run_bot.py'],
    pathex=[],
    binaries=[],
    datas=config_files + added_files,
    hiddenimports=[
        'PyQt5',
        'ccxt',
        'pandas',
        'numpy',
        'plotly',
        'yaml',
        'sqlalchemy',
        'loguru',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TradingBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/resources/icon.ico',
)
