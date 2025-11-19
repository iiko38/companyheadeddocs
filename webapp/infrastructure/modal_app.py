import base64
import io
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, Any

import modal
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv

# Modal app definition
app = modal.App("companyheadeddocs")

# Create FastAPI app with CORS
web_app = FastAPI()
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the Modal image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install([
        "fastapi",
        "uvicorn[standard]",
        "pydantic>=2,<3",
        "pydantic-settings",
        "python-docx",
        "docxtpl",
        "openai>=1.30.0",
        "python-multipart",
        "python-dotenv",
    ])
    .env({
        k: v for k, v in {
            "AZURE_OPENAI_API_KEY": os.environ.get("AZURE_OPENAI_API_KEY"),
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
            "AZURE_OPENAI_MODEL": os.environ.get("AZURE_OPENAI_MODEL", "gpt-5-mini"),
            "OPENAI_MODEL": os.environ.get("OPENAI_MODEL", "gpt-5-mini"),
            "AZURE_OPENAI_ENDPOINT": os.environ.get("AZURE_OPENAI_ENDPOINT"),
            "AZURE_OPENAI_BASE_URL": os.environ.get("AZURE_OPENAI_BASE_URL"),
            "OPENAI_BASE_URL": os.environ.get("OPENAI_BASE_URL"),
            "OPENAI_TEMPERATURE": os.environ.get("OPENAI_TEMPERATURE"),
        }.items() if v is not None and v != ""
    })
    .add_local_dir(".", "/root", ignore=["__pycache__", "*.pyc", ".git", "webapp", "out"])
)

# Volume for persistent storage if needed
volume = modal.Volume.from_name("companyheadeddocs-data", create_if_missing=True)


class TransformResponse(JSONResponse):
    media_type = "application/json"

    def __init__(self, *, request_id: str, minutes: Dict[str, Any], docx_base64: str):
        content = {
            "request_id": request_id,
            "minutes": minutes,
            "docx_base64": docx_base64,
        }
        super().__init__(content=content)


@web_app.post("/transform")
async def transform_web(
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
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info(f"Starting transform request for project: {project}")

    try:
        # Call the processing function
        logger.info("Calling process_transcript function")
        result = process_transcript.remote(
            template_id=template_id,
            project=project,
            job_min_no=job_min_no,
            description=description,
            date=date,
            time=time,
            location=location,
            file_content=file.file.read(),
            filename=file.filename,
        )

        logger.info(f"Process completed, result keys: {list(result.keys()) if result else 'None'}")

        if not result or "docx_base64" not in result:
            logger.error(f"Invalid result from process_transcript: {result}")
            return {"error": "Processing failed - no result returned"}

        request_id = str(uuid.uuid4())
        response_data = {
            "request_id": request_id,
            "minutes": result["minutes"],
            "docx_base64": result["docx_base64"]
        }

        logger.info(f"Returning successful response with request_id: {request_id}")
        return response_data

    except Exception as e:
        logger.error(f"Transform request failed: {str(e)}", exc_info=True)
        return {"error": f"Processing failed: {str(e)}"}


@web_app.post("/transform/download")
async def transform_download_web(
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
    # Call the processing function
    result = process_transcript.remote(
        template_id=template_id,
        project=project,
        job_min_no=job_min_no,
        description=description,
        date=date,
        time=time,
        location=location,
        file_content=file.file.read(),
        filename=file.filename,
    )

    # Convert base64 back to bytes
    docx_bytes = base64.b64decode(result["docx_base64"])

    # Create filename
    meeting_data = result["minutes"]
    meeting_date = meeting_data.get("meta", {}).get("date", "unknown").replace("/", "-")
    filename = f"meeting_minutes_{meeting_date}.docx"

    return StreamingResponse(
        content=io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@web_app.get("/health")
async def health_web():
    """
    Health check endpoint returning service status.
    Validates basic configuration and template availability.
    """
    try:
        from config import settings
        _ = settings.openai_api_key
        _ = settings.openai_model

        from template_registry import get_template
        _ = get_template("progress_minutes_v1")

        return {"status": "ok", "environment": "modal"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.function(image=image, volumes={"/data": volume})
def process_transcript(
    template_id: str,
    project: str,
    job_min_no: str,
    description: str,
    date: str,
    time: str,
    location: str,
    file_content: bytes,
    filename: str,
) -> Dict[str, Any]:
    """
    Core processing function that handles the transcript transformation.
    This runs in Modal's serverless environment.
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting transcript processing for project: {project}, file: {filename}")

        # Load environment variables from .env file
        load_dotenv()
        logger.info("Environment variables loaded")

        # Import our modules
        from llm_extractor import extract_meeting_model
        from models import MeetingMeta, MeetingModel
        from renderer import render_docx
        from template_registry import get_template
        from transcript_loader import load_transcript

        logger.info("Modules imported successfully")

        # Get template
        logger.info(f"Getting template: {template_id}")
        template = get_template(template_id)
        logger.info(f"Template loaded: {template.id}")

        # Load transcript
        logger.info(f"Loading transcript from {filename} ({len(file_content)} bytes)")
        text = load_transcript(file_content, filename)
        logger.info(f"Transcript loaded: {len(text)} characters")

        # Create metadata
        meta = MeetingMeta(
            project=project,
            job_min_no=job_min_no,
            description=description,
            date=date,
            time=time,
            location=location,
        )
        logger.info(f"Metadata created: {meta.project}")

        # Extract meeting model using LLM
        logger.info("Starting LLM extraction...")
        meeting = extract_meeting_model(text, meta, template)
        logger.info(f"LLM extraction completed. Attendees: {len(meeting.attendees)}, Sections: {len(meeting.sections)}")

        # Render DOCX
        logger.info("Rendering DOCX...")
        docx_bytes = render_docx(template, meeting)
        logger.info(f"DOCX rendered: {len(docx_bytes)} bytes")

        # Convert to base64
        docx_base64 = base64.b64encode(docx_bytes).decode("ascii")
        logger.info(f"Base64 conversion completed: {len(docx_base64)} characters")

        result = {
            "minutes": meeting.model_dump(),
            "docx_base64": docx_base64,
            "status": "success"
        }

        logger.info("Process completed successfully")
        return result

    except Exception as e:
        logging.error(f"Processing failed: {e}", exc_info=True)
        raise


# For local development/testing
if __name__ == "__main__":
    # Run locally for testing
    import uvicorn

    # Create a simple FastAPI app that delegates to Modal functions
    local_app = FastAPI(title="CompanyHeadedDocs - Local")

    @local_app.post("/transform")
    async def local_transform(
        template_id: str = Form(...),
        project: str = Form(...),
        job_min_no: str = Form(...),
        description: str = Form("Progress Meeting"),
        date: str = Form(...),
        time: str = Form(...),
        location: str = Form(...),
        file: UploadFile = File(...),
    ):
        result = process_transcript.remote(
            template_id=template_id,
            project=project,
            job_min_no=job_min_no,
            description=description,
            date=date,
            time=time,
            location=location,
            file_content=file.file.read(),
            filename=file.filename,
        )

        request_id = str(uuid.uuid4())
        return TransformResponse(
            request_id=request_id,
            minutes=result["minutes"],
            docx_base64=result["docx_base64"]
        )

    @local_app.get("/health")
    async def local_health():
        return {"status": "ok", "environment": "local"}

    print("Starting local server on http://127.0.0.1:8000")
    uvicorn.run(local_app, host="127.0.0.1", port=8000)


# Serve the FastAPI app with Modal
@app.function(image=image)
@modal.asgi_app()
def serve():
    # Add CORS middleware to handle preflight requests
    from starlette.middleware.cors import CORSMiddleware

    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Specific origins for development
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    return web_app
