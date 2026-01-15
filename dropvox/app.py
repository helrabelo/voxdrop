"""DropVox menu bar application."""

import json
import plistlib
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import rumps

from dropvox import __version__
from dropvox.clipboard import copy_to_clipboard
from dropvox.history import HistoryManager
from dropvox.notifications import notify_error, notify_success
from dropvox.transcriber import LANGUAGES, MODELS, SUPPORTED_FORMATS, transcribe_files

# URLs
LANDING_PAGE_URL = "https://dropvox.app"
GITHUB_URL = "https://github.com/helrabelo/dropvox"
RELEASES_URL = "https://github.com/helrabelo/dropvox/releases"
ISSUES_URL = "https://github.com/helrabelo/dropvox/issues"
RELEASES_API = "https://api.github.com/repos/helrabelo/dropvox/releases/latest"

# Update check cooldown (24 hours in seconds)
UPDATE_CHECK_COOLDOWN = 24 * 60 * 60

# Preferences directory
PREFS_DIR = Path.home() / "Library" / "Application Support" / "DropVox"
PREFS_FILE = PREFS_DIR / "preferences.json"


class DropVoxApp(rumps.App):
    """macOS menu bar application for audio transcription."""

    LAUNCH_AGENT_ID = "dev.helrabelo.dropvox"
    LAUNCH_AGENT_PATH = Path.home() / "Library/LaunchAgents" / f"{LAUNCH_AGENT_ID}.plist"

    def __init__(self):
        # Find menu bar icon
        icon_path = self._find_menubar_icon()

        super().__init__(
            name="DropVox",
            title="",  # Empty string for icon-only
            icon=icon_path,
            template=True,  # Adapt to light/dark menu bar
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

        # Check for updates on startup (non-blocking, with cooldown)
        threading.Thread(target=self._startup_update_check, daemon=True).start()

    @staticmethod
    def _find_menubar_icon() -> str | None:
        """Find the menu bar icon path."""
        import sys

        # When running from source
        source_icon = Path(__file__).parent.parent / "assets" / "menubar_icon.png"
        if source_icon.exists():
            return str(source_icon)

        # When running from .app bundle
        if getattr(sys, 'frozen', False):
            bundle_icon = Path(sys._MEIPASS) / "assets" / "menubar_icon.png"
            if bundle_icon.exists():
                return str(bundle_icon)

        return None

    def _setup_menu(self):
        """Set up the menu bar menu."""
        self._status_item = rumps.MenuItem("Status: Ready")
        self._status_item.set_callback(None)

        self._history_menu = rumps.MenuItem("Recent Transcriptions")
        self._populate_history_menu()

        # Model submenu
        model_menu = rumps.MenuItem("Model")
        for m in MODELS:
            item = rumps.MenuItem(
                f"  {m}" if m != self.model else f"* {m}",
                callback=self._make_model_callback(m),
            )
            model_menu.add(item)

        # Language submenu
        language_menu = rumps.MenuItem("Language")
        for lang in LANGUAGES:
            if lang is None:
                language_menu.add(None)  # Separator
            else:
                code, name = lang
                is_selected = code == self.language
                item = rumps.MenuItem(
                    f"* {name}" if is_selected else f"  {name}",
                    callback=self._make_language_callback(code),
                )
                language_menu.add(item)

        # Launch at login item
        self._launch_at_login_item = rumps.MenuItem(
            "Launch at Login",
            callback=self._toggle_launch_at_login,
        )
        self._launch_at_login_item.state = self._is_launch_at_login_enabled()

        # Settings submenu (contains Model, Language, Launch at Login)
        settings_menu = rumps.MenuItem("Settings")
        settings_menu.add(model_menu)
        settings_menu.add(language_menu)
        settings_menu.add(None)  # Separator
        settings_menu.add(self._launch_at_login_item)

        # Version display (non-clickable)
        version_item = rumps.MenuItem(f"DropVox v{__version__}")
        version_item.set_callback(None)

        self.menu = [
            self._status_item,
            None,
            rumps.MenuItem("Select Audio Files...", callback=self.select_files, key="o"),
            rumps.MenuItem("Paste from Clipboard", callback=self.paste_from_clipboard, key="v"),
            None,
            self._history_menu,
            None,
            settings_menu,
            None,
            version_item,
            rumps.MenuItem("Check for Updates...", callback=self._check_for_updates),
            rumps.MenuItem("Website", callback=self._open_website),
            rumps.MenuItem("GitHub", callback=self._open_github),
            rumps.MenuItem("About DropVox", callback=self.show_about),
            None,
            rumps.MenuItem("Quit DropVox", callback=rumps.quit_application, key="q"),
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
        model_menu = self.menu["Settings"]["Model"]
        for item in model_menu.values():
            name = item.title.strip().replace("* ", "").replace("  ", "")
            if name == self.model:
                item.title = f"* {name}"
            else:
                item.title = f"  {name}"

    def _make_language_callback(self, lang_code: str | None):
        def callback(_):
            self.language = lang_code
            self._update_language_menu()
        return callback

    def _update_language_menu(self):
        language_menu = self.menu["Settings"]["Language"]
        for item in language_menu.values():
            if item.title == "":  # Separator
                continue
            # Extract the display name without prefix
            display_name = item.title.strip().replace("* ", "").replace("  ", "")
            # Find the matching language code
            for lang in LANGUAGES:
                if lang is not None:
                    code, name = lang
                    if name == display_name:
                        if code == self.language:
                            item.title = f"* {name}"
                        else:
                            item.title = f"  {name}"
                        break

    def _is_launch_at_login_enabled(self) -> bool:
        """Check if launch at login is enabled."""
        return self.LAUNCH_AGENT_PATH.exists()

    def _get_executable_path(self) -> str:
        """Get the path to the DropVox executable."""
        import sys
        # If running as .app bundle, use the bundle path
        if getattr(sys, 'frozen', False):
            # PyInstaller bundle
            return sys.executable
        else:
            # Running from source - use python -m dropvox
            return f"{sys.executable} -m dropvox"

    def _toggle_launch_at_login(self, sender):
        """Toggle launch at login setting."""
        if self._is_launch_at_login_enabled():
            self._disable_launch_at_login()
            sender.state = False
        else:
            self._enable_launch_at_login()
            sender.state = True

    def _enable_launch_at_login(self):
        """Create LaunchAgent plist to enable launch at login."""
        import sys

        # Ensure LaunchAgents directory exists
        self.LAUNCH_AGENT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Determine how to launch based on environment
        if getattr(sys, 'frozen', False):
            # PyInstaller .app bundle
            program_args = [sys.executable]
        else:
            # Running from source
            program_args = [sys.executable, "-m", "dropvox"]

        plist_content = {
            "Label": self.LAUNCH_AGENT_ID,
            "ProgramArguments": program_args,
            "RunAtLoad": True,
            "KeepAlive": False,
        }

        with open(self.LAUNCH_AGENT_PATH, "wb") as f:
            plistlib.dump(plist_content, f)

    def _disable_launch_at_login(self):
        """Remove LaunchAgent plist to disable launch at login."""
        if self.LAUNCH_AGENT_PATH.exists():
            self.LAUNCH_AGENT_PATH.unlink()

    def select_files(self, _):
        if self._is_transcribing:
            rumps.alert(title="DropVox", message="Already transcribing. Please wait...", ok="OK")
            return

        try:
            from AppKit import NSModalResponseOK, NSOpenPanel

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

    def paste_from_clipboard(self, _):
        """Transcribe audio files from clipboard."""
        if self._is_transcribing:
            rumps.alert(title="DropVox", message="Already transcribing. Please wait...", ok="OK")
            return

        try:
            from AppKit import NSPasteboard, NSURL

            pasteboard = NSPasteboard.generalPasteboard()

            # Try to get file URLs from pasteboard
            file_paths = []

            # Check for file URLs (copied files in Finder)
            urls = pasteboard.readObjectsForClasses_options_([NSURL], None)
            if urls:
                for url in urls:
                    if url.isFileURL():
                        path = Path(url.path())
                        if path.suffix.lower() in SUPPORTED_FORMATS:
                            file_paths.append(str(path))

            if not file_paths:
                rumps.alert(
                    title="DropVox",
                    message="No audio files in clipboard.\n\nCopy audio files (.opus, .mp3, .m4a, .wav) in Finder, then try again.",
                    ok="OK"
                )
                return

            # Start transcription
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
            self._set_title("")  # Reset to icon-only
            # Reset status after delay
            def reset():
                time.sleep(3)
                self._set_status("Ready")
            threading.Thread(target=reset, daemon=True).start()

    def show_about(self, _):
        rumps.alert(
            title="DropVox",
            message=(
                f"DropVox v{__version__}\n\n"
                "Transcribe WhatsApp audio files using Whisper AI.\n\n"
                "Built by Hel Rabelo\n"
                "https://helrabelo.dev"
            ),
            ok="OK",
        )

    def _check_for_updates(self, _):
        """Check GitHub for new releases."""
        try:
            req = urllib.request.Request(
                RELEASES_API,
                headers={"User-Agent": f"DropVox/{__version__}"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                latest_version = data["tag_name"].lstrip("v")

                if self._version_newer(latest_version, __version__):
                    result = rumps.alert(
                        title="Update Available",
                        message=(
                            f"DropVox v{latest_version} is available!\n\n"
                            f"You have v{__version__}.\n\n"
                            "Would you like to download the update?"
                        ),
                        ok="Download",
                        cancel="Later",
                    )
                    if result == 1:  # OK/Download clicked
                        webbrowser.open(RELEASES_URL)
                else:
                    rumps.alert(
                        title="DropVox",
                        message=f"You're up to date!\n\nDropVox v{__version__} is the latest version.",
                        ok="OK",
                    )
        except Exception as e:
            rumps.alert(
                title="Update Check Failed",
                message=f"Could not check for updates.\n\n{str(e)}",
                ok="OK",
            )

    @staticmethod
    def _version_newer(latest: str, current: str) -> bool:
        """Check if latest version is newer than current."""
        try:
            latest_parts = [int(x) for x in latest.split(".")]
            current_parts = [int(x) for x in current.split(".")]
            return latest_parts > current_parts
        except ValueError:
            return False

    def _open_website(self, _):
        """Open DropVox website."""
        webbrowser.open(LANDING_PAGE_URL)

    def _open_github(self, _):
        """Open GitHub repository."""
        webbrowser.open(GITHUB_URL)

    def _load_preferences(self) -> dict:
        """Load preferences from file."""
        if PREFS_FILE.exists():
            try:
                with open(PREFS_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_preferences(self, prefs: dict):
        """Save preferences to file."""
        try:
            PREFS_DIR.mkdir(parents=True, exist_ok=True)
            with open(PREFS_FILE, "w") as f:
                json.dump(prefs, f)
        except OSError:
            pass

    def _startup_update_check(self):
        """Check for updates on startup with 24h cooldown."""
        prefs = self._load_preferences()
        last_check = prefs.get("last_update_check", 0)
        now = time.time()

        # Skip if checked within cooldown period
        if now - last_check < UPDATE_CHECK_COOLDOWN:
            return

        # Update last check time
        prefs["last_update_check"] = now
        self._save_preferences(prefs)

        # Check for updates silently
        try:
            req = urllib.request.Request(
                RELEASES_API,
                headers={"User-Agent": f"DropVox/{__version__}"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                latest_version = data["tag_name"].lstrip("v")

                if self._version_newer(latest_version, __version__):
                    # Show notification for available update
                    self._send_notification(
                        "success",
                        f"DropVox v{latest_version} is available! Click 'Check for Updates' to download."
                    )
        except Exception:
            # Silently fail on startup check
            pass
