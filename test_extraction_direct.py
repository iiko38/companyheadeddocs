"""Test extraction function directly."""
import os
from models import MeetingMeta
from template_registry import get_template
from llm_extractor import extract_meeting_model

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Test assumes .env file is present with required variables

# Reload config to pick up new env vars
import importlib
import config
import llm_extractor
importlib.reload(config)
importlib.reload(llm_extractor)

text = """Meeting between Jake (Client) and Sam (Contractor) on 20 June 2025.

Introductions:
- Jake introduces the project and confirms scope.
- Sam confirms he is the site lead.

Monthly Progress Report:
- Sam explains that Section 1 is 80% complete.
- Delays due to material shortages, but still targeting 15/07/2025.

Health & Safety:
- No reported incidents this month.

Construction Programme & Progress Review:
- Programme updated to reflect new delivery dates.
- Sam to send updated programme by 21/06/2025.

Design Matters:
- Jake requests clarification on the lobby finishes.
- Action: Sam to send revised drawings to Jake by 24/06/2025.

Contract Dates:
- Contract commencement was 01/05/2025.
- Practical completion currently planned for 30/09/2025.
"""

meta = MeetingMeta(
    project="Sample Project",
    job_min_no="MIN-001",
    description="Progress Meeting",
    date="20/06/2025",
    time="10:00",
    location="Site Office",
)

template = get_template("progress_minutes_v1")

print("Testing extract_meeting_model...")
print(f"Text length: {len(text)}")
print()

try:
    meeting = extract_meeting_model(text, meta, template)
    print("SUCCESS!")
    print(f"Attendees: {len(meeting.attendees)}")
    print(f"Sections: {len(meeting.sections)}")
    print(f"First section: {meeting.sections[0].code} - {meeting.sections[0].title}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

