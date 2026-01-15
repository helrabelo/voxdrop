# VoxDrop

> Drag. Drop. Transcribe. A macOS menu bar app for WhatsApp audio files.

VoxDrop lives in your menu bar and transcribes audio files using [OpenAI Whisper](https://github.com/openai/whisper). Perfect for quickly transcribing WhatsApp voice messages without leaving your workflow.

## Features

- **Simple** - Lives in your menu bar, always one click away
- **Fast** - Uses Whisper "base" model by default for quick transcriptions
- **Batch Support** - Select multiple files, get one combined transcript
- **Auto-Copy** - Transcription copied to clipboard automatically
- **Native** - macOS notifications when complete
- **Private** - All processing happens locally on your Mac

## Supported Formats

- `.opus` (WhatsApp default)
- `.mp3`
- `.m4a`
- `.wav`

## Installation

### From Source

```bash
git clone https://github.com/helrabelo/voxdrop.git
cd voxdrop
python3 -m venv venv
source venv/bin/activate
pip install -e .
voxdrop
```

### Requirements

- macOS 12.0+
- Python 3.10+
- ~1GB disk space (for Whisper model on first run)

## Usage

1. Click the **VoxDrop** text in your menu bar
2. Select **"Select Audio Files..."**
3. Choose one or more audio files
4. Wait for transcription (progress shown in menu bar)
5. Transcription is automatically copied to clipboard
6. Paste anywhere!

## Configuration

Click the menu bar icon to access:

- **Model Selection**: tiny, base (default), small, medium, large
  - Larger models = better accuracy, slower speed
  - `base` is recommended for most use cases

## Development

```bash
# Run in development
source venv/bin/activate
python -m voxdrop

# Run tests
pip install pytest
pytest tests/
```

See [CLAUDE.md](CLAUDE.md) for development context.

## How It Works

1. VoxDrop uses [rumps](https://github.com/jaredks/rumps) for the menu bar interface
2. Audio files are transcribed locally using OpenAI's Whisper model
3. Results are copied to your clipboard via pyperclip
4. macOS notifications inform you when transcription is complete

## Roadmap

- [ ] Native drag-and-drop window (PyObjC)
- [ ] Language detection/selection UI
- [ ] Keyboard shortcut support
- [ ] Swift/SwiftUI native rewrite
- [ ] Share Extension for macOS share sheet
- [ ] App Store distribution

## License

MIT - See [LICENSE](LICENSE)

---

Built by [Hel Rabelo](https://helrabelo.dev) as a weekend experiment.
