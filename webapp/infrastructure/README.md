# Infrastructure - Modal Deployment

This folder contains the Modal deployment configuration for the Company Headed Docs application.

## Files

- `modal_app.py` - Main Modal application with FastAPI endpoints
- `requirements.txt` - Python dependencies for Modal deployment
- `README.md` - This deployment guide

## Prerequisites

1. **Python 3.12 environment** for Modal CLI
2. **Modal account** and authentication
3. **Azure OpenAI API key** configured in `.env`

## Setup

### 1. Install Modal CLI

```bash
# In a Python 3.12 environment
pip install modal
python -m modal setup
```

### 2. Configure Environment

Update the root `.env` file with your Azure OpenAI credentials:

```bash
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com
OPENAI_MODEL=gpt-5-mini
```

### 3. Deploy

```bash
# From the project root directory
modal deploy webapp/infrastructure/modal_app.py
```

Or from the infrastructure directory:

```bash
cd webapp/infrastructure
modal deploy modal_app.py
```

## API Endpoints

After deployment, the following endpoints will be available:

- `POST /transform` - Process transcripts and return DOCX as base64
- `POST /transform/download` - Process transcripts and return DOCX file download
- `GET /health` - Health check endpoint

## Webapp Integration

The webapp automatically connects to the Modal endpoints. Update the API URL in `webapp/src/lib/api.ts` if needed:

```typescript
const API_BASE_URL = 'https://your-modal-app-url.modal.run'
```

## Troubleshooting

### CORS Issues
The Modal app includes CORS middleware for development. For production, update the allowed origins in `modal_app.py`.

### Environment Variables
Modal loads environment variables from the mounted `.env` file. Ensure all required variables are set.

### Deployment Issues
Check Modal logs:
```bash
modal app logs <app-id>
```

## Architecture

- **Frontend**: React + TypeScript webapp
- **Backend**: Modal serverless functions with FastAPI
- **AI**: Azure OpenAI GPT-4 for transcript processing
- **Storage**: DOCX templates and output generation
