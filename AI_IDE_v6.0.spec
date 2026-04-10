# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('ui/', 'ui/'), ('core/', 'core/'), ('plugins/', 'plugins/'), ('style.qss', '.')],
    hiddenimports=['agent_tools', 'git_integration', 'orchestrator', 'local_engine', 'model_manager', 'context_engine', 'autocomplete', 'settings', 'fastapi', 'uvicorn', 'zeroconf', 'pandas', 'matplotlib', 'pyscreenshot', 'speech_recognition', 'deep_translator'],
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
