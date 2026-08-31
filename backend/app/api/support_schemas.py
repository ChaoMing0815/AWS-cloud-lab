from pydantic import BaseModel, ConfigDict, field_validator


def _normalize_bounded_text(
    value: str,
    *,
    maximum: int,
    preserve_layout: bool = False,
) -> str:
    stripped = value.strip()
    normalized = " ".join(stripped.split())
    if not 1 <= len(normalized) <= maximum:
        raise ValueError("support text is outside the allowed boundary")
    return stripped if preserve_layout else normalized


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
        return _normalize_bounded_text(value, maximum=2000, preserve_layout=True)
