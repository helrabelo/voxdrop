# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for VoxDrop macOS app."""

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / 'voxdrop' / '__main__.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'rumps',
        'whisper',
        'pyperclip',
        'torch',
        'torchaudio',
        'numpy',
        'regex',
        'tqdm',
        'more_itertools',
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
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
    [],
    exclude_binaries=True,
    name='VoxDrop',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoxDrop',
)

app = BUNDLE(
    coll,
    name='VoxDrop.app',
    icon=str(project_root / 'assets' / 'icon.icns') if (project_root / 'assets' / 'icon.icns').exists() else None,
    bundle_identifier='dev.helrabelo.voxdrop',
    info_plist={
        'CFBundleName': 'VoxDrop',
        'CFBundleDisplayName': 'VoxDrop',
        'CFBundleVersion': '0.3.0',
        'CFBundleShortVersionString': '0.3.0',
        'LSMinimumSystemVersion': '10.15',
        'LSUIElement': True,  # Menu bar app (no dock icon)
        'NSHighResolutionCapable': True,
        'NSMicrophoneUsageDescription': 'VoxDrop needs microphone access for audio transcription.',
    },
)
