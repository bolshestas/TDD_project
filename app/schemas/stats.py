from datetime import datetime
from pydantic import BaseModel


class StatsResponse(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}