from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    conversation_id: str | None = Field(default=None, pattern=r"^con_[a-f0-9]{32}$")
    canvas_revision: int | None = Field(default=None, ge=1)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question cannot be blank")
        return cleaned
