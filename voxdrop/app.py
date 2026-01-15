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
            quit_button=None,
        )
        self.model = "base"
        self.language = None
        self._is_transcribing = False
        self.history_manager = HistoryManager(max_entries=10)

        # Thread-safe state for UI updates
        self._pending_status = None
        self._pending_title = None
        self._pending_history_refresh = False
        self._pending_notification = None  # (type, message)

        self._setup_menu()

        # Timer for thread-safe UI updates (runs every 0.25s on main thread)
        self._update_timer = rumps.Timer(self._process_pending_updates, 0.25)
        self._update_timer.start()

    def _setup_menu(self):
        """Set up the menu bar menu."""
        self._status_item = rumps.MenuItem("Status: Ready")
        self._status_item.set_callback(None)

        self._history_menu = rumps.MenuItem("Recent Transcriptions")
        self._populate_history_menu()

        model_menu = rumps.MenuItem("Model")
        for m in MODELS:
            item = rumps.MenuItem(
                f"  {m}" if m != self.model else f"* {m}",
                callback=self._make_model_callback(m),
            )
            model_menu.add(item)

        self.menu = [
            self._status_item,
            None,
            rumps.MenuItem("Select Audio Files...", callback=self.select_files),
            None,
            self._history_menu,
            None,
            model_menu,
            None,
            rumps.MenuItem("About VoxDrop", callback=self.show_about),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

    def _populate_history_menu(self):
        """Populate history menu with current entries."""
        history = self.history_manager.get_all()

        if not history:
            empty_item = rumps.MenuItem("No transcriptions yet")
            empty_item.set_callback(None)
            self._history_menu.add(empty_item)
        else:
            for record in history:
                label = f'"{record.preview}" ({record.time_ago()})'
                item = rumps.MenuItem(
                    label,
                    callback=self._make_history_callback(record.id),
                )
                self._history_menu.add(item)

            self._history_menu.add(None)
            self._history_menu.add(rumps.MenuItem("Clear History", callback=self._clear_history))

    def _process_pending_updates(self, _):
        """Process pending UI updates on main thread."""
        # Update status
        if self._pending_status is not None:
            self._status_item.title = f"Status: {self._pending_status}"
            self._pending_status = None

        # Update title
        if self._pending_title is not None:
            self.title = self._pending_title
            self._pending_title = None

        # Refresh history
        if self._pending_history_refresh:
            self._pending_history_refresh = False
            try:
                self._history_menu.clear()
                self._populate_history_menu()
            except Exception:
                pass

        # Send notification
        if self._pending_notification is not None:
            ntype, msg = self._pending_notification
            self._pending_notification = None
            if ntype == "success":
                notify_success(msg)
            elif ntype == "error":
                notify_error(msg)

    # Thread-safe setters (can be called from any thread)
    def _set_status(self, status: str):
        self._pending_status = status

    def _set_title(self, title: str):
        self._pending_title = title

    def _request_history_refresh(self):
        self._pending_history_refresh = True

    def _send_notification(self, ntype: str, msg):
        self._pending_notification = (ntype, msg)

    def _make_history_callback(self, record_id: str):
        def callback(_):
            record = self.history_manager.get_by_id(record_id)
            if record:
                if copy_to_clipboard(record.text):
                    self._set_status("Copied to clipboard!")
                    # Schedule reset
                    def reset():
                        time.sleep(2)
                        self._set_status("Ready")
                    threading.Thread(target=reset, daemon=True).start()
                else:
                    self._send_notification("error", "Failed to copy to clipboard")
        return callback

    def _clear_history(self, _):
        self.history_manager.clear()
        self._request_history_refresh()
        self._set_status("History cleared")
        def reset():
            time.sleep(2)
            self._set_status("Ready")
        threading.Thread(target=reset, daemon=True).start()

    def _make_model_callback(self, model_name: str):
        def callback(_):
            self.model = model_name
            self._update_model_menu()
        return callback

    def _update_model_menu(self):
        model_menu = self.menu["Model"]
        for item in model_menu.values():
            name = item.title.strip().replace("* ", "").replace("  ", "")
            if name == self.model:
                item.title = f"* {name}"
            else:
                item.title = f"  {name}"

    def select_files(self, _):
        if self._is_transcribing:
            rumps.alert(title="VoxDrop", message="Already transcribing. Please wait...", ok="OK")
            return

        try:
            from AppKit import NSApplication, NSModalResponseOK, NSOpenPanel

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
                    thread = threading.Thread(
                        target=self._transcribe_files,
                        args=(file_paths,),
                        daemon=True,
                    )
                    thread.start()

        except Exception as e:
            self._send_notification("error", str(e))

    def _transcribe_files(self, file_paths: list[str]):
        """Background transcription task."""
        self._is_transcribing = True
        file_count = len(file_paths)
        start_time = time.time()

        try:
            self._set_status(f"Loading model...")
            self._set_title(f"[0/{file_count}]")

            paths = [Path(p) for p in file_paths]
            file_names = [p.name for p in paths]

            def on_progress(current: int, total: int, filename: str):
                pct = int((current / total) * 100)
                short_name = filename[:20] + "..." if len(filename) > 20 else filename
                self._set_status(f"Transcribing {pct}% ({current}/{total}) - {short_name}")
                self._set_title(f"[{current}/{total}]")

            text = transcribe_files(
                paths,
                model=self.model,
                language=self.language,
                on_progress=on_progress,
            )

            # Save to history
            self.history_manager.save(text=text, file_names=file_names, model=self.model)
            self._request_history_refresh()

            # Copy to clipboard
            if copy_to_clipboard(text):
                elapsed = time.time() - start_time
                self._set_status(f"Done! ({elapsed:.1f}s)")
                self._send_notification("success", file_count)
            else:
                self._send_notification("error", "Failed to copy to clipboard")

        except Exception as e:
            self._set_status(f"Error: {str(e)[:30]}")
            self._send_notification("error", str(e))

        finally:
            self._is_transcribing = False
            self._set_title("VoxDrop")
            # Reset status after delay
            def reset():
                time.sleep(3)
                self._set_status("Ready")
            threading.Thread(target=reset, daemon=True).start()

    def show_about(self, _):
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
