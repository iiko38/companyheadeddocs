# Meeting Transcript → Company Headed DOCX Service

FastAPI service that converts uploaded meeting transcripts into structured meeting minutes JSON and renders headed DOCX output using predefined templates.

## Quick start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables (see Configuration section below):
   - Option A: Copy `.env.example` to `.env` and fill in your values
   - Option B: Set environment variables directly in your shell
3. Run the API:
   ```bash
   uvicorn main:app --reload
   ```

## Configuration

This service uses **Azure OpenAI** via the OpenAI Python client library. The client is configured with a `base_url` pointing to your Azure endpoint.

### Required environment variables

- `AZURE_OPENAI_API_KEY` (or `OPENAI_API_KEY`): Your Azure OpenAI API key
- `OPENAI_MODEL`: The Azure deployment/model name (e.g., `gpt-4.1-mini`)

### Optional environment variables

- `AZURE_OPENAI_ENDPOINT` (or `AZURE_OPENAI_BASE_URL`, or `OPENAI_BASE_URL`): Your Azure OpenAI endpoint URL

  - If provided as a bare endpoint (e.g., `https://YOUR-RESOURCE.openai.azure.com`), the service automatically appends `/openai/v1/`
  - If already a full v1 URL, it's used as-is
  - If not provided, the client uses the default OpenAI endpoint (for compatibility)

### Example configuration

**Option 1: Using .env file (recommended for local development)**

Copy `.env.example` to `.env` and update the values:
```bash
cp .env.example .env
# Then edit .env with your actual values
```

**Option 2: Environment variables**

```bash
export AZURE_OPENAI_API_KEY="sk-..."
export AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE-NAME.openai.azure.com"
export OPENAI_MODEL="gpt-4.1-mini"  # or your Azure deployment/model name
```

On Windows PowerShell:
```powershell
$env:AZURE_OPENAI_API_KEY="sk-..."
$env:AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE-NAME.openai.azure.com"
$env:OPENAI_MODEL="gpt-4.1-mini"
```

The service uses the OpenAI Python client with `base_url` configured to point at Azure, ensuring your data stays within Azure's infrastructure and isn't used to train OpenAI's public models.

## Running tests

Install dependencies and run tests:

```bash
pip install -r requirements.txt
pytest
```

Tests verify that the MeetingModel and renderer work correctly without requiring LLM calls.

## Endpoints

- `POST /transform`: Multipart form upload of `file` plus meeting metadata and `template_id`; returns JSON containing the meeting model and a base64 encoded DOCX.
- `POST /transform/download`: Same inputs but streams the DOCX file download directly.
- `GET /health`: Basic health check.

Templates live under `templates/` and are registered in `template_registry.py`. If you don't have a branded DOCX handy the service auto-generates a lightweight fallback template at runtime, so binary template files don't need to live in the repository. The service keeps all transcript and generated document data in memory only.
