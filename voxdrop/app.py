"""VoxDrop menu bar application."""

import threading
import time
from pathlib import Path

import rumps

from voxdrop.clipboard import copy_to_clipboard
from voxdrop.history import HistoryManager
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
        self.history_manager = HistoryManager(max_entries=10)
        self._setup_menu()

    def _setup_menu(self):
        """Set up the menu bar menu."""
        # Status item (at top)
        self._status_item = rumps.MenuItem("Status: Ready")
        self._status_item.set_callback(None)  # Not clickable

        # History submenu
        self._history_menu = rumps.MenuItem("Recent Transcriptions")
        self._refresh_history_menu()

        # Model submenu
        model_menu = rumps.MenuItem("Model")
        for m in MODELS:
            item = rumps.MenuItem(
                f"  {m}" if m != self.model else f"* {m}",
                callback=self._make_model_callback(m),
            )
            model_menu.add(item)

        self.menu = [
            self._status_item,
            None,  # Separator
            rumps.MenuItem("Select Audio Files...", callback=self.select_files),
            None,  # Separator
            self._history_menu,
            None,  # Separator
            model_menu,
            None,  # Separator
            rumps.MenuItem("About VoxDrop", callback=self.show_about),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

    def _refresh_history_menu(self):
        """Refresh the history submenu with current entries."""
        # Clear existing items
        self._history_menu.clear()

        history = self.history_manager.get_all()

        if not history:
            empty_item = rumps.MenuItem("No transcriptions yet")
            empty_item.set_callback(None)
            self._history_menu.add(empty_item)
        else:
            for record in history:
                # Format: "Preview text... (time ago)"
                label = f'"{record.preview}" ({record.time_ago()})'
                item = rumps.MenuItem(
                    label,
                    callback=self._make_history_callback(record.id),
                )
                self._history_menu.add(item)

            # Add separator and clear option
            self._history_menu.add(None)
            clear_item = rumps.MenuItem(
                "Clear History",
                callback=self._clear_history,
            )
            self._history_menu.add(clear_item)

    def _make_history_callback(self, record_id: str):
        """Create a callback for clicking a history item."""

        def callback(_):
            record = self.history_manager.get_by_id(record_id)
            if record:
                if copy_to_clipboard(record.text):
                    self._update_status("Copied to clipboard!")
                    # Reset status after 2 seconds
                    threading.Timer(2.0, lambda: self._update_status("Ready")).start()
                else:
                    notify_error("Failed to copy to clipboard")

        return callback

    def _clear_history(self, _):
        """Clear all history."""
        self.history_manager.clear()
        self._refresh_history_menu()
        self._update_status("History cleared")
        threading.Timer(2.0, lambda: self._update_status("Ready")).start()

    def _update_status(self, status: str):
        """Update the status menu item."""
        self._status_item.title = f"Status: {status}"

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

    def select_files(self, _):
        """Handle file selection."""
        if self._is_transcribing:
            rumps.alert(
                title="VoxDrop",
                message="Already transcribing. Please wait...",
                ok="OK",
            )
            return

        # Use native macOS file picker via PyObjC (more reliable than tkinter)
        try:
            from AppKit import NSApplication, NSModalResponseOK, NSOpenPanel

            # Activate the app to bring file dialog to front
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

            panel = NSOpenPanel.openPanel()
            panel.setCanChooseFiles_(True)
            panel.setCanChooseDirectories_(False)
            panel.setAllowsMultipleSelection_(True)
            panel.setAllowedFileTypes_(["opus", "mp3", "m4a", "wav"])
            panel.setTitle_("Select Audio Files")
            panel.setMessage_("Choose WhatsApp audio files to transcribe")

            if panel.runModal() == NSModalResponseOK:
                file_paths = [str(url.path()) for url in panel.URLs()]
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

    def _transcribe_files(self, file_paths: list[str]):
        """Background transcription task."""
        self._is_transcribing = True
        original_title = self.title
        file_count = len(file_paths)
        start_time = time.time()

        try:
            # Update status
            self._update_status(f"Transcribing 0/{file_count}...")
            self.title = f"[0/{file_count}]"

            # Convert to Path objects
            paths = [Path(p) for p in file_paths]
            file_names = [p.name for p in paths]

            # Transcribe with progress updates
            def on_progress(current: int, total: int, filename: str):
                elapsed = time.time() - start_time
                pct = int((current / total) * 100)
                # Truncate filename if too long
                short_name = filename[:20] + "..." if len(filename) > 20 else filename
                self._update_status(f"Transcribing {pct}% ({current}/{total}) - {short_name}")
                self.title = f"[{current}/{total}]"

            text = transcribe_files(
                paths,
                model=self.model,
                language=self.language,
                on_progress=on_progress,
            )

            # Save to history
            self.history_manager.save(
                text=text,
                file_names=file_names,
                model=self.model,
            )
            self._refresh_history_menu()

            # Copy to clipboard
            if copy_to_clipboard(text):
                elapsed = time.time() - start_time
                self._update_status(f"Done! ({elapsed:.1f}s)")
                notify_success(file_count)
            else:
                notify_error("Failed to copy to clipboard")

        except Exception as e:
            self._update_status(f"Error: {str(e)[:30]}")
            notify_error(str(e))

        finally:
            self._is_transcribing = False
            self.title = original_title
            # Reset status after 3 seconds
            threading.Timer(3.0, lambda: self._update_status("Ready")).start()

    def show_about(self, _):
        """Show about dialog."""
        rumps.alert(
            title="VoxDrop",
            message=(
                "VoxDrop v0.2.0\n\n"
                "Transcribe WhatsApp audio files using Whisper AI.\n\n"
                "Built by Hel Rabelo\n"
                "https://helrabelo.dev"
            ),
            ok="OK",
        )
