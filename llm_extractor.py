import json
import logging
from textwrap import dedent
from typing import Any

from fastapi import HTTPException
from openai import OpenAI

from config import settings
from models import MeetingMeta, MeetingModel, TemplateExtractionSpec, TemplateSpec

logger = logging.getLogger(__name__)

# Maximum transcript length in characters before truncation
# Increased to handle large meeting transcripts (13k+ words = ~90k chars)
# Note: Azure Responses API can handle much larger inputs, but we keep a reasonable limit
# for cost and processing time. For transcripts exceeding this, chunking should be implemented.
MAX_TRANSCRIPT_CHARS = 150000

# Module-level OpenAI client configured for Azure
client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.resolved_base_url or None,
)


def extract_meeting_model(text: str, meta: MeetingMeta, template: TemplateSpec) -> MeetingModel:
    original_length = len(text)
    # TODO: implement proper chunked map-reduce summarisation for very long transcripts
    if len(text) > MAX_TRANSCRIPT_CHARS:
        logger.warning(
            "Transcript truncated for length",
            extra={
                "template_id": template.id,
                "original_length": original_length,
                "truncated_length": MAX_TRANSCRIPT_CHARS,
            },
        )
        text = text[:MAX_TRANSCRIPT_CHARS]
        truncation_note = True
    else:
        truncation_note = False

    logger.info(
        "Extracting meeting model",
        extra={"template_id": template.id, "transcript_length": len(text)},
    )
    prompt = build_prompt(text=text, meta=meta, extraction=template.extraction, was_truncated=truncation_note)

    try:
        # Build kwargs, conditionally including temperature for Azure compatibility
        # Azure deployments may reject temperature parameter, so only pass when explicitly set
        kwargs = {
            "model": settings.openai_model,
            "input": prompt,
        }
        if settings.openai_temperature_float is not None:
            kwargs["temperature"] = settings.openai_temperature_float

        response = client.responses.create(**kwargs)

        raw_json = _extract_text_payload(response)
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            logger.warning("Initial JSON parse failed, attempting repair")
            repaired = _repair_json(raw_json, prompt)
            try:
                data = json.loads(repaired)
            except json.JSONDecodeError as exc:
                logger.error("JSON repair failed", exc_info=exc)
                raise HTTPException(
                    status_code=502, detail="LLM extraction failed: invalid JSON after repair"
                ) from exc

        meeting = MeetingModel.model_validate(data)
        meeting.meta = meta
        return meeting
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "LLM extraction failed",
            exc_info=exc,
            extra={"template_id": template.id, "prompt_preview": prompt[:200]},
        )
        raise HTTPException(status_code=502, detail="LLM extraction failed") from exc


def build_prompt(*, text: str, meta: MeetingMeta, extraction: TemplateExtractionSpec, was_truncated: bool = False) -> str:
    """
    Build a structured prompt for LLM extraction.

    Structure:
    1. USER-PROVIDED METADATA: project, date, time, location (must be copied exactly)
    2. TEMPLATE SECTIONS: predefined sections with codes and titles
    3. TASKS: numbered instructions for extraction
    4. OUTPUT SCHEMA: literal JSON example matching MeetingModel
    5. TRANSCRIPT: the actual meeting transcript text
    """
    # USER-PROVIDED METADATA
    metadata_section = dedent(
        f"""
        === USER-PROVIDED METADATA ===
        These values must be copied EXACTLY into the output JSON meta field. Do not modify or reformat them.

        project: {meta.project}
        job_min_no: {meta.job_min_no}
        description: {meta.description}
        date: {meta.date}
        time: {meta.time}
        location: {meta.location}
        """
    ).strip()

    # TEMPLATE SECTIONS
    sections_list = "\n".join(
        f"  {section.code}: {section.title}"
        + (f" (aliases: {', '.join(section.aliases)})" if section.aliases else "")
        for section in extraction.predefined_sections
    )
    template_sections = dedent(
        f"""
        === TEMPLATE SECTIONS ===
        You must use exactly these section codes and titles in your output. Include all sections even if empty.

        {sections_list}
        """
    ).strip()

    # TASKS
    truncation_warning = (
        "\n  Note: The transcript was truncated for length. Only the visible portion was available."
        if was_truncated
        else ""
    )
    tasks = dedent(
        f"""
        === TASKS ===
        1. Extract attendees and apologies from the transcript. Use empty strings for missing initials or company.
        2. For each predefined section above, extract notes and actions from the transcript.
        3. Use exactly the given section codes and titles - do not invent new sections.
        4. For actions: if an owner or due_date is not mentioned, use an empty string (""). Do not guess.
        5. For contract dates: extract from sections with "contract" in the title, or leave dates as empty strings.
        6. Copy the metadata fields EXACTLY as provided - do not modify dates, times, or other metadata values.
        7. Do not invent information. If unsure, use empty strings ("").{truncation_warning}
        """
    ).strip()

    # OUTPUT SCHEMA with literal JSON example
    output_schema = dedent(
        """
        === OUTPUT SCHEMA ===
        Your output MUST be a single JSON object matching this exact structure. Do not include any extra fields or top-level keys.

        Example output (with dummy values):
        {
          "meta": {
            "project": "Example Project",
            "job_min_no": "JOB-001",
            "description": "Progress Meeting",
            "date": "15/11/2024",
            "time": "10:00",
            "location": "Site Office"
          },
          "attendees": [
            {"name": "John Smith", "initials": "JS", "company": "Contractor Ltd"},
            {"name": "Jane Doe", "initials": "JD", "company": ""}
          ],
          "apologies": [
            {"name": "Mike Johnson", "initials": "MJ", "company": "Consultant Co"}
          ],
          "sections": [
            {
              "code": "1",
              "title": "Introductions",
              "notes": "Team introductions completed",
              "actions": [
                {"action": "Send updated drawings", "owner": "John", "due_date": "21/06/2025"}
              ],
              "dates": null
            },
            {
              "code": "6",
              "title": "Contract Dates",
              "notes": "",
              "actions": [],
              "dates": {
                "contract_commencement": "01/07/2024",
                "section1_completion": "15/12/2024",
                "section2_completion": "",
                "section3_completion": "",
                "practical_completion": "30/06/2025"
              }
            }
          ]
        }

        Field types:
        - meta: object with project (string), job_min_no (string), description (string), date (string), time (string), location (string)
        - attendees: array of objects with name (string), initials (string), company (string)
        - apologies: array of objects with name (string), initials (string), company (string)
        - sections: array of objects with:
          - code (string): must match one of the predefined section codes
          - title (string): must match one of the predefined section titles
          - notes (string): extracted notes for this section
          - actions (array): array of objects with action (string), owner (string), due_date (string)
          - dates (object | null): object with contract_commencement, section1_completion, section2_completion, section3_completion, practical_completion (all strings), or null

        Critical rules:
        - Metadata fields (project, job_min_no, description, date, time, location) must be copied EXACTLY as provided above.
        - Do not invent information. If unsure, use empty strings ("").
        - Use exactly the predefined section codes and titles listed above.
        - If a section has no information, still include it with empty notes and actions.
        - For each section, the first action in the "actions" array should be the most important/primary action.
        """
    ).strip()

    # TRANSCRIPT
    transcript_section = dedent(
        f"""
        === TRANSCRIPT ===
        {text}
        """
    ).strip()

    # Combine all sections
    return "\n\n".join([metadata_section, template_sections, tasks, output_schema, transcript_section])


def _extract_text_payload(response: Any) -> str:
    """
    Extract the JSON string from a Responses API response.
    Handles reasoning models which may have reasoning items before the message.
    """
    # First try the convenience property (works for most cases)
    text = getattr(response, "output_text", None)
    if text:
        return text
    
    # Fallback: extract from output array
    # For reasoning models, output may contain reasoning items before the message
    try:
        if hasattr(response, "output") and response.output:
            # Find the first message item (skip reasoning items)
            for item in response.output:
                if hasattr(item, "type") and item.type == "message":
                    if hasattr(item, "content") and item.content:
                        # Get the first text content
                        for content in item.content:
                            if hasattr(content, "type") and content.type == "output_text":
                                if hasattr(content, "text"):
                                    return content.text
                            # Also check for direct text attribute
                            if hasattr(content, "text"):
                                return content.text
    except Exception as e:
        logger.warning(f"Failed to extract from output array: {e}")
    
    raise ValueError("Could not extract text payload from Responses API response")


def _repair_json(bad_json: str, prompt: str) -> str:
    repair_prompt = dedent(
        f"""
        The following string was intended to be valid JSON but was not parsable.
        Return only valid JSON that matches the requested schema. Do not include commentary.
        Original request:
        {prompt}

        Broken JSON:
        {bad_json}
        """
    )

    try:
        # Same reasoning as above: avoid explicit `temperature` for maximum
        # compatibility with Azure Responses deployments.
        kwargs = {
            "model": settings.openai_model,
            "input": repair_prompt,
        }
        if settings.openai_temperature_float is not None:
            kwargs["temperature"] = settings.openai_temperature_float

        response = client.responses.create(**kwargs)
        return _extract_text_payload(response)
    except Exception as exc:
        logger.error("JSON repair LLM call failed", exc_info=exc)
        raise HTTPException(status_code=502, detail="LLM extraction failed: repair call failed") from exc
