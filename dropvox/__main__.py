#!/usr/bin/env python3
"""DropVox - macOS menu bar audio transcription."""

import multiprocessing
import os
import sys
import fcntl
from pathlib import Path

# PyInstaller multiprocessing support - must be early
multiprocessing.freeze_support()

# Single-instance lock file
LOCK_FILE = Path.home() / ".dropvox" / "app.lock"
_lock_fd = None  # Keep reference to prevent garbage collection


def acquire_lock():
    """Acquire single-instance lock. Exit silently if another instance is running."""
    global _lock_fd
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    _lock_fd = open(LOCK_FILE, 'w')
    try:
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Write PID for debugging
        _lock_fd.write(str(os.getpid()))
        _lock_fd.flush()
    except BlockingIOError:
        # Another instance is already running - exit silently
        sys.exit(0)


def main():
    """Run the DropVox menu bar application."""
    # Write PID after acquiring lock
    if _lock_fd:
        _lock_fd.seek(0)
        _lock_fd.truncate()
        _lock_fd.write(str(os.getpid()))
        _lock_fd.flush()

    from dropvox.app import DropVoxApp
    app = DropVoxApp()
    app.run()


if __name__ == "__main__":
    acquire_lock()
    main()
