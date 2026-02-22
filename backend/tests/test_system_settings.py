"""Tests for KV settings endpoints in backend.routes.system."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.routes.system import get_kv_setting, upsert_kv_setting, KVSettingUpdate


# ---------------------------------------------------------------------------
# get_kv_setting
# ---------------------------------------------------------------------------

class TestGetKVSetting:
    """Tests for get_kv_setting route handler."""

    def test_key_not_found_returns_none_value(self, mock_db):
        """Returns {key, None} when key doesn't exist in DB."""
        mock_db.first.return_value = None

        result = get_kv_setting(key="missing_key", db=mock_db)

        assert result == {"key": "missing_key", "value": None}

    def test_key_found_returns_value(self, mock_db):
        """Returns {key, value} when key exists in DB."""
        setting = SimpleNamespace(key="my_key", value="my_value")
        mock_db.first.return_value = setting

        result = get_kv_setting(key="my_key", db=mock_db)

        assert result == {"key": "my_key", "value": "my_value"}


# ---------------------------------------------------------------------------
# upsert_kv_setting
# ---------------------------------------------------------------------------

class TestUpsertKVSetting:
    """Tests for upsert_kv_setting route handler."""

    def test_creates_new_setting(self, mock_db):
        """Creates a new setting when key doesn't exist."""
        mock_db.first.return_value = None

        # After commit+refresh, the setting object should have key/value
        created_setting = SimpleNamespace(key="new_key", value="new_value")
        mock_db.refresh.side_effect = lambda obj: None

        body = KVSettingUpdate(value="new_value")

        # We need to capture what gets added and mock refresh to return it
        added_objects = []
        original_add = mock_db.add

        def capture_add(obj):
            added_objects.append(obj)
        mock_db.add.side_effect = capture_add

        def fake_refresh(obj):
            obj.key = "new_key"
            obj.value = "new_value"
        mock_db.refresh.side_effect = fake_refresh

        result = upsert_kv_setting(key="new_key", body=body, db=mock_db)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result["key"] == "new_key"
        assert result["value"] == "new_value"

    def test_updates_existing_setting(self, mock_db):
        """Updates value when key already exists."""
        existing = SimpleNamespace(key="existing_key", value="old_value")
        mock_db.first.return_value = existing

        body = KVSettingUpdate(value="updated_value")

        result = upsert_kv_setting(key="existing_key", body=body, db=mock_db)

        assert existing.value == "updated_value"
        mock_db.commit.assert_called_once()
        mock_db.add.assert_not_called()
        assert result["key"] == "existing_key"
        assert result["value"] == "updated_value"

    def test_upsert_with_none_value(self, mock_db):
        """Can set value to None."""
        existing = SimpleNamespace(key="some_key", value="has_value")
        mock_db.first.return_value = existing

        body = KVSettingUpdate(value=None)

        result = upsert_kv_setting(key="some_key", body=body, db=mock_db)

        assert existing.value is None
        assert result["key"] == "some_key"
        assert result["value"] is None

