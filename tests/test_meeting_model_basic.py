"""Basic test for MeetingModel and DOCX rendering.

This test builds a MeetingModel in code (no LLM) and verifies that render_docx
produces a valid DOCX file without exceptions.
"""

from pathlib import Path

from models import ActionItem, MeetingMeta, MeetingModel, Person, Section, SectionDates
from renderer import render_docx
from template_registry import get_template


def test_render_docx_with_minimal_model():
    """Test that render_docx works with a minimal MeetingModel."""
    # Build a minimal MeetingModel in code
    meta = MeetingMeta(
        project="Test Project",
        job_min_no="TEST-001",
        description="Test Meeting",
        date="01/01/2024",
        time="10:00",
        location="Test Location",
    )

    meeting = MeetingModel(
        meta=meta,
        attendees=[
            Person(name="John Doe", initials="JD", company="Test Co"),
            Person(name="Jane Smith", initials="JS", company=""),
        ],
        apologies=[Person(name="Bob Wilson", initials="BW", company="Other Co")],
        sections=[
            Section(
                code="1",
                title="Test Section",
                notes="Some test notes here",
                actions=[
                    ActionItem(action="Test action", owner="John", due_date="15/01/2024")
                ],
                dates=None,
            ),
            Section(
                code="6",
                title="Contract Dates",
                notes="",
                actions=[],
                dates=SectionDates(
                    contract_commencement="01/07/2024",
                    section1_completion="15/12/2024",
                    section2_completion="",
                    section3_completion="",
                    practical_completion="30/06/2025",
                ),
            ),
        ],
    )

    # Get template
    template = get_template("progress_minutes_v1")

    # Render DOCX
    docx_bytes = render_docx(template, meeting)

    # Assertions
    assert len(docx_bytes) > 0, "DOCX bytes should not be empty"
    assert docx_bytes.startswith(b"PK"), "DOCX should start with ZIP magic bytes (PK)"

