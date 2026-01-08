# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['asyncio', 'queue', 'mcp', 'mcp.server', 'mcp.server.lowlevel', 'mcp.server.lowlevel.server']
hiddenimports += collect_submodules('importlib.metadata')
hiddenimports += collect_submodules('lightrag_hku')
hiddenimports += collect_submodules('tree_sitter')
hiddenimports += collect_submodules('anthropic')
hiddenimports += collect_submodules('openai')
hiddenimports += collect_submodules('google_genai')
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('tokenizers')
hiddenimports += collect_submodules('sentence_transformers')
hiddenimports += collect_submodules('faiss')


a = Analysis(
    ['E:\\opensource\\LightRAGCoder\\lightragcoder.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
    a.binaries,
    a.datas,
    [],
    name='LightRAGCoder',
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
)
