# -*- mode: python ; coding: utf-8 -*-
"""
X Knowledge Graph v0.4.27 - PyInstaller Spec File
Directory-based build for better user experience (no temp extraction)
"""

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend', 'frontend'),
        ('core', 'core'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'networkx',
        'networkx.drawing',
        'pandas',
        'numpy',
        'tkinter',
        'tkinter.filedialog',
        'threading',
        'socket',
        'webbrowser',
        'argparse',
        'json',
        'dataclasses',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.ttk',
        'test',
        'tests',
        'pytest',
        '__pycache__',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='XKnowledgeGraph'
)
