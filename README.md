# Meeting Transcript → Company Headed DOCX Service

FastAPI service that converts uploaded meeting transcripts into structured meeting minutes JSON and renders headed DOCX output using predefined templates.

## Quick start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables:
   ```bash
   export OPENAI_API_KEY=<your-key>
   export OPENAI_MODEL=gpt-4.1-mini
   ```
3. Run the API:
   ```bash
   uvicorn main:app --reload
   ```

## Endpoints

- `POST /transform`: Multipart form upload of `file` plus meeting metadata and `template_id`; returns JSON containing the meeting model and a base64 encoded DOCX.
- `POST /transform/download`: Same inputs but streams the DOCX file download directly.
- `GET /health`: Basic health check.

Templates live under `templates/` and are registered in `template_registry.py`. If you don't have a branded DOCX handy the service auto-generates a lightweight fallback template at runtime, so binary template files don't need to live in the repository. The service keeps all transcript and generated document data in memory only.
