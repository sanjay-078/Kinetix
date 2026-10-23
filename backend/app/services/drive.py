"""Google Drive storage for original PDF bytes only.

Never parse, OCR, summarize, vectorize, embed or inspect PDF content here.
"""

import io
import os

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from app.config import settings


def upload_original_pdf(credentials, filename: str, pdf_bytes: bytes) -> dict:
    """Store the untouched attachment in the owner's Google Drive."""
    if credentials is None or not getattr(credentials, "valid", False):
        raise RuntimeError("An authorized Google Drive connection is required")
    if not isinstance(pdf_bytes, (bytes, bytearray)) or not pdf_bytes:
        raise ValueError("Missing original PDF attachment bytes")

    # A supplier-provided filename is metadata, not a filesystem path.
    name = os.path.basename(filename.replace("\\", "/")) or "catalogue.pdf"
    metadata = {"name": name, "mimeType": "application/pdf"}
    if settings.GOOGLE_DRIVE_FOLDER_ID:
        metadata["parents"] = [settings.GOOGLE_DRIVE_FOLDER_ID]

    service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    media = MediaIoBaseUpload(
        io.BytesIO(pdf_bytes), mimetype="application/pdf", resumable=True
    )
    uploaded = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,webViewLink",
    ).execute()
    file_id = uploaded.get("id")
    if not file_id:
        raise RuntimeError("Google Drive did not return a stored file ID")

    return {
        "drive_file_id": file_id,
        "web_view_link": uploaded.get("webViewLink")
        or f"https://drive.google.com/file/d/{file_id}/view",
        "file_size": len(pdf_bytes),
        "filename": filename,
        "mime_type": "application/pdf",
    }
