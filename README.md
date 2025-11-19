# OKII TG DOCS - Meeting Transcript Processor

**Transform meeting transcripts into documented minutes** with AI-powered extraction and professional DOCX generation.

A modern web application that converts meeting transcripts (uploaded files or pasted text) into structured meeting minutes using Azure OpenAI GPT-4, then renders them into company-branded DOCX documents.

## ✨ Features

- **📝 Multiple Input Methods**: Upload transcript files (.txt, .docx, .vtt) or paste text directly
- **🤖 AI-Powered Extraction**: Uses Azure OpenAI GPT-4 to intelligently extract attendees, actions, dates, and meeting notes
- **📄 Professional Output**: Generates company-headed DOCX meeting minutes with customizable templates
- **🌐 Modern Web Interface**: Clean, responsive React UI with progress tracking
- **⚡ Serverless Backend**: Scalable Modal infrastructure for processing
- **🔒 Enterprise Security**: All data processed in-memory, Azure OpenAI ensures data privacy

## 🚀 Quick Start

### Prerequisites

- **Azure OpenAI account** with GPT-4 deployment
- **Node.js 18+** for frontend development
- **Python 3.12** for Modal CLI (if deploying)

### 1. Clone & Setup

```bash
git clone <repository-url>
cd companyheadeddocs

# Install webapp dependencies
cd webapp
npm install
cd ..
```

### 2. Configure Azure OpenAI

Create a `.env` file in the project root:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com
OPENAI_MODEL=gpt-5-mini
```

### 3. Run Locally

**Frontend Development:**
```bash
cd webapp
npm run dev
# Opens http://localhost:5173
```

**Backend Deployment:**
```bash
# Install Modal CLI
pip install modal
python -m modal setup

# Deploy backend
modal deploy webapp/infrastructure/modal_app.py
```

## 📋 How to Use

1. **Access the webapp** at `http://localhost:5173`
2. **Choose input method**:
   - **File Upload**: Select a transcript file (.txt, .docx, .vtt)
   - **Text Input**: Paste transcript text directly
3. **Fill meeting details**:
   - Project name
   - Job/Minute number
   - Description
   - Date, time, location
4. **Click "Generate Minutes"**
5. **Wait for AI processing** (progress bar shows ~90 seconds)
6. **Download** professional DOCX meeting minutes

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Webapp  │───▶│   Modal Backend │───▶│  Azure OpenAI   │
│                 │    │  (Serverless)   │    │     GPT-4       │
│ • File/Text     │    │ • FastAPI       │    │ • Extract       │
│   Input         │    │ • CORS enabled  │    │   Structure     │
│ • Progress UI   │    │ • AI Processing │    │ • Attendees     │
│ • Download      │    │ • DOCX Render   │    │ • Actions       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │   DOCX Output    │
                                           │ • Company        │
                                           │   Branding       │
                                           │ • Professional   │
                                           │   Format         │
                                           │ • Downloadable   │
                                           └─────────────────┘
```

### Key Components

- **Frontend** (`webapp/`): React + TypeScript + Tailwind CSS + shadcn/ui
- **Backend** (`webapp/infrastructure/`): Modal serverless functions + FastAPI
- **AI Processing** (`llm_extractor.py`): Azure OpenAI GPT-4 integration
- **Document Generation** (`renderer.py`): DOCX template rendering
- **Templates** (`templates/`): Company-branded DOCX templates

## 🔧 Development

### Project Structure

```
companyheadeddocs/
├── config.py              # Application configuration
├── llm_extractor.py       # AI processing logic
├── models.py              # Data models (Pydantic)
├── renderer.py            # DOCX generation
├── template_registry.py   # Template management
├── transcript_loader.py   # File/text processing
├── old/                   # Legacy files (deprecated)
├── samples/               # Sample transcripts
├── scripts/               # Utility scripts
├── templates/             # DOCX templates
├── tests/                 # Unit tests
└── webapp/                # React frontend
    ├── infrastructure/    # Modal deployment
    ├── src/               # React source code
    └── modal_env/         # Python environment
```

### Testing

```bash
# Unit tests (no LLM required)
pytest

# Manual testing with sample transcript
python -c "
from llm_extractor import extract_meeting_model
from models import MeetingMeta
# ... test code
"
```

### Deployment

**Production Deployment:**
```bash
# Deploy Modal backend
modal deploy webapp/infrastructure/modal_app.py

# Build and deploy webapp to Vercel/Netlify/etc
cd webapp
npm run build
# Deploy dist/ folder to hosting service
```

## 🔐 Security & Privacy

- **API Keys**: Never committed to version control (.env ignored by git)
- **Data Processing**: All transcripts processed in-memory only
- **Azure OpenAI**: Data stays within Azure infrastructure
- **No Training**: Your transcripts are not used to train OpenAI models

## 📚 API Reference

### Modal Endpoints

- `POST /transform` - Process transcript, return JSON + base64 DOCX
- `POST /transform/download` - Process transcript, return DOCX file download
- `GET /health` - Service health check

### Request Format

```typescript
interface TransformRequest {
  template_id: string        // e.g., "progress_minutes_v1"
  project: string           // Project name
  job_min_no: string        // Job/minute number
  description: string       // Meeting description
  date: string              // Meeting date
  time: string              // Meeting time
  location: string          // Meeting location
  file: File                // Transcript file OR text content
}
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly (both frontend and backend)
5. **Submit** a pull request

## 📄 License

[Add your license here]

## 🆘 Troubleshooting

**"CORS error"**: Ensure Modal backend is deployed and webapp points to correct URL
**"401 Unauthorized"**: Check Azure OpenAI API key and endpoint in .env
**"Modal deploy fails"**: Ensure Python 3.12 environment and Modal authentication
**"Build fails"**: Check Node.js version (18+) and dependencies

---

**Built with ❤️ using React, Modal, Azure OpenAI, and modern web technologies.**
