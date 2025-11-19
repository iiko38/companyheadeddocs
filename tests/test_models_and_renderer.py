"""Test MeetingModel and renderer without LLM calls.

This test builds a MeetingModel in code and verifies that render_docx
produces a valid DOCX file.
"""

from models import ActionItem, MeetingMeta, MeetingModel, Person, Section
from renderer import render_docx
from template_registry import get_template


def test_render_docx_with_fake_meeting():
    """Test that render_docx works with a fake MeetingModel built in code."""
    # Construct a fake MeetingModel in code (no LLM call)
    meta = MeetingMeta(
        project="Test Project",
        job_min_no="1234",
        description="Progress Meeting",
        date="20/06/2025",
        time="10:00",
        location="Site Office",
    )

    meeting = MeetingModel(
        meta=meta,
        attendees=[
            Person(name="Alice Smith", initials="AS", company="ClientCo"),
            Person(name="Bob Jones", initials="BJ", company="ContractorCo"),
        ],
        apologies=[
            Person(name="Charlie Brown", initials="CB", company="ConsultantCo"),
        ],
        sections=[
            Section(
                code="1",
                title="Introductions",
                notes="Introductions and review of the agenda.",
                actions=[
                    ActionItem(
                        action="Circulate updated project directory.",
                        owner="Alice Smith",
                        due_date="27/06/2025",
                    )
                ],
            ),
            Section(
                code="2",
                title="Monthly Progress report Presentation (Report No. xx)",
                notes="Overall progress is on track, minor delays on facade.",
                actions=[],
            ),
        ],
    )

    # Load the progress template
    template = get_template("progress_minutes_v1")

    # Call render_docx to get docx_bytes
    docx_bytes = render_docx(template, meeting)

    # Assertions
    assert isinstance(docx_bytes, bytes), "docx_bytes should be bytes"
    assert len(docx_bytes) > 0, "docx_bytes should not be empty"

    # TODO: Optionally use python-docx to open the bytes and assert that
    # some known text is present (e.g. "Test Project" or "Alice Smith")

