from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    graduation_year: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class WorkExperienceItem(BaseModel):
    company: str | None = None
    position: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration: str | None = None
    description: str | None = None
    highlights: list[str] = Field(default_factory=list)


class CertificationItem(BaseModel):
    name: str | None = None
    issuer: str | None = None
    year: str | None = None


class ProjectItem(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class ResumeData(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str | None = None
    education: list[EducationItem] = Field(default_factory=list)
    work_experience: list[WorkExperienceItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    raw_markdown_preview: str = ""


class ParseResponse(BaseModel):
    provider: str
    model: str
    filename: str
    data: ResumeData
