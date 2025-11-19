from pydantic import BaseModel, Field


class MeetingMeta(BaseModel):
    project: str
    job_min_no: str
    description: str
    date: str  # dd/mm/yyyy
    time: str
    location: str


class ActionItem(BaseModel):
    action: str
    owner: str = ""
    due_date: str = ""  # dd/mm/yyyy or ""


class SectionDates(BaseModel):
    contract_commencement: str = ""
    section1_completion: str = ""
    section2_completion: str = ""
    section3_completion: str = ""
    practical_completion: str = ""


class Section(BaseModel):
    code: str
    title: str
    notes: str = ""
    actions: list[ActionItem] = Field(default_factory=list)
    dates: SectionDates | None = None


class Person(BaseModel):
    name: str
    initials: str = ""
    company: str = ""


class MeetingModel(BaseModel):
    meta: MeetingMeta
    attendees: list[Person] = Field(default_factory=list)
    apologies: list[Person] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)


class TemplateSectionSpec(BaseModel):
    code: str
    title: str
    aliases: list[str] = Field(default_factory=list)


class TemplateExtractionSpec(BaseModel):
    predefined_sections: list[TemplateSectionSpec]
    wants_actions: bool = True
    wants_dates: bool = False


class TemplateBindingSpec(BaseModel):
    id: str


class TemplateSpec(BaseModel):
    id: str
    label: str
    extraction: TemplateExtractionSpec
    binding: TemplateBindingSpec
    docx_path: str
