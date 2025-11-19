from pathlib import Path
import tempfile

from docx import Document
from fastapi import HTTPException


SUPPORTED_EXTENSIONS = {"docx", "vtt", "txt", "text"}


def load_transcript(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if ext == "docx":
        return _extract_docx(file_bytes)
    if ext == "vtt":
        return _extract_vtt(file_bytes)
    return file_bytes.decode("utf-8", errors="ignore")


def _extract_docx(file_bytes: bytes) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "upload.docx"
        tmp_path.write_bytes(file_bytes)
        document = Document(tmp_path)
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)


def _extract_vtt(file_bytes: bytes) -> str:
    text = file_bytes.decode("utf-8", errors="ignore")
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if "-->" in line:
            continue
        if line.replace(".", "").isdigit():
            continue
        lines.append(line)
    return "\n".join(lines)
