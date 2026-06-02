from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(None)


class ChatResponse(BaseModel):
    type: str
    content: str
    session_id: str | None = None


class AbilitiesResponse(BaseModel):
    name: str
    description: str
    abilities: list[dict]
    greeting: str
