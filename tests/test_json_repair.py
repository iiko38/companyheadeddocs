"""Test the JSON repair functionality in llm_extractor."""
import json
from unittest.mock import MagicMock, patch

import pytest

from llm_extractor import _repair_json
from models import MeetingMeta
from template_registry import get_template


def test_json_repair_success():
    """Test that _repair_json can fix malformed JSON and return valid MeetingModel data."""
    # Mock malformed JSON that the LLM might return initially
    malformed_json = '''
    {
        "meta": {
            "project": "Test Project",
            "job_min_no": "TEST-001",
            "description": "Test Meeting",
            "date": "01/01/2024",
            "time": "10:00",
            "location": "Test Location"
        },
        "attendees": [
            {"name": "John Doe", "initials": "JD", "company": "Test Co"}
        ],
        "apologies": [],
        "sections": [
            {
                "code": "1",
                "title": "Test Section",
                "notes": "Some notes",
                "actions": [],
                "dates": null
            }
        ]
        // Missing closing brace - this is malformed!
    '''

    # Valid JSON that the repair LLM call should return
    repaired_json = '''
    {
        "meta": {
            "project": "Test Project",
            "job_min_no": "TEST-001",
            "description": "Test Meeting",
            "date": "01/01/2024",
            "time": "10:00",
            "location": "Test Location"
        },
        "attendees": [
            {"name": "John Doe", "initials": "JD", "company": "Test Co"}
        ],
        "apologies": [],
        "sections": [
            {
                "code": "1",
                "title": "Test Section",
                "notes": "Some notes",
                "actions": [],
                "dates": null
            }
        ]
    }
    '''

    # Mock the LLM client to return the repaired JSON
    mock_response = MagicMock()
    mock_response.output_text = repaired_json

    with patch('llm_extractor.client') as mock_client:
        mock_client.responses.create.return_value = mock_response

        # Test the repair function
        result = _repair_json(malformed_json, "dummy prompt")

        # Should return valid JSON that can be parsed
        result_data = json.loads(result)
        expected_data = json.loads(repaired_json)

        # Should match the expected structure
        assert result_data == expected_data

        # Should have called the LLM once
        assert mock_client.responses.create.call_count == 1

        # Verify the call was made with correct parameters
        call_args = mock_client.responses.create.call_args
        assert "model" in call_args[1]
        assert "input" in call_args[1]
        # Should not include temperature since it's not set in config
        assert "temperature" not in call_args[1]


def test_json_repair_failure():
    """Test that _repair_json raises HTTPException when repair LLM call fails."""
    from fastapi import HTTPException

    malformed_json = '{"broken": json}'
    prompt = "dummy prompt"

    # Mock the LLM client to raise an exception
    with patch('llm_extractor.client') as mock_client:
        mock_client.responses.create.side_effect = Exception("LLM repair failed")

        with pytest.raises(HTTPException) as exc_info:
            _repair_json(malformed_json, prompt)

        assert exc_info.value.status_code == 502
        assert "repair call failed" in exc_info.value.detail
