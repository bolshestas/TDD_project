from pydantic import BaseModel, field_validator


class ShortenRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str

    model_config = {"from_attributes": True}
