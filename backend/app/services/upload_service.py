from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZipFile, is_zipfile

from fastapi import UploadFile

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_UPLOAD_TYPES = {
    ".pdf": {"application/pdf"},
    ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".xls": {"application/vnd.ms-excel", "application/octet-stream"},
    ".doc": {"application/msword", "application/octet-stream"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".txt": {"text/plain"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
}
PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_ROOT = PROJECT_ROOT / ".uploads"


def sanitize_submission_id(submission_id: str) -> str:
    candidate = str(submission_id).strip()
    if not candidate or candidate in {".", ".."} or ".." in candidate:
        raise ValueError("Invalid submission reference.")
    if "/" in candidate or "\\" in candidate:
        raise ValueError("Invalid submission reference.")
    return candidate


def _safe_filename(filename: str) -> str:
    candidate = Path(filename).name
    if not candidate or candidate in {".", ".."}:
        raise ValueError("Invalid filename.")
    if "/" in candidate or "\\" in candidate:
        raise ValueError("Invalid filename.")
    return candidate


def _validate_file_signature(suffix: str, content: bytes) -> None:
    signatures = {
        ".pdf": content.startswith(b"%PDF-"),
        ".jpg": content.startswith(b"\xff\xd8\xff"),
        ".jpeg": content.startswith(b"\xff\xd8\xff"),
        ".png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        ".xls": content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
        ".doc": content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
    }
    if suffix in signatures and not signatures[suffix]:
        raise ValueError("File content does not match its extension.")
    if suffix in {".xlsx", ".docx"}:
        required_member = "xl/workbook.xml" if suffix == ".xlsx" else "word/document.xml"
        try:
            if not is_zipfile(BytesIO(content)):
                raise ValueError("File content does not match its extension.")
            with ZipFile(BytesIO(content)) as archive:
                if required_member not in archive.namelist():
                    raise ValueError("File content does not match its extension.")
        except BadZipFile as exc:
            raise ValueError("File content does not match its extension.") from exc
    if suffix in {".csv", ".txt"} and b"\x00" in content:
        raise ValueError("Text file content contains binary data.")


async def save_uploaded_file(submission_id: str, upload: UploadFile) -> dict[str, object]:
    safe_submission_id = sanitize_submission_id(submission_id)

    if upload.filename is None:
        raise ValueError("A file is required.")

    safe_name = _safe_filename(upload.filename)
    if len(safe_name) > 255:
        raise ValueError("Filename must be at most 255 characters.")
    content_type = upload.content_type or "application/octet-stream"
    if len(content_type) > 150:
        raise ValueError("Content type is too long.")
    suffix = Path(safe_name).suffix.lower()
    allowed_types = ALLOWED_UPLOAD_TYPES.get(suffix)
    if allowed_types is None or content_type.lower() not in allowed_types:
        raise ValueError("File extension and content type are not allowed.")
    content = bytearray()
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            break
        if len(content) + len(chunk) > MAX_UPLOAD_BYTES:
            raise ValueError("File exceeds the 25 MB limit.")
        content.extend(chunk)

    if not content:
        raise ValueError("Uploaded file is empty.")
    _validate_file_signature(suffix, bytes(content))

    upload_root = UPLOAD_ROOT.resolve()
    target_dir = (upload_root / safe_submission_id).resolve()
    if not target_dir.is_relative_to(upload_root):
        raise ValueError("Invalid submission reference.")
    target_dir.mkdir(parents=True, exist_ok=True)

    digest = sha256(content).hexdigest()
    name_without_ext = Path(safe_name).stem
    stored_name = f"{name_without_ext}-{digest[:12]}-{uuid4().hex}{suffix}"
    target_path = target_dir / stored_name

    try:
        with target_path.open("xb") as fp:
            fp.write(content)
    except OSError:
        target_path.unlink(missing_ok=True)
        raise

    return {
        "submission_id": safe_submission_id,
        "original_filename": safe_name,
        "stored_path": str(target_path.relative_to(upload_root)),
        "content_type": content_type,
        "file_size_bytes": len(content),
        "checksum_sha256": digest,
    }
