# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

CURRENT_DIR = Path('.').resolve()

# Find llama_cpp lib path
try:
    import llama_cpp
    LLAMA_CPP_PATH = Path(llama_cpp.__file__).parent / 'lib'
except ImportError:
    LLAMA_CPP_PATH = None

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

# Collect all llama_cpp data
try:
    datas_llama, binaries_llama, hiddenimports_llama = collect_all('llama_cpp')
except:
    datas_llama, binaries_llama, hiddenimports_llama = [], [], []

# Collect sentence_transformers data
try:
    datas_st, binaries_st, hiddenimports_st = collect_all('sentence_transformers')
except:
    datas_st, binaries_st, hiddenimports_st = [], [], []

# Collect faiss data
try:
    datas_faiss, binaries_faiss, hiddenimports_faiss = collect_all('faiss')
except:
    datas_faiss, binaries_faiss, hiddenimports_faiss = [], [], []

# Collect PySide6 data
try:
    datas_pyside, binaries_pyside, hiddenimports_pyside = collect_all('PySide6')
except:
    datas_pyside, binaries_pyside, hiddenimports_pyside = [], [], []

# Local modules - explicitly add project files
local_modules = [
    'context_engine',
    'local_engine',
    'model_manager',
    'settings',
    'settings_dialog',
    'git_integration',
    'git_dialog',
    'model_benchmark',
    'orchestrator',
    'agent_tools',
    'autocomplete',
]

a = Analysis(
    ['main.py'],
    pathex=[str(CURRENT_DIR)],
    binaries=(binaries_llama or []) + (binaries_st or []) + (binaries_faiss or []) + (binaries_pyside or []),
    datas=(datas_llama or []) + (datas_st or []) + (datas_faiss or []) + (datas_pyside or []) + [
        ('.env.example', '.'),
        ('icon.ico', '.'),
    ] + [(f'{mod}.py', '.') for mod in local_modules],
    hiddenimports=(hiddenimports_llama or []) + (hiddenimports_st or []) + (hiddenimports_faiss or []) + (hiddenimports_pyside or []) + [
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'PySide6.QtNetwork',
        'PySide6.QtPrintSupport',
        'httpx',
        'faiss',
        'numpy',
        'aiofiles',
        'dotenv',
        'requests',
        'psutil',
        'sentence_transformers',
        'transformers',
        'torch',
        'llama_cpp',
        'llama_cpp.llama',
        'llama_cpp.llama_grammar',
        'llama_cpp.llama_types',
        'llama_cpp.llama_cpp',
        'git_integration',
        'git_dialog',
        'settings',
        'settings_dialog',
        'model_benchmark',
        'context_engine',
        'local_engine',
        'model_manager',
        'orchestrator',
        'agent_tools',
        'autocomplete',
        'typing_extensions',
        'PIL',
        'PIL.Image',
        'certifi',
        'cryptography',
        'uvicorn',
        'pydantic',
        'jinja2',
        'rich',
        'anyio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'sklearn',
        'pandas',
        'notebook',
        'jupyter',
        'IPython',
        'test',
        'tests',
    ],
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
    exclude_binaries=True,
    name='AI_Coding_IDE_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Вимкнути консольне вікно!
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AI_Coding_IDE_v2'
)
