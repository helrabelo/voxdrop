"""macOS notification utilities."""

import subprocess


def notify(title: str, message: str, sound: bool = True) -> None:
    """
    Send a macOS notification using osascript.

    Args:
        title: Notification title
        message: Notification body text
        sound: Whether to play a sound (default: True)
    """
    # Escape quotes in message
    message = message.replace('"', '\\"')
    title = title.replace('"', '\\"')

    script = f'display notification "{message}" with title "{title}"'
    if sound:
        script += ' sound name "default"'

    subprocess.run(["osascript", "-e", script], check=False, capture_output=True)


def notify_success(file_count: int) -> None:
    """Send a success notification after transcription."""
    if file_count == 1:
        message = "Transcription complete. Copied to clipboard!"
    else:
        message = f"Transcribed {file_count} files. Copied to clipboard!"

    notify("DropVox", message)


def notify_error(error_message: str) -> None:
    """Send an error notification."""
    notify("DropVox", f"Error: {error_message}", sound=True)
