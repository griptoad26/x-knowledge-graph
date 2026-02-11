# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for X Knowledge Graph v0.3.10
Creates standalone .exe with everything bundled
"""

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('frontend', 'frontend'),
        ('core', 'core'),
    ],
    hiddenimports=[
        # Flask and extensions
        'flask',
        'flask_cors',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'click',
        'itsdangerous',
        'blinker',
        'flask_compress',
        # NetworkX dependencies
        'networkx',
        'networkx.drawing',
        'networkx.readwrite',
        # Pandas dependencies
        'pandas',
        'pandas._libs',
        'pandas._libs.window',
        'pandas._libs.tslibs',
        # NumPy dependencies
        'numpy',
        'numpy.core._methods',
        'numpy.core.multiarray',
        'numpy.lib.format',
        # Other dependencies
        'json',
        'sqlite3',
        'dataclasses',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'test', 'pytest', 'pydoc', 'doctest', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='XKnowledgeGraph',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
