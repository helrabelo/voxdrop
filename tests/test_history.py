"""Tests for the history module."""

import json
import tempfile
from pathlib import Path

import pytest

from voxdrop.history import HistoryManager, TranscriptionRecord


@pytest.fixture
def temp_storage():
    """Create a temporary directory for history storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def history_manager(temp_storage):
    """Create a HistoryManager with temporary storage."""
    return HistoryManager(max_entries=5, storage_dir=temp_storage)


class TestTranscriptionRecord:
    """Tests for TranscriptionRecord dataclass."""

    def test_create_record(self):
        """Should create a record with preview."""
        record = TranscriptionRecord.create(
            text="This is a test transcription that is longer than fifty characters for preview",
            file_names=["audio1.opus", "audio2.opus"],
            model="base",
        )

        assert record.id is not None
        assert record.text.startswith("This is a test")
        assert record.preview == "This is a test transcription that is longer than f..."
        assert record.file_count == 2
        assert record.model == "base"
        assert record.timestamp is not None

    def test_create_short_preview(self):
        """Should not add ellipsis for short text."""
        record = TranscriptionRecord.create(
            text="Short text",
            file_names=["audio.opus"],
            model="tiny",
        )

        assert record.preview == "Short text"
        assert "..." not in record.preview

    def test_time_ago_just_now(self):
        """Should show 'just now' for recent records."""
        record = TranscriptionRecord.create(
            text="Test",
            file_names=["audio.opus"],
            model="base",
        )

        assert record.time_ago() == "just now"


class TestHistoryManager:
    """Tests for HistoryManager class."""

    def test_save_and_retrieve(self, history_manager):
        """Should save and retrieve transcriptions."""
        record = history_manager.save(
            text="Test transcription",
            file_names=["audio.opus"],
            model="base",
        )

        history = history_manager.get_all()
        assert len(history) == 1
        assert history[0].text == "Test transcription"
        assert history[0].id == record.id

    def test_max_entries_limit(self, history_manager):
        """Should limit to max_entries (5 in fixture)."""
        for i in range(10):
            history_manager.save(
                text=f"Transcription {i}",
                file_names=[f"audio{i}.opus"],
                model="base",
            )

        history = history_manager.get_all()
        assert len(history) == 5
        # Most recent should be first
        assert history[0].text == "Transcription 9"

    def test_most_recent_first(self, history_manager):
        """Should order entries with most recent first."""
        history_manager.save(text="First", file_names=["a.opus"], model="base")
        history_manager.save(text="Second", file_names=["b.opus"], model="base")
        history_manager.save(text="Third", file_names=["c.opus"], model="base")

        history = history_manager.get_all()
        assert history[0].text == "Third"
        assert history[1].text == "Second"
        assert history[2].text == "First"

    def test_get_by_id(self, history_manager):
        """Should retrieve specific record by ID."""
        record = history_manager.save(
            text="Find me",
            file_names=["audio.opus"],
            model="base",
        )

        found = history_manager.get_by_id(record.id)
        assert found is not None
        assert found.text == "Find me"

    def test_get_by_id_not_found(self, history_manager):
        """Should return None for unknown ID."""
        found = history_manager.get_by_id("nonexistent-id")
        assert found is None

    def test_delete_record(self, history_manager):
        """Should delete a specific record."""
        record = history_manager.save(
            text="Delete me",
            file_names=["audio.opus"],
            model="base",
        )

        assert len(history_manager) == 1

        deleted = history_manager.delete(record.id)
        assert deleted is True
        assert len(history_manager) == 0

    def test_delete_nonexistent(self, history_manager):
        """Should return False when deleting nonexistent record."""
        deleted = history_manager.delete("nonexistent-id")
        assert deleted is False

    def test_clear_history(self, history_manager):
        """Should clear all history."""
        history_manager.save(text="One", file_names=["a.opus"], model="base")
        history_manager.save(text="Two", file_names=["b.opus"], model="base")

        assert len(history_manager) == 2

        history_manager.clear()
        assert len(history_manager) == 0
        assert not history_manager

    def test_persistence(self, temp_storage):
        """Should persist history across instances."""
        # Create first manager and save
        manager1 = HistoryManager(max_entries=10, storage_dir=temp_storage)
        manager1.save(text="Persist me", file_names=["audio.opus"], model="base")

        # Create second manager pointing to same storage
        manager2 = HistoryManager(max_entries=10, storage_dir=temp_storage)
        history = manager2.get_all()

        assert len(history) == 1
        assert history[0].text == "Persist me"

    def test_corrupted_file_recovery(self, temp_storage):
        """Should recover from corrupted history file."""
        # Write corrupted JSON
        storage_file = temp_storage / "history.json"
        storage_file.write_text("{ invalid json }")

        # Should not crash, should start with empty history
        manager = HistoryManager(max_entries=10, storage_dir=temp_storage)
        assert len(manager) == 0

    def test_empty_history_bool(self, history_manager):
        """Should be falsy when empty."""
        assert not history_manager
        assert len(history_manager) == 0

    def test_nonempty_history_bool(self, history_manager):
        """Should be truthy when not empty."""
        history_manager.save(text="Test", file_names=["a.opus"], model="base")
        assert history_manager
        assert len(history_manager) == 1
