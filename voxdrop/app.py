"""VoxDrop menu bar application."""

import threading
from pathlib import Path

import rumps

from voxdrop.clipboard import copy_to_clipboard
from voxdrop.notifications import notify_error, notify_success
from voxdrop.transcriber import MODELS, transcribe_files


class VoxDropApp(rumps.App):
    """macOS menu bar application for audio transcription."""

    def __init__(self):
        super().__init__(
            name="VoxDrop",
            title="VoxDrop",
            quit_button=None,  # We'll add our own
        )
        self.model = "base"
        self.language = None  # Auto-detect
        self._is_transcribing = False
        self._setup_menu()

    def _setup_menu(self):
        """Set up the menu bar menu."""
        # Model submenu
        model_menu = rumps.MenuItem("Model")
        for m in MODELS:
            item = rumps.MenuItem(
                f"  {m}" if m != self.model else f"* {m}",
                callback=self._make_model_callback(m),
            )
            model_menu.add(item)

        self.menu = [
            rumps.MenuItem("Select Audio Files...", callback=self.select_files),
            None,  # Separator
            model_menu,
            None,  # Separator
            rumps.MenuItem("About VoxDrop", callback=self.show_about),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

    def _make_model_callback(self, model_name: str):
        """Create a callback for model selection."""

        def callback(_):
            self.model = model_name
            self._update_model_menu()

        return callback

    def _update_model_menu(self):
        """Update the model menu checkmarks."""
        model_menu = self.menu["Model"]
        for item in model_menu.values():
            name = item.title.strip().replace("* ", "").replace("  ", "")
            if name == self.model:
                item.title = f"* {name}"
            else:
                item.title = f"  {name}"

    @rumps.clicked("Select Audio Files...")
    def select_files(self, _):
        """Handle file selection."""
        if self._is_transcribing:
            rumps.alert(
                title="VoxDrop",
                message="Already transcribing. Please wait...",
                ok="OK",
            )
            return

        # Use tkinter for file dialog (works well with rumps)
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            file_paths = filedialog.askopenfilenames(
                title="Select Audio Files",
                filetypes=[
                    ("Audio Files", "*.opus *.mp3 *.m4a *.wav"),
                    ("WhatsApp Audio", "*.opus"),
                    ("MP3 Files", "*.mp3"),
                    ("M4A Files", "*.m4a"),
                    ("WAV Files", "*.wav"),
                    ("All Files", "*.*"),
                ],
            )
            root.destroy()

            if file_paths:
                # Run transcription in background thread
                thread = threading.Thread(
                    target=self._transcribe_files,
                    args=(file_paths,),
                    daemon=True,
                )
                thread.start()

        except Exception as e:
            notify_error(str(e))

    def _transcribe_files(self, file_paths: tuple[str, ...]):
        """Background transcription task."""
        self._is_transcribing = True
        original_title = self.title
        file_count = len(file_paths)

        try:
            # Update menu bar to show progress
            self.title = "Transcribing..."

            # Convert to Path objects
            paths = [Path(p) for p in file_paths]

            # Transcribe with progress updates
            def on_progress(current: int, total: int, filename: str):
                self.title = f"[{current}/{total}]"

            text = transcribe_files(
                paths,
                model=self.model,
                language=self.language,
                on_progress=on_progress,
            )

            # Copy to clipboard
            if copy_to_clipboard(text):
                notify_success(file_count)
            else:
                notify_error("Failed to copy to clipboard")

        except Exception as e:
            notify_error(str(e))

        finally:
            self._is_transcribing = False
            self.title = original_title

    @rumps.clicked("About VoxDrop")
    def show_about(self, _):
        """Show about dialog."""
        rumps.alert(
            title="VoxDrop",
            message=(
                "VoxDrop v0.1.0\n\n"
                "Transcribe WhatsApp audio files using Whisper AI.\n\n"
                "Built by Hel Rabelo\n"
                "https://helrabelo.dev"
            ),
            ok="OK",
        )
