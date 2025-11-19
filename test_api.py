"""Quick end-to-end test of the API."""
import urllib.request
import urllib.parse
import base64
import json
from pathlib import Path

# Test the /transform endpoint
url = "http://127.0.0.1:8000/transform"

# Prepare multipart form data
import mimetypes
from email.generator import Generator
from io import BytesIO

def create_multipart_formdata(fields, files):
    """Create multipart/form-data body."""
    boundary = '----WebKitFormBoundary' + ''.join([str(i) for i in range(10)])
    body = BytesIO()
    
    # Add fields
    for key, value in fields.items():
        body.write(f'--{boundary}\r\n'.encode())
        body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        body.write(f'{value}\r\n'.encode())
    
    # Add files
    for key, (filename, fileobj) in files.items():
        body.write(f'--{boundary}\r\n'.encode())
        body.write(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode())
        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        body.write(f'Content-Type: {content_type}\r\n\r\n'.encode())
        body.write(fileobj.read())
        body.write(b'\r\n')
    
    body.write(f'--{boundary}--\r\n'.encode())
    return body.getvalue(), f'multipart/form-data; boundary={boundary}'

# Prepare data
fields = {
    'template_id': 'progress_minutes_v1',
    'project': 'Sample Project',
    'job_min_no': 'MIN-001',
    'description': 'Progress Meeting',
    'date': '20/06/2025',
    'time': '10:00',
    'location': 'Site Office'
}

with open('sample_transcript.txt', 'rb') as f:
    files = {'file': ('sample_transcript.txt', f)}
    body, content_type = create_multipart_formdata(fields, files)

print("Testing /transform endpoint...")
print(f"URL: {url}")
print(f"Template: {fields['template_id']}")
print()

try:
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', content_type)
    
    with urllib.request.urlopen(req, timeout=120) as response:
        status_code = response.getcode()
        result = json.loads(response.read().decode())
        
        print("SUCCESS - API responded!")
        print(f"  Status Code: {status_code}")
        print(f"  Request ID: {result.get('request_id', 'N/A')}")
        print()
        
        # Check minutes structure
        minutes = result.get('minutes', {})
        print("Minutes structure:")
        print(f"  Project: {minutes.get('meta', {}).get('project', 'N/A')}")
        print(f"  Attendees: {len(minutes.get('attendees', []))}")
        print(f"  Apologies: {len(minutes.get('apologies', []))}")
        print(f"  Sections: {len(minutes.get('sections', []))}")
        
        # Show first section
        if minutes.get('sections'):
            first_section = minutes['sections'][0]
            print(f"  First section: {first_section.get('code')} - {first_section.get('title')}")
            print(f"    Notes length: {len(first_section.get('notes', ''))}")
            print(f"    Actions: {len(first_section.get('actions', []))}")
        
        # Check DOCX
        docx_b64 = result.get('docx_base64', '')
        if docx_b64:
            docx_bytes = base64.b64decode(docx_b64)
            print()
            print(f"DOCX:")
            print(f"  Base64 length: {len(docx_b64)} chars")
            print(f"  Decoded size: {len(docx_bytes)} bytes")
            print(f"  Magic bytes: {docx_bytes[:2]}")
            
            # Save it
            output_path = Path('out/test_output.docx')
            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(docx_bytes)
            print(f"  Saved to: {output_path}")
            print()
            print("END-TO-END TEST PASSED!")
        else:
            print("ERROR: No docx_base64 in response")
        
except urllib.error.URLError as e:
    if isinstance(e.reason, ConnectionRefusedError):
        print("ERROR: Could not connect to server. Is uvicorn running?")
        print("  Run: uvicorn main:app --reload")
    else:
        print(f"ERROR: {e}")
except urllib.error.HTTPError as e:
    print(f"ERROR: HTTP {e.code}")
    try:
        error_detail = json.loads(e.read().decode())
        print(f"  Detail: {error_detail}")
    except:
        error_text = e.read().decode()[:500]
        print(f"  Response: {error_text}")
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

