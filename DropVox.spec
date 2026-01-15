# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for DropVox macOS app."""

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)

# Find static-ffmpeg binaries
def get_ffmpeg_binaries():
    """Get static-ffmpeg binary paths for bundling."""
    try:
        import static_ffmpeg
        ffmpeg_path, ffprobe_path = static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()
        ffmpeg_dir = Path(ffmpeg_path).parent
        return [
            (str(ffmpeg_dir / 'ffmpeg'), 'static_ffmpeg/bin/darwin'),
            (str(ffmpeg_dir / 'ffprobe'), 'static_ffmpeg/bin/darwin'),
        ]
    except Exception:
        return []

ffmpeg_binaries = get_ffmpeg_binaries()

# Find whisper assets
def get_whisper_assets():
    """Get whisper asset files for bundling."""
    try:
        import whisper
        whisper_dir = Path(whisper.__path__[0])
        assets_dir = whisper_dir / 'assets'
        if assets_dir.exists():
            return [(str(assets_dir), 'whisper/assets')]
    except Exception:
        pass
    return []

whisper_assets = get_whisper_assets()

a = Analysis(
    [str(project_root / 'dropvox' / '__main__.py')],
    pathex=[str(project_root)],
    binaries=ffmpeg_binaries,
    datas=[
        (str(project_root / 'assets' / 'menubar_icon.png'), 'assets'),
        (str(project_root / 'assets' / 'menubar_icon@2x.png'), 'assets'),
    ] + whisper_assets,
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
        'static_ffmpeg',
        'static_ffmpeg.run',
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
    name='DropVox',
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
    name='DropVox',
)

app = BUNDLE(
    coll,
    name='DropVox.app',
    icon=str(project_root / 'assets' / 'icon.icns') if (project_root / 'assets' / 'icon.icns').exists() else None,
    bundle_identifier='dev.helrabelo.dropvox',
    info_plist={
        'CFBundleName': 'DropVox',
        'CFBundleDisplayName': 'DropVox',
        'CFBundleVersion': '0.7.2',
        'CFBundleShortVersionString': '0.7.2',
        'LSMinimumSystemVersion': '10.15',
        'LSUIElement': True,  # Menu bar app (no dock icon)
        'NSHighResolutionCapable': True,
        'NSMicrophoneUsageDescription': 'DropVox needs microphone access for audio transcription.',
    },
)
