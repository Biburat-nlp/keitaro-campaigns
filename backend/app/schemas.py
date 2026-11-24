from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from app.countries import COUNTRY_CODES


def clean_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise PydanticCustomError("empty_name", "Name can't be empty")
    return value


def clean_countries(values: list[str]) -> list[str]:
    result: list[str] = []
    for raw in values:
        code = raw.strip().upper()
        if code not in COUNTRY_CODES:
            raise PydanticCustomError("unknown_country", "Unknown country code: {code}", {"code": raw.strip()})
        if code not in result:
            result.append(code)
    if not result:
        raise PydanticCustomError("need_country", "At least one country is required")
    return result


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    countries: list[str] = Field(min_length=1)
    offer_id: int = Field(gt=0)
    domain_id: int | None = Field(default=None, gt=0)
    group_id: int | None = Field(default=None, gt=0)
    traffic_source_id: int | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return clean_name(value)

    @field_validator("countries")
    @classmethod
    def check_countries(cls, value: list[str]) -> list[str]:
        return clean_countries(value)


class CountriesAdd(BaseModel):
    countries: list[str] = Field(min_length=1)

    @field_validator("countries")
    @classmethod
    def check_countries(cls, value: list[str]) -> list[str]:
        return clean_countries(value)


class CampaignRename(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return clean_name(value)


class OfferAdd(BaseModel):
    offer_id: int = Field(gt=0)


class ShareSet(BaseModel):
    share: int = Field(ge=0, le=100)


class PinSet(BaseModel):
    pinned: bool


class OperationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    stream_id: int | None
    action: str
    details: dict[str, Any]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def as_utc(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class OperationsPage(BaseModel):
    items: list[OperationOut]
    total: int
    offset: int
    limit: int


class CampaignDetails(BaseModel):
    campaign: dict[str, Any]
    streams: list[dict[str, Any]]
    admin_url: str
    created_here: bool
