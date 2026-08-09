from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Tone = Literal[
    "light_comedy",
    "workplace_satire",
    "slice_of_life",
    "mystery",
    "adventure",
    "sci_fi",
    "dark_fairy_tale",
    "custom",
]


class ConfirmWorldRequest(BaseModel):
    story_title: str = Field(min_length=1, max_length=40)
    premise: str = Field(min_length=50, max_length=500)
    objective: str = Field(min_length=10, max_length=200)
    opening_scene: str = Field(min_length=20, max_length=400)
    core_obstacle: str = Field(min_length=10, max_length=200)
    tone: Tone
    custom_tone: str | None = Field(default=None, min_length=1, max_length=40)
    max_rounds: Literal[4, 6, 8]
    room_version: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_custom_tone(self) -> "ConfirmWorldRequest":
        if self.tone == "custom" and not self.custom_tone:
            raise ValueError("自訂調性不可空白。")
        if self.tone != "custom":
            self.custom_tone = None
        return self


class StartGameRequest(BaseModel):
    room_version: int = Field(ge=1)


class UpdateCharacterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    background: str = Field(min_length=10, max_length=160)
    trait: str = Field(min_length=1, max_length=40)
    weakness: str = Field(min_length=1, max_length=40)
    courage: int = Field(ge=0, le=2)
    insight: int = Field(ge=0, le=2)
    bond: int = Field(ge=0, le=2)
    room_version: int = Field(ge=1)


class JoinRoomRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=12)
    role: str = Field(min_length=1, max_length=20)
    room_version: int = Field(ge=1)


class CreateRoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nickname: str = Field(min_length=1, max_length=12)


class JoinRoomByCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_code: str
    nickname: str


class SubmitActionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=240)
    approach: Literal["courage", "insight", "bond"]
    room_version: int = Field(ge=1)


class RollRoundRequest(BaseModel):
    room_version: int = Field(ge=1)


class SparkDecisionRequest(BaseModel):
    decision: Literal["USE", "DECLINE"]
    room_version: int = Field(ge=1)


class ResolveRoundRequest(BaseModel):
    skip_pending_spark: bool = False
    room_version: int = Field(ge=1)


class FinishRoomRequest(BaseModel):
    decision: Literal["FINISH_NOW", "CONTINUE"]
    room_version: int = Field(ge=1)
