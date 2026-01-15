"""Audio transcription using OpenAI Whisper."""

import os
import sys
from pathlib import Path
from typing import Callable

# Set up static ffmpeg before importing whisper
def _setup_ffmpeg():
    """Add static-ffmpeg to PATH if available."""
    # Check if running from PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # For .app bundle, check multiple possible locations
        possible_paths = [
            # PyInstaller _MEIPASS location
            Path(sys._MEIPASS) / 'static_ffmpeg' / 'bin' / 'darwin',
            # .app bundle Frameworks location
            Path(sys.executable).parent.parent / 'Frameworks' / 'static_ffmpeg' / 'bin' / 'darwin',
            # .app bundle Resources location
            Path(sys.executable).parent.parent / 'Resources' / 'static_ffmpeg' / 'bin' / 'darwin',
        ]

        for ffmpeg_dir in possible_paths:
            if ffmpeg_dir.exists() and (ffmpeg_dir / 'ffmpeg').exists():
                os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")
                return

    # Try static_ffmpeg module (for development)
    try:
        import static_ffmpeg
        ffmpeg_path, _ = static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()
        ffmpeg_dir = str(Path(ffmpeg_path).parent)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    except ImportError:
        pass  # static-ffmpeg not installed, rely on system ffmpeg

_setup_ffmpeg()

import whisper

SUPPORTED_FORMATS = {".opus", ".mp3", ".m4a", ".wav"}
MODELS = ["tiny", "base", "small", "medium", "large"]

# Common languages for WhatsApp transcription (code, display name)
LANGUAGES = [
    (None, "Auto-detect"),
    ("pt", "Portuguese (PT-BR)"),
    ("en", "English (EN-US)"),
    None,  # Separator
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("ar", "Arabic"),
    ("it", "Italian"),
    ("nl", "Dutch"),
    ("ru", "Russian"),
    ("hi", "Hindi"),
]

# Cache the model to avoid reloading
_model_cache: dict[str, whisper.Whisper] = {}


def get_model(model_name: str = "base") -> whisper.Whisper:
    """Get or load a Whisper model (cached)."""
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]


def is_supported_format(file_path: Path) -> bool:
    """Check if the file format is supported."""
    return file_path.suffix.lower() in SUPPORTED_FORMATS


def transcribe_files(
    file_paths: list[Path],
    model: str = "base",
    language: str | None = None,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> str:
    """
    Transcribe multiple audio files and return combined text.

    Args:
        file_paths: List of audio file paths
        model: Whisper model name (tiny, base, small, medium, large)
        language: Optional language code (auto-detect if None)
        on_progress: Callback(current, total, filename) for progress updates

    Returns:
        Combined transcription text
    """
    if not file_paths:
        return ""

    # Filter to supported formats only
    valid_files = [f for f in file_paths if is_supported_format(f)]
    if not valid_files:
        raise ValueError("No supported audio files provided")

    # Load the model
    model_instance = get_model(model)

    transcriptions = []
    total = len(valid_files)

    for i, audio_file in enumerate(valid_files, 1):
        if on_progress:
            on_progress(i, total, audio_file.name)

        result = model_instance.transcribe(str(audio_file), language=language)
        text = result["text"].strip()
        transcriptions.append(text)

    # Combine all transcriptions
    if len(transcriptions) == 1:
        return transcriptions[0]

    # Multiple files: join with newlines
    return "\n\n".join(transcriptions)


def transcribe_single(
    file_path: Path,
    model: str = "base",
    language: str | None = None,
) -> str:
    """Transcribe a single audio file."""
    return transcribe_files([file_path], model, language)
