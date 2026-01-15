"""Tests for the VoxDrop app module."""

import pytest


class TestAppInitialization:
    """Test app initialization."""

    def test_import_app(self):
        """App module should import without errors."""
        from voxdrop.app import VoxDropApp

        assert VoxDropApp is not None

    def test_import_clipboard(self):
        """Clipboard module should import without errors."""
        from voxdrop.clipboard import copy_to_clipboard, get_clipboard

        assert copy_to_clipboard is not None
        assert get_clipboard is not None

    def test_import_notifications(self):
        """Notifications module should import without errors."""
        from voxdrop.notifications import notify, notify_error, notify_success

        assert notify is not None
        assert notify_error is not None
        assert notify_success is not None


# Note: Full app integration tests require macOS GUI environment
# and are tested manually
