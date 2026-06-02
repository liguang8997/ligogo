from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    receiver_id: str
    title: str
    content: str
    type: int
    related_id: int | None
    is_read: int
    created_at: str
