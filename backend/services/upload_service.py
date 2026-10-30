"""Validate text uploads and assign trusted, owner-only document metadata."""
import uuid
from pathlib import PurePosixPath

from backend import api_error_message


class UploadService:
    MAX_BYTES = 1024 * 1024
    EXTENSIONS = frozenset({".txt", ".md"})

    def build_document(self, owner_id: str, filename: str, data: bytes) -> dict:
        if not filename or len(filename) > 200 or any(
            ord(char) < 32 or ord(char) == 127 or char in "/\\" for char in filename
        ):
            raise ValueError(api_error_message.UPLOAD_FILENAME_INVALID)
        if PurePosixPath(filename).suffix.lower() not in self.EXTENSIONS:
            raise ValueError(api_error_message.UPLOAD_TYPE_INVALID)
        if len(data) > self.MAX_BYTES:
            raise ValueError(api_error_message.UPLOAD_TOO_LARGE)
        try:
            content = data.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError(api_error_message.UPLOAD_TEXT_INVALID) from error
        if not content.strip() or any(ord(char) < 32 and char not in "\n\r\t" for char in content):
            raise ValueError(api_error_message.UPLOAD_TEXT_INVALID)
        return {
            "id": "upload-" + uuid.uuid4().hex,
            "title": filename,
            "document_type": "personal_upload",
            "classification": "PRIVATE · UPLOAD",
            "owner_id": owner_id,
            "content": content,
            "tags": ["upload"],
        }
