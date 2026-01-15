# CLAUDE.md

Development context for VoxDrop - macOS menu bar transcription app.

## Commands

```bash
# Activate environment
source venv/bin/activate

# Run the app
python -m voxdrop

# Run tests
pytest tests/

# Install in dev mode
pip install -e .
```

## Architecture

### Tech Stack

- Python 3.11+
- rumps - macOS menu bar framework
- openai-whisper - Local transcription
- pyperclip - Clipboard support
- pyobjc - macOS native bindings (via rumps)

### Project Structure

```
voxdrop/
├── __init__.py        # Package version
├── __main__.py        # Entry point
├── app.py             # Main rumps application
├── transcriber.py     # Whisper integration
├── clipboard.py       # Clipboard utilities
└── notifications.py   # macOS notifications
```

### Key Modules

**app.py** - Main application class extending `rumps.App`
- Menu bar setup with model selection submenu
- File picker using tkinter (cross-platform)
- Threading for non-blocking transcription
- State management (idle/transcribing)

**transcriber.py** - Whisper wrapper
- Model caching to avoid reloading
- Multi-file transcription with progress callbacks
- Format validation (.opus, .mp3, .m4a, .wav)

**clipboard.py** - Simple pyperclip wrapper

**notifications.py** - macOS notifications via osascript

### Design Decisions

1. **rumps over PyObjC** - Simpler API, sufficient for MVP
2. **tkinter file picker** - Cross-platform, works with rumps
3. **No history** - Clipboard-only per user preference
4. **Model caching** - Avoids slow reloads between transcriptions
5. **Threading** - Non-blocking UI during transcription

## Audio Formats

- `.opus` - WhatsApp default (primary use case)
- `.mp3` - Common audio format
- `.m4a` - Apple audio format
- `.wav` - Uncompressed audio

## Environment

No environment variables required. Whisper models are downloaded automatically on first use to `~/.cache/whisper/`.

## Testing

```bash
pytest tests/                    # All tests
pytest tests/test_transcriber.py # Transcriber only
pytest -v                        # Verbose output
```

Test fixtures should be placed in `tests/fixtures/` (not committed).

## Future Plans

- Native drag-and-drop window using PyObjC
- Swift/SwiftUI rewrite for better performance
- macOS Share Extension
- Keyboard shortcuts
