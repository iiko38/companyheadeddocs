import base64
import io
import logging
import uuid

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from llm_extractor import extract_meeting_model
from models import MeetingMeta, MeetingModel
from renderer import render_docx
from template_registry import get_template
from transcript_loader import load_transcript

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


app = FastAPI(title="Meeting Transcript to DOCX")


class TransformResponse(JSONResponse):
    media_type = "application/json"

    def __init__(self, *, request_id: str, minutes: MeetingModel, docx_bytes: bytes):
        content = {
            "request_id": request_id,
            "minutes": minutes.model_dump(),
            "docx_base64": base64.b64encode(docx_bytes).decode("ascii"),
        }
        super().__init__(content=content)


@app.post("/transform")
async def transform(
    template_id: str = Form(...),
    project: str = Form(...),
    job_min_no: str = Form(...),
    description: str = Form("Progress Meeting"),
    date: str = Form(...),
    time: str = Form(...),
    location: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Transform a transcript file + meeting metadata into structured minutes
    and a company-headed DOCX, returned as base64 in JSON.
    """
    request_id = str(uuid.uuid4())
    template = get_template(template_id)

    file_bytes = await file.read()
    text = load_transcript(file_bytes, file.filename)

    meta = MeetingMeta(
        project=project,
        job_min_no=job_min_no,
        description=description,
        date=date,
        time=time,
        location=location,
    )

    meeting = extract_meeting_model(text, meta, template)
    docx_bytes = render_docx(template, meeting)

    return TransformResponse(request_id=request_id, minutes=meeting, docx_bytes=docx_bytes)


@app.post("/transform/download")
async def transform_download(
    template_id: str = Form(...),
    project: str = Form(...),
    job_min_no: str = Form(...),
    description: str = Form("Progress Meeting"),
    date: str = Form(...),
    time: str = Form(...),
    location: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Transform a transcript file + meeting metadata into structured minutes
    and a company-headed DOCX, returned as a file download.
    """
    template = get_template(template_id)

    file_bytes = await file.read()
    text = load_transcript(file_bytes, file.filename)

    meta = MeetingMeta(
        project=project,
        job_min_no=job_min_no,
        description=description,
        date=date,
        time=time,
        location=location,
    )

    meeting = extract_meeting_model(text, meta, template)
    docx_bytes = render_docx(template, meeting)

    filename = f"meeting_minutes_{meeting.meta.date.replace('/', '-')}.docx"
    return StreamingResponse(
        content=io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/health")
async def health() -> dict:
    """
    Health check endpoint returning service status.
    Validates basic configuration and template availability.
    """
    from config import settings

    # Validate settings can be instantiated and have required fields
    _ = settings.openai_api_key
    _ = settings.openai_model

    # Validate default template can be loaded
    _ = get_template("progress_minutes_v1")

    return {"status": "ok"}
