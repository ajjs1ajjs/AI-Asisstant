# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('ui/', 'ui/'), ('core/', 'core/'), ('plugins/', 'plugins/'), ('threads/', 'threads/'), ('style.qss', '.'), ('icon.ico', '.'), ('agent_tools.py', '.'), ('autocomplete.py', '.'), ('context_engine.py', '.'), ('git_dialog.py', '.'), ('git_integration.py', '.'), ('hook-runtime.py', '.'), ('local_engine.py', '.'), ('main.py', '.'), ('model_benchmark.py', '.'), ('model_manager.py', '.'), ('orchestrator.py', '.'), ('settings.py', '.'), ('settings_dialog.py', '.')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('llama_cpp')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('faiss')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sentence_transformers')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI_IDE_v6.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI_IDE_v6.0',
)
