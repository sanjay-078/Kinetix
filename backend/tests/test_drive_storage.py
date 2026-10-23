"""Tests that production Drive storage uploads only untouched original bytes."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import drive


def test_drive_upload_preserves_original_bytes_and_creates_private_file(monkeypatch):
    original = b"%PDF-1.4\noriginal attachment bytes\n%%EOF"
    captured = {}

    def media_builder(stream, mimetype, resumable):
        captured["uploaded_bytes"] = stream.read()
        captured["mime_type"] = mimetype
        captured["resumable"] = resumable
        return object()

    fake_api = MagicMock()
    fake_api.files.return_value.create.return_value.execute.return_value = {
        "id": "real-google-file-id",
        "webViewLink": "https://drive.google.com/file/d/real-google-file-id/view",
    }
    monkeypatch.setattr(drive, "build", lambda *args, **kwargs: fake_api)
    monkeypatch.setattr(drive, "MediaIoBaseUpload", media_builder)

    result = drive.upload_original_pdf(
        SimpleNamespace(valid=True), "supplier.pdf", original
    )
    assert captured["uploaded_bytes"] == original
    assert captured["mime_type"] == "application/pdf"
    assert captured["resumable"] is True
    assert result["drive_file_id"] == "real-google-file-id"
    assert result["file_size"] == len(original)
    assert result["web_view_link"].startswith("https://drive.google.com/")


def test_drive_upload_rejects_missing_original_bytes():
    with pytest.raises(ValueError, match="Missing original"):
        drive.upload_original_pdf(SimpleNamespace(valid=True), "missing.pdf", b"")


def test_drive_upload_rejects_unconnected_account():
    with pytest.raises(RuntimeError, match="authorized Google Drive"):
        drive.upload_original_pdf(None, "supplier.pdf", b"%PDF-1.4")
