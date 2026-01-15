"""Clipboard utilities for macOS."""

import pyperclip


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard.

    Args:
        text: The text to copy

    Returns:
        True if successful, False otherwise
    """
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def get_clipboard() -> str:
    """Get current clipboard contents."""
    try:
        return pyperclip.paste()
    except Exception:
        return ""
