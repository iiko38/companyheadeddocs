"""Manual test script for the meeting transcript extraction pipeline.

Run this to test the full pipeline without starting the FastAPI server:
    python scripts/manual_test_progress.py
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import from the main modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import MeetingMeta
from template_registry import get_template
from transcript_loader import load_transcript
from llm_extractor import extract_meeting_model
from renderer import render_docx


def main():
    # Read sample transcript
    sample_path = Path(__file__).parent.parent / "samples" / "progress_meeting_short.txt"
    with open(sample_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Build dummy metadata
    meta = MeetingMeta(
        project="Test Construction Project",
        job_min_no="JOB-2024-001",
        description="Progress Meeting",
        date="15/11/2024",
        time="10:00",
        location="Site Office",
    )

    # Get template
    template = get_template("progress_minutes_v1")

    print("Extracting meeting model from transcript...")
    print(f"Transcript length: {len(text)} characters")
    print()

    # Extract meeting model
    meeting = extract_meeting_model(text, meta, template)

    # Print summary
    print("Extraction complete!")
    print(f"  Attendees: {len(meeting.attendees)}")
    print(f"  Apologies: {len(meeting.apologies)}")
    print(f"  Sections: {len(meeting.sections)}")
    total_actions = sum(len(section.actions) for section in meeting.sections)
    print(f"  Total actions: {total_actions}")
    print()

    # Render DOCX
    print("Rendering DOCX...")
    docx_bytes = render_docx(template, meeting)

    # Write output
    out_path = Path(__file__).parent.parent / "out" / "manual_test_progress.docx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(docx_bytes)

    print(f"DOCX written to: {out_path}")
    print(f"File size: {len(docx_bytes)} bytes")


if __name__ == "__main__":
    main()

