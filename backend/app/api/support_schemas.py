from pydantic import BaseModel, ConfigDict, field_validator


def _normalize_bounded_text(value: str, *, maximum: int) -> str:
    normalized = " ".join(value.strip().split())
    if not 1 <= len(normalized) <= maximum:
        raise ValueError("support text is outside the allowed boundary")
    return normalized


class RuleLookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return _normalize_bounded_text(value, maximum=500)


class DraftReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    description: str

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return _normalize_bounded_text(value, maximum=2000)
