"""Tests for backend.routes.content_templates helpers and route logic."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.routes.content_templates import _template_to_response


# ---------------------------------------------------------------------------
# _template_to_response helper — serialization
# ---------------------------------------------------------------------------

class TestTemplateToResponseBasic:
    """Basic field serialization for _template_to_response."""

    def test_basic_fields(self, make_content_template):
        """Core fields are serialized correctly."""
        t = make_content_template(
            content_type="Battle Card",
            name="BC Template",
            description="A battle card template",
        )
        result = _template_to_response(t)

        assert result["id"] == str(t.id)
        assert result["content_type"] == "Battle Card"
        assert result["name"] == "BC Template"
        assert result["description"] == "A battle card template"
        assert result["is_active"] is True

    def test_timestamps_serialized(self, make_content_template):
        """created_at and updated_at are ISO-formatted strings."""
        t = make_content_template()
        result = _template_to_response(t)

        assert result["created_at"] is not None
        assert result["updated_at"] is not None
        datetime.fromisoformat(result["created_at"])
        datetime.fromisoformat(result["updated_at"])

    def test_null_sections_empty_list(self, make_content_template):
        """Null sections results in empty list."""
        t = make_content_template(sections=None)
        result = _template_to_response(t)

        assert result["sections"] == []

    def test_sections_passed_through(self, make_content_template):
        """Non-empty sections are passed through."""
        sections = [
            {"title": "Overview", "description": "Overview section", "prompt_hint": ""},
            {"title": "Strengths", "description": "Key strengths", "prompt_hint": ""},
        ]
        t = make_content_template(sections=sections)
        result = _template_to_response(t)

        assert result["sections"] == sections
        assert len(result["sections"]) == 2

    def test_doc_name_pattern(self, make_content_template):
        """doc_name_pattern is serialized when set."""
        t = make_content_template(doc_name_pattern="Battle Card - {competitor}")
        result = _template_to_response(t)

        assert result["doc_name_pattern"] == "Battle Card - {competitor}"

    def test_doc_name_pattern_null(self, make_content_template):
        """doc_name_pattern is None when not set."""
        t = make_content_template(doc_name_pattern=None)
        result = _template_to_response(t)

        assert result["doc_name_pattern"] is None

    def test_inactive_template(self, make_content_template):
        """is_active=False is serialized correctly."""
        t = make_content_template(is_active=False)
        result = _template_to_response(t)

        assert result["is_active"] is False


# ---------------------------------------------------------------------------
# Route handler logic tests
# ---------------------------------------------------------------------------

class TestListTemplates:
    """Tests for list_templates route handler."""

    def test_returns_empty_list(self, mock_db):
        """Returns empty list when no templates exist."""
        from backend.routes.content_templates import list_templates

        mock_db.all.return_value = []
        result = list_templates(db=mock_db)
        assert result == []

    def test_returns_serialized_templates(self, mock_db, make_content_template):
        """Returns serialized list of templates."""
        from backend.routes.content_templates import list_templates

        t = make_content_template()
        mock_db.all.return_value = [t]
        result = list_templates(db=mock_db)
        assert len(result) == 1
        assert result[0]["id"] == str(t.id)


class TestGetTemplate:
    """Tests for get_template route handler."""

    def test_not_found_raises_404(self, mock_db):
        """Returns 404 when template not found."""
        from backend.routes.content_templates import get_template

        mock_db.first.return_value = None
        with pytest.raises(Exception) as exc_info:
            get_template(template_id=str(uuid.uuid4()), db=mock_db)
        assert exc_info.value.status_code == 404

    def test_returns_template(self, mock_db, make_content_template):
        """Returns serialized template when found."""
        from backend.routes.content_templates import get_template

        t = make_content_template()
        mock_db.first.return_value = t
        result = get_template(template_id=str(t.id), db=mock_db)
        assert result["id"] == str(t.id)




class TestCreateTemplate:
    """Tests for create_template route handler."""

    def test_non_admin_raises_403(self, mock_db, make_user):
        """Non-admin user gets 403."""
        from backend.routes.content_templates import create_template, TemplateCreate

        user = make_user(role="viewer")
        body = TemplateCreate(content_type="Battle Card", name="BC Template")

        with pytest.raises(Exception) as exc_info:
            create_template(body=body, db=mock_db, current_user=user)
        assert exc_info.value.status_code == 403

    def test_duplicate_content_type_raises_409(self, mock_db, make_user, make_content_template):
        """Duplicate content_type returns 409."""
        from backend.routes.content_templates import create_template, TemplateCreate

        existing = make_content_template(content_type="Battle Card")
        mock_db.first.return_value = existing
        admin = make_user(role="admin")
        body = TemplateCreate(content_type="Battle Card", name="Another BC")

        with pytest.raises(Exception) as exc_info:
            create_template(body=body, db=mock_db, current_user=admin)
        assert exc_info.value.status_code == 409

    def test_admin_creates_template(self, mock_db, make_user):
        """Admin can create a template successfully."""
        from backend.routes.content_templates import create_template, TemplateCreate

        mock_db.first.return_value = None  # No duplicate
        admin = make_user(role="admin")
        body = TemplateCreate(content_type="Battle Card", name="BC Template")

        # mock refresh to set timestamps on the created object
        def fake_refresh(obj):
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)
        mock_db.refresh.side_effect = fake_refresh

        result = create_template(body=body, db=mock_db, current_user=admin)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestUpdateTemplate:
    """Tests for update_template route handler."""

    def test_non_admin_raises_403(self, mock_db, make_user):
        """Non-admin user gets 403."""
        from backend.routes.content_templates import update_template, TemplateUpdate

        user = make_user(role="viewer")
        body = TemplateUpdate(name="Updated Name")

        with pytest.raises(Exception) as exc_info:
            update_template(template_id=str(uuid.uuid4()), body=body, db=mock_db, current_user=user)
        assert exc_info.value.status_code == 403

    def test_not_found_raises_404(self, mock_db, make_user):
        """Returns 404 when template not found."""
        from backend.routes.content_templates import update_template, TemplateUpdate

        mock_db.first.return_value = None
        admin = make_user(role="admin")
        body = TemplateUpdate(name="Updated Name")

        with pytest.raises(Exception) as exc_info:
            update_template(template_id=str(uuid.uuid4()), body=body, db=mock_db, current_user=admin)
        assert exc_info.value.status_code == 404

    def test_admin_updates_template(self, mock_db, make_user, make_content_template):
        """Admin can update a template successfully."""
        from backend.routes.content_templates import update_template, TemplateUpdate

        t = make_content_template(name="Old Name")
        mock_db.first.return_value = t
        admin = make_user(role="admin")
        body = TemplateUpdate(name="New Name")

        result = update_template(template_id=str(t.id), body=body, db=mock_db, current_user=admin)
        assert t.name == "New Name"
        mock_db.commit.assert_called_once()


class TestDeleteTemplate:
    """Tests for delete_template route handler."""

    def test_non_admin_raises_403(self, mock_db, make_user):
        """Non-admin user gets 403."""
        from backend.routes.content_templates import delete_template

        user = make_user(role="viewer")

        with pytest.raises(Exception) as exc_info:
            delete_template(template_id=str(uuid.uuid4()), db=mock_db, current_user=user)
        assert exc_info.value.status_code == 403

    def test_not_found_raises_404(self, mock_db, make_user):
        """Returns 404 when template not found."""
        from backend.routes.content_templates import delete_template

        mock_db.first.return_value = None
        admin = make_user(role="admin")

        with pytest.raises(Exception) as exc_info:
            delete_template(template_id=str(uuid.uuid4()), db=mock_db, current_user=admin)
        assert exc_info.value.status_code == 404

    def test_soft_deletes_template(self, mock_db, make_user, make_content_template):
        """Admin soft-deletes by setting is_active=False."""
        from backend.routes.content_templates import delete_template

        t = make_content_template(is_active=True)
        mock_db.first.return_value = t
        admin = make_user(role="admin")

        result = delete_template(template_id=str(t.id), db=mock_db, current_user=admin)
        assert t.is_active is False
        assert result["ok"] is True
        assert result["id"] == str(t.id)
        mock_db.commit.assert_called_once()