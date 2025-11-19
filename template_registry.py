from fastapi import HTTPException

from models import TemplateBindingSpec, TemplateExtractionSpec, TemplateSectionSpec, TemplateSpec


PROGRESS_TEMPLATE = TemplateSpec(
    id="progress_minutes_v1",
    label="Construction Progress Meeting Minutes",
    docx_path="templates/progress_minutes_v1.docx",
    extraction=TemplateExtractionSpec(
        predefined_sections=[
            TemplateSectionSpec(code="1", title="Introductions"),
            TemplateSectionSpec(code="2", title="Monthly Progress report Presentation (Report No. xx)"),
            TemplateSectionSpec(code="3", title="Health & Safety"),
            TemplateSectionSpec(code="4", title="Construction Programme & Progress Review"),
            TemplateSectionSpec(code="5", title="Design Matters"),
            TemplateSectionSpec(
                code="6",
                title="Contract Dates",
                aliases=["Contract", "Contract Dates"],
            ),
        ],
        wants_actions=True,
        wants_dates=True,
    ),
    binding=TemplateBindingSpec(id="progress_minutes_v1"),
)

TEMPLATES: dict[str, TemplateSpec] = {PROGRESS_TEMPLATE.id: PROGRESS_TEMPLATE}


def get_template(template_id: str) -> TemplateSpec:
    try:
        return TEMPLATES[template_id]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="Unknown template_id") from exc
