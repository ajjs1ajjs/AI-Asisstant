# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

CURRENT_DIR = Path('.').resolve()

# Find llama_cpp lib path
import llama_cpp
LLAMA_CPP_PATH = Path(llama_cpp.__file__).parent / 'lib'

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

# Collect all llama_cpp data
datas_llama, binaries_llama, hiddenimports_llama = collect_all('llama_cpp')

a = Analysis(
    ['main.py'],
    pathex=[str(CURRENT_DIR)],
    binaries=binaries_llama + [
        (str(LLAMA_CPP_PATH / '*.dll'), 'llama_cpp'),
    ],
    datas=datas_llama + [
        ('.env', '.'),
    ],
    hiddenimports=hiddenimports_llama + [
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'httpx',
        'faiss',
        'numpy',
        'aiofiles',
        'dotenv',
        'requests',
        'psutil',
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
    name='AI_Coding_IDE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
