from pydantic import BaseModel, Field


class JoinRoomRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=12)
    role: str = Field(min_length=1, max_length=20)
    room_version: int = Field(ge=1)


class SubmitActionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=240)
    room_version: int = Field(ge=1)
