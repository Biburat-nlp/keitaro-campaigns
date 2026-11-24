from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import drafts, services
from app.config import Settings, get_settings
from app.countries import COUNTRY_CODES
from app.db import get_db
from app.keitaro import KeitaroClient
from app.models import CampaignRecord, Operation
from app.schemas import (
    CampaignCreate,
    CampaignDetails,
    CampaignRename,
    CountriesAdd,
    OfferAdd,
    OperationOut,
    PinSet,
    ShareSet,
)

router = APIRouter(prefix="/api")


def get_keitaro(request: Request) -> KeitaroClient:
    return request.app.state.keitaro


Keitaro = Annotated[KeitaroClient, Depends(get_keitaro)]
Db = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/catalog")
def catalog(client: Keitaro, settings: AppSettings) -> dict[str, Any]:
    return {
        "domains": client.list_domains(),
        "groups": client.list_campaign_groups(),
        "traffic_sources": client.list_traffic_sources(),
        "countries": sorted(COUNTRY_CODES),
        "defaults": {
            "domain_id": settings.default_domain_id,
            "group_id": settings.default_group_id,
            "traffic_source_id": settings.default_traffic_source_id,
        },
    }


@router.get("/offers")
def offers(client: Keitaro) -> list[dict[str, Any]]:
    return [
        {
            "id": offer["id"],
            "name": offer.get("name") or "",
            "country": offer.get("country") or [],
            "state": offer.get("state"),
            "payout_value": offer.get("payout_value"),
            "payout_currency": offer.get("payout_currency"),
        }
        for offer in client.list_offers()
    ]


@router.get("/campaigns")
def campaigns(
    client: Keitaro,
    db: Db,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict[str, Any]]:
    items = client.list_campaigns(offset, limit)
    local_ids = set(db.scalars(select(CampaignRecord.keitaro_id)))
    return [{**item, "created_here": item.get("id") in local_ids} for item in items]


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
def create_campaign(data: CampaignCreate, client: Keitaro, db: Db, settings: AppSettings) -> CampaignDetails:
    campaign_id = services.create_campaign(client, db, settings, data)
    return campaign_details(campaign_id, client, db, settings)


@router.get("/campaigns/{campaign_id}")
def campaign_details(campaign_id: int, client: Keitaro, db: Db, settings: AppSettings) -> CampaignDetails:
    campaign = client.get_campaign(campaign_id)
    streams = drafts.ensure_synced(client, db, campaign_id)
    return details_response(campaign, streams, db, settings)


def details_response(campaign: dict[str, Any], streams: list, db: Session, settings: Settings) -> CampaignDetails:
    campaign_id = int(campaign["id"])
    created_here = db.scalar(select(CampaignRecord.id).where(CampaignRecord.keitaro_id == campaign_id)) is not None
    return CampaignDetails(
        campaign=campaign,
        streams=[drafts.stream_view(stream) for stream in streams],
        admin_url=f"{settings.keitaro_admin_url}{campaign_id}",
        created_here=created_here,
    )


@router.post("/campaigns/{campaign_id}/sync")
def sync_campaign(campaign_id: int, client: Keitaro, db: Db, settings: AppSettings) -> CampaignDetails:
    campaign = client.get_campaign(campaign_id)
    streams = drafts.sync_campaign(client, db, campaign_id)
    return details_response(campaign, streams, db, settings)


@router.patch("/campaigns/{campaign_id}")
def rename_campaign(campaign_id: int, data: CampaignRename, client: Keitaro, db: Db) -> dict[str, Any]:
    return services.rename_campaign(client, db, campaign_id, data.name)


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: int, client: Keitaro, db: Db) -> None:
    services.delete_campaign(client, db, campaign_id)


@router.get("/campaigns/{campaign_id}/operations")
def operations(campaign_id: int, db: Db) -> list[OperationOut]:
    rows = db.scalars(
        select(Operation).where(Operation.campaign_id == campaign_id).order_by(Operation.id.desc()).limit(100)
    )
    return [OperationOut.model_validate(row) for row in rows]


@router.post("/streams/{stream_id}/offers")
def add_offer(stream_id: int, data: OfferAdd, client: Keitaro, db: Db) -> dict[str, Any]:
    return drafts.add_offer(client, db, stream_id, data.offer_id)


@router.post("/streams/{stream_id}/offers/{offer_id}/remove")
def remove_offer(stream_id: int, offer_id: int, db: Db) -> dict[str, Any]:
    return drafts.remove_offer(db, stream_id, offer_id)


@router.post("/streams/{stream_id}/offers/{offer_id}/restore")
def restore_offer(stream_id: int, offer_id: int, db: Db) -> dict[str, Any]:
    return drafts.restore_offer(db, stream_id, offer_id)


@router.put("/streams/{stream_id}/offers/{offer_id}/share")
def set_share(stream_id: int, offer_id: int, data: ShareSet, db: Db) -> dict[str, Any]:
    return drafts.set_share(db, stream_id, offer_id, data.share)


@router.put("/streams/{stream_id}/offers/{offer_id}/pin")
def set_pinned(stream_id: int, offer_id: int, data: PinSet, db: Db) -> dict[str, Any]:
    return drafts.set_pinned(db, stream_id, offer_id, data.pinned)


@router.post("/streams/{stream_id}/publish")
def publish(stream_id: int, client: Keitaro, db: Db) -> dict[str, Any]:
    return drafts.publish(client, db, stream_id)


@router.post("/streams/{stream_id}/cancel")
def cancel(stream_id: int, db: Db) -> dict[str, Any]:
    return drafts.cancel_draft(db, stream_id)


@router.post("/streams/{stream_id}/countries")
def add_countries(stream_id: int, data: CountriesAdd, client: Keitaro, db: Db) -> dict[str, Any]:
    return services.add_countries(client, db, stream_id, data.countries)


@router.delete("/streams/{stream_id}/countries/{code}")
def remove_country(stream_id: int, code: str, client: Keitaro, db: Db) -> dict[str, Any]:
    return services.remove_country(client, db, stream_id, code)
