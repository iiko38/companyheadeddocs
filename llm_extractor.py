import json
from textwrap import dedent
from typing import Any

from fastapi import HTTPException
from openai import OpenAI

from config import settings
from models import MeetingMeta, MeetingModel, TemplateExtractionSpec, TemplateSpec


def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def extract_meeting_model(text: str, meta: MeetingMeta, template: TemplateSpec) -> MeetingModel:
    prompt = build_prompt(text=text, meta=meta, extraction=template.extraction)
    client = _client()
    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    raw_json = _extract_text_payload(response)
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        repaired = _repair_json(raw_json, prompt)
        try:
            data = json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail="Failed to parse LLM JSON output") from exc

    meeting = MeetingModel.model_validate(data)
    meeting.meta = meta
    return meeting


def build_prompt(*, text: str, meta: MeetingMeta, extraction: TemplateExtractionSpec) -> str:
    sections_description = "\n".join(
        f"- {section.code}: {section.title} (aliases: {', '.join(section.aliases) if section.aliases else 'none'})"
        for section in extraction.predefined_sections
    )
    schema_description = dedent(
        """
        Return strictly valid JSON for the meeting minutes with this schema:
        {
          "meta": {
            "project": string,
            "job_min_no": string,
            "description": string,
            "date": string,
            "time": string,
            "location": string
          },
          "attendees": [
            {"name": string, "initials": string, "company": string}
          ],
          "apologies": [
            {"name": string, "initials": string, "company": string}
          ],
          "sections": [
            {
              "code": string,
              "title": string,
              "notes": string,
              "actions": [
                {"action": string, "owner": string, "due_date": string}
              ],
              "dates": {
                "contract_commencement": string,
                "section1_completion": string,
                "section2_completion": string,
                "section3_completion": string,
                "practical_completion": string
              } | null
            }
          ]
        }
        Use empty strings for unknown values. Do not invent people, dates, or sections that are not present in the transcript.
        Only use the predefined section titles and codes below. If information is missing for a section, still include the section with empty strings.
        """
    )

    return dedent(
        f"""
        You are an assistant that extracts structured meeting minutes from a transcript.
        Copy the meeting metadata exactly as provided. Do not reformat dates or times.

        Meeting metadata:
        project: {meta.project}
        job_min_no: {meta.job_min_no}
        description: {meta.description}
        date: {meta.date}
        time: {meta.time}
        location: {meta.location}

        Predefined sections:
        {sections_description}

        Transcript:
        ---
        {text}
        ---

        {schema_description}
        """
    ).strip()


def _extract_text_payload(response: Any) -> str:
    try:
        return response.output[0].content[0].text
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Unexpected LLM response format") from exc


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

    client = _client()
    response = client.responses.create(
        model=settings.openai_model,
        input=repair_prompt,
        response_format={"type": "json_object"},
        temperature=0,
    )
    return _extract_text_payload(response)
