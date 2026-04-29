from app.schemas import ResumeData


def test_resume_data_defaults_to_empty_sections() -> None:
    resume = ResumeData()

    assert resume.contact.name is None
    assert resume.education == []
    assert resume.work_experience == []
    assert resume.skills == []
    assert resume.certifications == []
    assert resume.projects == []
    assert resume.languages == []
    assert resume.raw_markdown_preview == ""


def test_resume_data_accepts_expected_fields() -> None:
    resume = ResumeData.model_validate(
        {
            "contact": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+1 555 123 4567",
                "location": "New York, NY",
                "links": ["https://linkedin.com/in/janedoe"],
            },
            "summary": "Backend engineer.",
            "education": [
                {
                    "institution": "Example University",
                    "degree": "BS",
                    "field_of_study": "Computer Science",
                    "graduation_year": "2020",
                }
            ],
            "work_experience": [
                {
                    "company": "Acme",
                    "position": "Engineer",
                    "description": "Built APIs.",
                    "highlights": ["FastAPI", "Postgres"],
                }
            ],
            "skills": ["Python", "FastAPI"],
            "raw_markdown_preview": "Jane Doe",
        }
    )

    assert resume.contact.email == "jane@example.com"
    assert resume.education[0].institution == "Example University"
    assert resume.work_experience[0].highlights == ["FastAPI", "Postgres"]
