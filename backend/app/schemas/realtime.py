from typing import Literal

from pydantic import BaseModel


class RealtimeStatus(BaseModel):
    status: Literal["ok", "unavailable"]
    channel: str = "events:updates"
    endpoint: str = "/ws/events"
