import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import Settings
from app.drafts import stream_view, upsert_stream
from app.errors import ServiceError
from app.keitaro import KeitaroClient, KeitaroError
from app.models import CampaignRecord, Operation, StreamRecord
from app.schemas import CampaignCreate

logger = logging.getLogger(__name__)

COUNTRY_FILTER = "country"
GEO_NAME_LIMIT = 5


def ensure_offer_exists(client: KeitaroClient, offer_id: int) -> dict[str, Any]:
    try:
        return client.get_offer(offer_id)
    except KeitaroError as error:
        if error.status_code == 404:
            raise ServiceError(404, "offer_not_found", offer_id=offer_id) from error
        raise


def geo_stream_name(countries: list[str]) -> str:
    shown = ", ".join(countries[:GEO_NAME_LIMIT])
    extra = len(countries) - GEO_NAME_LIMIT
    return f"Geo {shown} +{extra}" if extra > 0 else f"Geo {shown}"


def stream_campaign_id(stream: dict[str, Any]) -> int:
    return int(stream.get("campaign_id") or 0)


def log_operation(db: Session, campaign_id: int, action: str, details: dict[str, Any], stream_id: int | None = None) -> None:
    try:
        db.add(Operation(campaign_id=campaign_id, stream_id=stream_id, action=action, details=details))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to log operation %s for campaign %s", action, campaign_id)


def create_campaign(client: KeitaroClient, db: Session, settings: Settings, data: CampaignCreate) -> int:
    offer = ensure_offer_exists(client, data.offer_id)

    campaign = client.create_campaign(
        {
            "name": data.name,
            "type": "position",
            "state": "active",
            "domain_id": data.domain_id or settings.default_domain_id,
            "group_id": data.group_id or settings.default_group_id,
            "traffic_source_id": data.traffic_source_id or settings.default_traffic_source_id,
        }
    )
    if not isinstance(campaign, dict) or not campaign.get("id"):
        raise KeitaroError(502, key="campaign_without_id")
    campaign_id = int(campaign["id"])

    try:
        geo_stream = client.create_stream(
            {
                "campaign_id": campaign_id,
                "name": geo_stream_name(data.countries),
                "type": "regular",
                "schema": "redirect",
                "action_type": "http",
                "action_payload": settings.geo_redirect_url,
                "position": 1,
                "state": "active",
                "filters": [{"name": COUNTRY_FILTER, "mode": "accept", "payload": data.countries}],
            }
        )
        offers_stream = client.create_stream(
            {
                "campaign_id": campaign_id,
                "name": "Offers",
                "type": "default",
                "schema": "landings",
                "position": 2,
                "state": "active",
                "offers": [{"offer_id": data.offer_id, "share": 100, "state": "active"}],
            }
        )
        db.add(
            CampaignRecord(
                keitaro_id=campaign_id,
                name=data.name,
                alias=campaign.get("alias") or "",
                countries=data.countries,
                offer_id=data.offer_id,
                geo_stream_id=int(geo_stream["id"]),
                offers_stream_id=int(offers_stream["id"]),
            )
        )
        upsert_stream(db, campaign_id, geo_stream)
        upsert_stream(db, campaign_id, offers_stream)
        db.add(
            Operation(
                campaign_id=campaign_id,
                action="create_campaign",
                details={
                    "name": data.name,
                    "countries": data.countries,
                    "offer_id": data.offer_id,
                    "offer_name": offer.get("name"),
                },
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        try:
            client.delete_campaign(campaign_id)
        except KeitaroError:
            logger.exception("Failed to delete partially created campaign %s", campaign_id)
        raise
    return campaign_id


def rename_campaign(client: KeitaroClient, db: Session, campaign_id: int, name: str) -> dict[str, Any]:
    campaign = client.get_campaign(campaign_id)
    old_name = campaign.get("name") or ""
    if old_name == name:
        return campaign

    updated = client.update_campaign(campaign_id, {"name": name})
    if not isinstance(updated, dict) or "id" not in updated:
        updated = {**campaign, "name": name}
    record = db.scalar(select(CampaignRecord).where(CampaignRecord.keitaro_id == campaign_id))
    if record is not None:
        record.name = name
    log_operation(db, campaign_id, "rename_campaign", {"old_name": old_name, "name": name})
    return updated


def delete_campaign(client: KeitaroClient, db: Session, campaign_id: int) -> None:
    campaign = client.get_campaign(campaign_id)
    client.delete_campaign(campaign_id)
    record = db.scalar(select(CampaignRecord).where(CampaignRecord.keitaro_id == campaign_id))
    if record is not None:
        db.delete(record)
    for stream in db.scalars(select(StreamRecord).where(StreamRecord.campaign_id == campaign_id)):
        db.delete(stream)
    log_operation(db, campaign_id, "delete_campaign", {"name": campaign.get("name")})


def stream_filters(stream: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"name": item["name"], "mode": item.get("mode") or "accept", "payload": item.get("payload")}
        for item in stream.get("filters") or []
    ]


def payload_codes(payload: Any) -> list[str]:
    values = payload if isinstance(payload, list) else [payload] if payload else []
    return [str(value).upper() for value in values]


def get_geo_stream(client: KeitaroClient, stream_id: int) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    stream = client.get_stream(stream_id)
    filters = stream_filters(stream)
    indexes = [index for index, item in enumerate(filters) if item["name"] == COUNTRY_FILTER]
    if not indexes:
        raise ServiceError(400, "no_country_filter", stream_id=stream_id)
    if len(indexes) > 1:
        raise ServiceError(400, "many_country_filters", stream_id=stream_id)
    return stream, filters, indexes[0]


def save_countries(
    client: KeitaroClient,
    db: Session,
    stream_id: int,
    stream: dict[str, Any],
    filters: list[dict[str, Any]],
    index: int,
    countries: list[str],
    action: str,
    changed: list[str],
) -> dict[str, Any]:
    old = payload_codes(filters[index]["payload"])
    filters[index] = {**filters[index], "payload": countries}
    payload: dict[str, Any] = {"filters": filters}
    if stream.get("name") == geo_stream_name(old):
        payload["name"] = geo_stream_name(countries)

    campaign_id = stream_campaign_id(stream)
    updated = client.update_stream(stream_id, payload)
    if not isinstance(updated, dict) or "filters" not in updated:
        updated = client.get_stream(stream_id)

    record = db.scalar(select(CampaignRecord).where(CampaignRecord.keitaro_id == campaign_id))
    if record is not None and record.geo_stream_id == stream_id:
        record.countries = countries
    local, _ = upsert_stream(db, campaign_id, updated)
    log_operation(db, campaign_id, action, {"countries": changed, "result": countries}, stream_id)
    db.refresh(local)
    return stream_view(local)


def add_countries(client: KeitaroClient, db: Session, stream_id: int, codes: list[str]) -> dict[str, Any]:
    stream, filters, index = get_geo_stream(client, stream_id)
    current = payload_codes(filters[index]["payload"])
    new = [code for code in codes if code not in current]
    if not new:
        raise ServiceError(409, "countries_already_added")
    return save_countries(client, db, stream_id, stream, filters, index, current + new, "add_countries", new)


def remove_country(client: KeitaroClient, db: Session, stream_id: int, code: str) -> dict[str, Any]:
    code = code.strip().upper()
    stream, filters, index = get_geo_stream(client, stream_id)
    current = payload_codes(filters[index]["payload"])
    if code not in current:
        raise ServiceError(404, "country_not_in_filter", code=code)
    if len(current) == 1:
        raise ServiceError(400, "last_country")
    remaining = [item for item in current if item != code]
    return save_countries(client, db, stream_id, stream, filters, index, remaining, "remove_country", [code])
