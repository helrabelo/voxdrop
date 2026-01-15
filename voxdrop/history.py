"""Transcription history management."""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class TranscriptionRecord:
    """A single transcription history entry."""

    id: str
    text: str
    preview: str
    file_names: list[str]
    file_count: int
    model: str
    timestamp: str  # ISO format string for JSON serialization

    @classmethod
    def create(
        cls,
        text: str,
        file_names: list[str],
        model: str,
    ) -> "TranscriptionRecord":
        """Create a new transcription record."""
        preview = text[:50].replace("\n", " ").strip()
        if len(text) > 50:
            preview += "..."

        return cls(
            id=str(uuid.uuid4()),
            text=text,
            preview=preview,
            file_names=file_names,
            file_count=len(file_names),
            model=model,
            timestamp=datetime.now().isoformat(),
        )

    @property
    def datetime(self) -> datetime:
        """Get timestamp as datetime object."""
        return datetime.fromisoformat(self.timestamp)

    def time_ago(self) -> str:
        """Get human-readable time ago string."""
        now = datetime.now()
        diff = now - self.datetime
        seconds = diff.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        else:
            days = int(seconds / 86400)
            return f"{days}d ago"


class HistoryManager:
    """Manages transcription history with persistence."""

    DEFAULT_DIR = Path.home() / ".voxdrop"
    DEFAULT_FILE = "history.json"

    def __init__(self, max_entries: int = 10, storage_dir: Path | None = None):
        """Initialize history manager.

        Args:
            max_entries: Maximum number of history entries to keep
            storage_dir: Directory for storage (default: ~/.voxdrop/)
        """
        self.max_entries = max_entries
        self.storage_dir = storage_dir or self.DEFAULT_DIR
        self.storage_file = self.storage_dir / self.DEFAULT_FILE
        self._history: list[TranscriptionRecord] = []
        self._ensure_storage_dir()
        self._load()

    def _ensure_storage_dir(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load history from disk."""
        if not self.storage_file.exists():
            self._history = []
            return

        try:
            with open(self.storage_file, "r") as f:
                data = json.load(f)
                self._history = [TranscriptionRecord(**record) for record in data]
        except (json.JSONDecodeError, KeyError, TypeError):
            # Corrupted file, start fresh
            self._history = []

    def _save(self) -> None:
        """Save history to disk."""
        data = [asdict(record) for record in self._history]
        with open(self.storage_file, "w") as f:
            json.dump(data, f, indent=2)

    def save(
        self,
        text: str,
        file_names: list[str],
        model: str,
    ) -> TranscriptionRecord:
        """Save a new transcription to history.

        Args:
            text: The transcription text
            file_names: List of transcribed file names
            model: Whisper model used

        Returns:
            The created TranscriptionRecord
        """
        record = TranscriptionRecord.create(text, file_names, model)

        # Add to beginning (most recent first)
        self._history.insert(0, record)

        # Trim to max entries
        if len(self._history) > self.max_entries:
            self._history = self._history[: self.max_entries]

        self._save()
        return record

    def get_all(self) -> list[TranscriptionRecord]:
        """Get all history entries (most recent first)."""
        return self._history.copy()

    def get_by_id(self, record_id: str) -> TranscriptionRecord | None:
        """Get a specific record by ID."""
        for record in self._history:
            if record.id == record_id:
                return record
        return None

    def delete(self, record_id: str) -> bool:
        """Delete a specific record by ID.

        Returns:
            True if record was found and deleted, False otherwise
        """
        for i, record in enumerate(self._history):
            if record.id == record_id:
                del self._history[i]
                self._save()
                return True
        return False

    def clear(self) -> None:
        """Clear all history."""
        self._history = []
        self._save()

    def __len__(self) -> int:
        """Get number of history entries."""
        return len(self._history)

    def __bool__(self) -> bool:
        """Check if history has any entries."""
        return bool(self._history)
