"""Google Docs service — creates and updates Google Docs from content outputs using user OAuth credentials."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GoogleDocsService:
    """Creates/updates Google Docs from content output data using per-user OAuth credentials."""

    def publish_doc(
        self,
        db: Session,
        content_output: Any,
        user: Any,
    ) -> None:
        """Create or update a Google Doc for the content output.

        Raises an exception if credentials are missing or publish fails.
        Sets google_doc_id, google_doc_url, published_at, and status on success.
        Does NOT set status on failure — caller handles that.
        """
        credentials = self._build_credentials(user)
        if credentials is None:
            raise ValueError("Google credentials not configured. Please re-authenticate.")

        from googleapiclient.discovery import build

        docs_service = build("docs", "v1", credentials=credentials)
        drive_service = build("drive", "v3", credentials=credentials)

        sections = self._parse_content(content_output.content)
        title = content_output.title or "Untitled Content"

        if content_output.google_doc_id:
            self._update_existing_doc(docs_service, content_output.google_doc_id, title, sections)
            logger.info("Updated existing Google Doc: %s", content_output.google_doc_id)
        else:
            doc_id, doc_url = self._create_new_doc(
                docs_service, drive_service, title, sections, db
            )
            content_output.google_doc_id = doc_id
            content_output.google_doc_url = doc_url
            logger.info("Created new Google Doc: %s", doc_id)

        content_output.status = "published"
        content_output.published_at = datetime.now(timezone.utc)
        db.commit()

    def _build_credentials(self, user: Any):
        """Build Google OAuth credentials from user's stored tokens.

        Returns None if no refresh token is available.
        """
        if not user.google_refresh_token:
            logger.warning("No Google refresh token for user %s", user.id)
            return None

        try:
            from google.oauth2.credentials import Credentials
            from backend.config import settings

            credentials = Credentials(
                token=user.google_access_token,
                refresh_token=user.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=[
                    "https://www.googleapis.com/auth/drive.file",
                    "https://www.googleapis.com/auth/documents",
                ],
            )
            return credentials
        except Exception as e:
            logger.error("Failed to build Google credentials: %s", e)
            return None

    def _parse_content(self, content: str) -> list[dict[str, str]]:
        """Parse content JSON into a list of {title, body} sections."""
        try:
            data = json.loads(content) if isinstance(content, str) else content
            if isinstance(data, dict):
                return [{"title": k, "body": v} for k, v in data.items()]
            return []
        except (json.JSONDecodeError, TypeError):
            return [{"title": "Content", "body": str(content)}]

    def _create_new_doc(
        self,
        docs_service: Any,
        drive_service: Any,
        title: str,
        sections: list[dict[str, str]],
        db: Session,
    ) -> tuple[str, str]:
        """Create a new Google Doc and return (doc_id, doc_url)."""
        # Create the document
        doc = docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        # Move to folder if configured
        folder_id = self._get_folder_id(db)
        if folder_id:
            try:
                drive_service.files().update(
                    fileId=doc_id,
                    addParents=folder_id,
                    fields="id, parents",
                ).execute()
            except Exception as e:
                logger.warning("Failed to move doc to folder %s: %s", folder_id, e)

        # Write content
        requests = self._build_doc_requests(sections)
        if requests:
            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()

        return doc_id, doc_url



    def _update_existing_doc(
        self,
        docs_service: Any,
        doc_id: str,
        title: str,
        sections: list[dict[str, str]],
    ) -> None:
        """Clear and rewrite an existing Google Doc (preserves URL/sharing)."""
        # Get current doc to find content length
        doc = docs_service.documents().get(documentId=doc_id).execute()
        body_content = doc.get("body", {}).get("content", [])

        # Calculate end index (last element's endIndex minus 1 to keep the trailing newline)
        end_index = 1
        if body_content:
            last_element = body_content[-1]
            end_index = last_element.get("endIndex", 1) - 1

        requests = []

        # Clear existing content (if any beyond the initial newline)
        if end_index > 1:
            requests.append({
                "deleteContentRange": {
                    "range": {"startIndex": 1, "endIndex": end_index}
                }
            })

        # Write new content
        content_requests = self._build_doc_requests(sections)
        requests.extend(content_requests)

        if requests:
            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()

    def _build_doc_requests(self, sections: list[dict[str, str]]) -> list[dict]:
        """Build Google Docs API requests to insert section content.

        Inserts in reverse order at index 1 so sections appear in correct order.
        """
        if not sections:
            return []

        requests = []
        # We insert at index 1, building content from last section to first
        for section in reversed(sections):
            title = section.get("title", "")
            body = section.get("body", "")

            # Insert body text first (will be pushed down by title)
            if body:
                body_text = body.strip() + "\n\n"
                requests.append({
                    "insertText": {"location": {"index": 1}, "text": body_text}
                })

            # Insert section heading
            if title:
                heading_text = title + "\n"
                requests.append({
                    "insertText": {"location": {"index": 1}, "text": heading_text}
                })
                # Apply heading style
                requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": 1, "endIndex": 1 + len(heading_text)},
                        "paragraphStyle": {"namedStyleType": "HEADING_2"},
                        "fields": "namedStyleType",
                    }
                })

        return requests

    def _get_folder_id(self, db: Session) -> str | None:
        """Get the Google Drive folder ID from system settings."""
        try:
            from backend.models.system_setting import SystemSetting
            setting = db.query(SystemSetting).filter(
                SystemSetting.key == "GOOGLE_DRIVE_FOLDER_ID"
            ).first()
            return setting.value if setting else None
        except Exception:
            # SystemSetting table may not exist yet
            return None