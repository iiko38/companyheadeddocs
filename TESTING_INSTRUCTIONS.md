# End-to-End Testing Instructions

## Prerequisites

1. Set your Azure OpenAI environment variables:
   ```bash
   export AZURE_OPENAI_API_KEY="your_azure_key"
   export AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com"
   export OPENAI_MODEL="your-deployment-name"  # e.g. gpt-4.1-mini
   ```

   On Windows PowerShell:
   ```powershell
   $env:AZURE_OPENAI_API_KEY="your_azure_key"
   $env:AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com"
   $env:OPENAI_MODEL="your-deployment-name"
   ```

## Test Steps

1. **Start the server:**
   ```bash
   uvicorn main:app --reload
   ```

2. **In another terminal, run the test script:**
   ```bash
   python test_api.py
   ```

   Or use curl (if available):
   ```bash
   curl -X POST "http://127.0.0.1:8000/transform" \
     -F "template_id=progress_minutes_v1" \
     -F "project=Sample Project" \
     -F "job_min_no=MIN-001" \
     -F "description=Progress Meeting" \
     -F "date=20/06/2025" \
     -F "time=10:00" \
     -F "location=Site Office" \
     -F "file=@sample_transcript.txt"
   ```

## Expected Results

If successful, you should see:
- Status Code: 200
- A `request_id` in the response
- `minutes` JSON with:
  - `meta` object with your provided fields
  - `attendees` array (extracted from transcript)
  - `apologies` array (if any)
  - `sections` array matching the predefined sections
- `docx_base64` string that can be decoded to a valid DOCX file

The test script will save the DOCX to `out/test_output.docx` for inspection.

## Troubleshooting

- **Connection refused**: Make sure uvicorn is running on port 8000
- **502 Bad Gateway**: Check Azure OpenAI credentials and endpoint
- **500 Internal Server Error**: Check server logs for details
- **Config errors**: Ensure all required env vars are set before starting the server

