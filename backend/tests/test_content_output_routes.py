"""Tests for backend.routes.content_outputs helpers and route logic."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.routes.content_outputs import _output_to_response, VALID_STATUSES


# ---------------------------------------------------------------------------
# _output_to_response helper — serialization
# ---------------------------------------------------------------------------

class TestOutputToResponseBasic:
    """Basic field serialization for _output_to_response."""

    def test_basic_fields(self, make_content_output):
        """Core fields are serialized correctly."""
        co = make_content_output(status="draft")
        result = _output_to_response(co)

        assert result["id"] == str(co.id)
        assert result["competitor_id"] == str(co.competitor_id)
        assert result["competitor_name"] == co.competitor.name
        assert result["status"] == "draft"
        assert result["version"] == 1
        assert result["content_type"] == "Competitive Battle Card"
        assert result["title"] == "Test Output"

    def test_competitor_name_from_relation(self, make_content_output, make_competitor):
        """competitor_name comes from co.competitor.name."""
        comp = make_competitor(name="Acme Corp")
        co = make_content_output(competitor=comp)
        result = _output_to_response(co)

        assert result["competitor_name"] == "Acme Corp"

    def test_no_competitor_gives_empty_name(self, make_content_output):
        """When competitor is None, competitor_name is empty string."""
        co = make_content_output()
        co.competitor = None
        result = _output_to_response(co)

        assert result["competitor_name"] == ""

    def test_timestamps_serialized(self, make_content_output):
        """created_at and updated_at are ISO-formatted strings."""
        co = make_content_output()
        result = _output_to_response(co)

        assert result["created_at"] is not None
        assert result["updated_at"] is not None
        # Should be parseable ISO strings
        datetime.fromisoformat(result["created_at"])
        datetime.fromisoformat(result["updated_at"])


class TestOutputToResponseContent:
    """Content and sections parsing in _output_to_response."""

    def test_json_content_parsed_to_sections(self, make_content_output):
        """Valid JSON dict content is parsed into sections list."""
        co = make_content_output(content='{"Overview": "Some text", "Details": "More text"}')
        result = _output_to_response(co)

        assert len(result["sections"]) == 2
        titles = [s["title"] for s in result["sections"]]
        assert "Overview" in titles
        assert "Details" in titles

    def test_non_json_content_empty_sections(self, make_content_output):
        """Non-JSON content results in empty sections list."""
        co = make_content_output(content="plain text content")
        result = _output_to_response(co)

        assert result["sections"] == []
        assert result["content"] == "plain text content"

    def test_null_content(self, make_content_output):
        """None content results in empty string and empty sections."""
        co = make_content_output(content=None)
        result = _output_to_response(co)

        assert result["content"] == ""
        assert result["sections"] == []

    def test_json_array_content_empty_sections(self, make_content_output):
        """JSON array (not dict) results in empty sections."""
        co = make_content_output(content='["a", "b"]')
        result = _output_to_response(co)

        assert result["sections"] == []


class TestOutputToResponseOptionalFields:
    """Optional field handling in _output_to_response."""

    def test_optional_fields_null(self, make_content_output):
        """All optional fields default to None when not set."""
        co = make_content_output()
        result = _output_to_response(co)

        assert result["google_doc_id"] is None
        assert result["google_doc_url"] is None
        assert result["approved_by"] is None
        assert result["approved_by_name"] is None
        assert result["approved_at"] is None
        assert result["published_at"] is None
        assert result["error_message"] is None

    def test_optional_fields_populated(self, make_content_output):
        """Optional fields are serialized when populated."""
        tid = uuid.uuid4()
        uid = uuid.uuid4()
        now = datetime.now(timezone.utc)
        approver_mock = SimpleNamespace(name="Jane Admin")
        co = make_content_output(
            template_id=tid,
            google_doc_id="doc-123",
            google_doc_url="https://docs.google.com/doc-123",
            approved_by=uid,
            approver=approver_mock,
            approved_at=now,
            published_at=now,
            error_message="some error",
        )
        result = _output_to_response(co)

        assert result["template_id"] == str(tid)
        assert result["google_doc_id"] == "doc-123"
        assert result["google_doc_url"] == "https://docs.google.com/doc-123"
        assert result["approved_by"] == str(uid)
        assert result["approved_by_name"] == "Jane Admin"
        assert result["approved_at"] is not None
        assert result["published_at"] is not None
        assert result["error_message"] == "some error"

    def test_source_card_ids_default_empty(self, make_content_output):
        """source_card_ids defaults to empty list when None."""
        co = make_content_output()
        result = _output_to_response(co)

        assert result["source_card_ids"] == []

    def test_source_card_ids_populated(self, make_content_output):
        """source_card_ids are passed through when set."""
        co = make_content_output(source_card_ids=["card-1", "card-2"])
        result = _output_to_response(co)

        assert result["source_card_ids"] == ["card-1", "card-2"]


# ---------------------------------------------------------------------------
# Route handler logic tests
# ---------------------------------------------------------------------------

class TestListContentOutputs:
    """Tests for list_content_outputs route handler."""

    def test_returns_empty_list(self, mock_db, make_user):
        """Returns empty list when no outputs exist."""
        from backend.routes.content_outputs import list_content_outputs

        mock_db.all.return_value = []
        user = make_user()

        result = list_content_outputs(
            competitor_id=None, content_type=None, status=None,
            db=mock_db, current_user=user,
        )
        assert result == []

    def test_returns_serialized_outputs(self, mock_db, make_user, make_content_output):
        """Returns serialized list of content outputs."""
        from backend.routes.content_outputs import list_content_outputs

        co = make_content_output()
        mock_db.all.return_value = [co]
        user = make_user()

        result = list_content_outputs(
            competitor_id=None, content_type=None, status=None,
            db=mock_db, current_user=user,
        )
        assert len(result) == 1
        assert result[0]["id"] == str(co.id)


class TestGetContentOutput:
    """Tests for get_content_output route handler."""

    def test_not_found_raises_404(self, mock_db, make_user):
        """Returns 404 when output not found."""
        from backend.routes.content_outputs import get_content_output

        mock_db.first.return_value = None
        user = make_user()

        with pytest.raises(Exception) as exc_info:
            get_content_output(output_id=str(uuid.uuid4()), db=mock_db, current_user=user)
        assert exc_info.value.status_code == 404

    def test_returns_output(self, mock_db, make_user, make_content_output):
        """Returns serialized output when found."""
        from backend.routes.content_outputs import get_content_output

        co = make_content_output()
        mock_db.first.return_value = co
        user = make_user()

        result = get_content_output(output_id=str(co.id), db=mock_db, current_user=user)
        assert result["id"] == str(co.id)


class TestGenerateContent:
    """Tests for generate_content route handler (synchronous)."""

    def test_competitor_not_found_raises_404(self, mock_db, make_user):
        """Returns 404 when competitor doesn't exist."""
        from backend.routes.content_outputs import generate_content, ContentOutputCreate

        mock_db.first.return_value = None
        user = make_user()
        body = ContentOutputCreate(competitor_id=str(uuid.uuid4()), template_id=str(uuid.uuid4()))

        with pytest.raises(Exception) as exc_info:
            generate_content(body=body, db=mock_db, current_user=user)
        assert exc_info.value.status_code == 404
        assert "Competitor" in exc_info.value.detail

    def test_template_not_found_raises_404(self, mock_db, make_user, make_competitor):
        """Returns 404 when template doesn't exist or is inactive."""
        from backend.routes.content_outputs import generate_content, ContentOutputCreate

        comp = make_competitor()
        # First call returns competitor, second returns None (template)
        mock_db.first.side_effect = [comp, None]
        user = make_user()
        body = ContentOutputCreate(competitor_id=str(comp.id), template_id=str(uuid.uuid4()))

        with pytest.raises(Exception) as exc_info:
            generate_content(body=body, db=mock_db, current_user=user)
        assert exc_info.value.status_code == 404
        assert "Template" in exc_info.value.detail

    @patch("backend.routes.content_outputs.ContentGenerator")
    def test_successful_generation_returns_content(self, MockGenerator, mock_db, make_user, make_competitor, make_content_template):
        """Synchronous generation returns ContentOutputResponse with content."""
        from backend.routes.content_outputs import generate_content, ContentOutputCreate

        comp = make_competitor(name="Acme")
        tmpl = make_content_template(doc_name_pattern="Battle Card - {competitor}")
        user = make_user()
        body = ContentOutputCreate(competitor_id=str(comp.id), template_id=str(tmpl.id))

        mock_gen_instance = MagicMock()
        mock_gen_instance.generate_content.return_value = {
            "content": '{"Overview": "Test"}',
            "raw_llm_output": {"model": "test"},
            "source_card_ids": ["card-1"],
            "content_type": "Competitive Battle Card",
        }
        MockGenerator.return_value = mock_gen_instance

        # Capture the ContentOutput object added to the session
        captured = {}
        def track_add(obj):
            captured["co"] = obj
            obj.competitor = comp  # attach for serialization
        mock_db.add.side_effect = track_add

        # first() calls: 1=competitor, 2=template, 3=reload with joinedload
        call_count = [0]
        def smart_first():
            call_count[0] += 1
            if call_count[0] == 1:
                return comp
            elif call_count[0] == 2:
                return tmpl
            else:
                return captured.get("co")
        mock_db.first.side_effect = smart_first

        result = generate_content(body=body, db=mock_db, current_user=user)

        assert result["status"] == "draft"
        assert result["content"] == '{"Overview": "Test"}'
        assert result["title"] == "Battle Card - Acme"

    @patch("backend.routes.content_outputs.ContentGenerator")
    def test_generation_failure_sets_failed_status(self, MockGenerator, mock_db, make_user, make_competitor, make_content_template):
        """When ContentGenerator raises, status is set to 'failed' with error_message."""
        from backend.routes.content_outputs import generate_content, ContentOutputCreate

        comp = make_competitor(name="Acme")
        tmpl = make_content_template()
        user = make_user()
        body = ContentOutputCreate(competitor_id=str(comp.id), template_id=str(tmpl.id))

        mock_gen_instance = MagicMock()
        mock_gen_instance.generate_content.side_effect = RuntimeError("LLM failed")
        MockGenerator.return_value = mock_gen_instance

        # Capture the ContentOutput object added to the session
        captured = {}
        def track_add(obj):
            captured["co"] = obj
            obj.competitor = comp
        mock_db.add.side_effect = track_add

        call_count = [0]
        def smart_first():
            call_count[0] += 1
            if call_count[0] == 1:
                return comp
            elif call_count[0] == 2:
                return tmpl
            else:
                return captured.get("co")
        mock_db.first.side_effect = smart_first

        result = generate_content(body=body, db=mock_db, current_user=user)

        assert result["status"] == "failed"
        assert "LLM failed" in result["error_message"]


class TestDeleteContentOutput:
    """Tests for delete_content_output route handler."""

    def test_successful_delete_returns_none(self, mock_db, make_user, make_content_output):
        """Successful delete returns None (204 status handled by FastAPI)."""
        from backend.routes.content_outputs import delete_content_output

        co = make_content_output()
        mock_db.first.return_value = co
        user = make_user()

        result = delete_content_output(output_id=str(co.id), db=mock_db, current_user=user)

        assert result is None
        mock_db.delete.assert_called_once_with(co)
        mock_db.commit.assert_called()

    def test_delete_not_found_raises_404(self, mock_db, make_user):
        """Returns 404 when content output not found."""
        from backend.routes.content_outputs import delete_content_output

        mock_db.first.return_value = None
        user = make_user()

        with pytest.raises(Exception) as exc_info:
            delete_content_output(output_id=str(uuid.uuid4()), db=mock_db, current_user=user)
        assert exc_info.value.status_code == 404

    def test_delete_requires_auth(self):
        """Delete endpoint requires authentication (get_current_user dependency).

        This is verified by the function signature having current_user: User = Depends(get_current_user).
        Without a valid user, FastAPI will return 401 before the handler runs.
        """
        from backend.routes.content_outputs import delete_content_output
        import inspect
        sig = inspect.signature(delete_content_output)
        param_names = list(sig.parameters.keys())
        assert "current_user" in param_names


class TestUpdateContentOutput:
    """Tests for update_content_output route handler."""

    def test_not_found_raises_404(self, mock_db, make_user):
        """Returns 404 when output not found."""
        from backend.routes.content_outputs import update_content_output, ContentOutputUpdate

        mock_db.first.return_value = None
        user = make_user()
        body = ContentOutputUpdate(title="New Title")

        with pytest.raises(Exception) as exc_info:
            update_content_output(output_id=str(uuid.uuid4()), body=body, db=mock_db, current_user=user)
        assert exc_info.value.status_code == 404


class TestUpdateContentOutputStatus:
    """Tests for update_content_output_status route handler."""

    def test_invalid_status_raises_400(self, mock_db, make_user):
        """Returns 400 for invalid status value."""
        from backend.routes.content_outputs import update_content_output_status, StatusUpdate

        user = make_user()
        body = StatusUpdate(status="invalid_status")

        with pytest.raises(Exception) as exc_info:
            update_content_output_status(
                output_id=str(uuid.uuid4()), body=body,
                db=mock_db, current_user=user,
            )
        assert exc_info.value.status_code == 400

    def test_not_found_raises_404(self, mock_db, make_user):
        """Returns 404 when output not found."""
        from backend.routes.content_outputs import update_content_output_status, StatusUpdate

        mock_db.first.return_value = None
        user = make_user()
        body = StatusUpdate(status="in_review")

        with pytest.raises(Exception) as exc_info:
            update_content_output_status(
                output_id=str(uuid.uuid4()), body=body,
                db=mock_db, current_user=user,
            )
        assert exc_info.value.status_code == 404

    def test_approval_requires_admin(self, mock_db, make_user, make_content_output):
        """Non-admin user gets 403 when trying to approve."""
        from backend.routes.content_outputs import update_content_output_status, StatusUpdate

        co = make_content_output(status="in_review")
        mock_db.first.return_value = co
        user = make_user(role="viewer")
        body = StatusUpdate(status="approved")

        with pytest.raises(Exception) as exc_info:
            update_content_output_status(
                output_id=str(co.id), body=body,
                db=mock_db, current_user=user,
            )
        assert exc_info.value.status_code == 403

    def test_admin_approval_sets_fields_no_auto_publish(self, mock_db, make_user, make_content_output):
        """Admin approval sets approved_by and approved_at but does NOT trigger auto-publish."""
        from backend.routes.content_outputs import update_content_output_status, StatusUpdate

        co = make_content_output(status="in_review")
        mock_db.first.return_value = co
        admin = make_user(role="admin")
        body = StatusUpdate(status="approved")

        result = update_content_output_status(
            output_id=str(co.id), body=body,
            db=mock_db, current_user=admin,
        )

        assert co.approved_by == admin.id
        assert co.approved_at is not None
        assert co.status == "approved"

    def test_non_approval_status_change(self, mock_db, make_user, make_content_output):
        """Non-approval status change works without admin."""
        from backend.routes.content_outputs import update_content_output_status, StatusUpdate

        co = make_content_output(status="draft")
        mock_db.first.return_value = co
        user = make_user(role="viewer")
        body = StatusUpdate(status="in_review")

        result = update_content_output_status(
            output_id=str(co.id), body=body,
            db=mock_db, current_user=user,
        )

        assert co.status == "in_review"


class TestPublishContentOutput:
    """Tests for publish_content_output route handler."""

    def test_publish_requires_admin(self, mock_db, make_user):
        """Non-admin user gets 403 when trying to publish."""
        from backend.routes.content_outputs import publish_content_output

        user = make_user(role="viewer")

        with pytest.raises(Exception) as exc_info:
            publish_content_output(output_id=str(uuid.uuid4()), db=mock_db, current_user=user)
        assert exc_info.value.status_code == 403

    def test_publish_not_found_raises_404(self, mock_db, make_user):
        """Returns 404 when content output not found."""
        from backend.routes.content_outputs import publish_content_output

        mock_db.first.return_value = None
        admin = make_user(role="admin")
        admin.google_refresh_token = "token"

        with pytest.raises(Exception) as exc_info:
            publish_content_output(output_id=str(uuid.uuid4()), db=mock_db, current_user=admin)
        assert exc_info.value.status_code == 404

    def test_publish_requires_approved_status(self, mock_db, make_user, make_content_output):
        """Returns 400 when content output is not approved."""
        from backend.routes.content_outputs import publish_content_output

        co = make_content_output(status="draft")
        mock_db.first.return_value = co
        admin = make_user(role="admin")
        admin.google_refresh_token = "token"

        with pytest.raises(Exception) as exc_info:
            publish_content_output(output_id=str(co.id), db=mock_db, current_user=admin)
        assert exc_info.value.status_code == 400
        assert "approved" in exc_info.value.detail.lower()

    def test_publish_requires_google_credentials(self, mock_db, make_user, make_content_output):
        """Returns 400 when user has no Google credentials."""
        from backend.routes.content_outputs import publish_content_output

        co = make_content_output(status="approved")
        mock_db.first.return_value = co
        admin = make_user(role="admin")
        admin.google_refresh_token = None

        with pytest.raises(Exception) as exc_info:
            publish_content_output(output_id=str(co.id), db=mock_db, current_user=admin)
        assert exc_info.value.status_code == 400
        assert "Google credentials" in exc_info.value.detail

    @patch("backend.services.google_docs_service.GoogleDocsService")
    def test_publish_success(self, MockService, mock_db, make_user, make_content_output):
        """Successful publish calls GoogleDocsService.publish_doc."""
        from backend.routes.content_outputs import publish_content_output

        co = make_content_output(status="approved")
        mock_db.first.return_value = co
        admin = make_user(role="admin")
        admin.google_refresh_token = "token"

        mock_svc = MagicMock()
        MockService.return_value = mock_svc

        result = publish_content_output(output_id=str(co.id), db=mock_db, current_user=admin)
        mock_svc.publish_doc.assert_called_once_with(mock_db, co, admin)

    @patch("backend.services.google_docs_service.GoogleDocsService")
    def test_publish_failure_keeps_approved_status(self, MockService, mock_db, make_user, make_content_output):
        """When publish fails, status stays 'approved' and error_message is set."""
        from backend.routes.content_outputs import publish_content_output

        co = make_content_output(status="approved")
        mock_db.first.return_value = co
        admin = make_user(role="admin")
        admin.google_refresh_token = "token"

        mock_svc = MagicMock()
        mock_svc.publish_doc.side_effect = RuntimeError("API error")
        MockService.return_value = mock_svc

        result = publish_content_output(output_id=str(co.id), db=mock_db, current_user=admin)

        assert co.status == "approved"
        assert "API error" in co.error_message

