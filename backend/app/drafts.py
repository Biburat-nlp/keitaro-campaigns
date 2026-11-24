from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ServiceError
from app.keitaro import KeitaroClient, KeitaroError
from app.models import Operation, StreamOffer, StreamRecord

ACTIVE = "active"
REMOVED = "removed"
OFFERS_SCHEMA = "landings"


def distribute_shares(count: int, total: int = 100) -> list[int]:
    if count <= 0:
        return []
    base, remainder = divmod(total, count)
    return [base + 1 if index < remainder else base for index in range(count)]


def parse_share(value: Any) -> int:
    try:
        return int(round(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def is_dirty(row: StreamOffer) -> bool:
    return row.committed_status is None or row.status != row.committed_status or row.share != row.committed_share


def has_intent(row: StreamOffer) -> bool:
    if row.committed_status is None or row.status != row.committed_status:
        return True
    return row.pinned and row.status == ACTIVE and row.share != row.committed_share


def stream_dirty(stream: StreamRecord) -> bool:
    return any(is_dirty(row) for row in stream.offers)


def active_rows(stream: StreamRecord) -> list[StreamOffer]:
    return [row for row in stream.offers if row.status == ACTIVE]


def rebalance(stream: StreamRecord) -> None:
    for row in stream.offers:
        if row.status != ACTIVE:
            row.share = 0
            row.pinned = False
    active = active_rows(stream)
    pinned_total = sum(row.share for row in active if row.pinned)
    if pinned_total > 100:
        raise ServiceError(400, "pinned_over_100", total=pinned_total)
    free = [row for row in active if not row.pinned]
    for row, share in zip(free, distribute_shares(len(free), 100 - pinned_total)):
        row.share = share


def offer_view(row: StreamOffer) -> dict[str, Any]:
    return {
        "offer_id": row.offer_id,
        "share": row.share,
        "pinned": row.pinned,
        "status": row.status,
        "state": row.keitaro_state,
        "committed_status": row.committed_status,
        "committed_share": row.committed_share,
        "is_new": row.committed_status is None,
        "dirty": is_dirty(row),
    }


def stream_view(stream: StreamRecord) -> dict[str, Any]:
    rows = sorted(stream.offers, key=lambda row: (row.status != ACTIVE, -row.share, row.id))
    active = active_rows(stream)
    return {
        **{key: value for key, value in (stream.data or {}).items() if key != "offers"},
        "id": stream.id,
        "campaign_id": stream.campaign_id,
        "name": stream.name,
        "type": stream.type,
        "schema": stream.schema,
        "position": stream.position,
        "state": stream.state,
        "offers": [offer_view(row) for row in rows],
        "dirty": stream_dirty(stream),
        "total": sum(row.share for row in active),
        "active_count": len(active),
        "synced_at": as_utc(stream.synced_at).isoformat() if stream.synced_at else None,
    }


def upsert_stream(db: Session, campaign_id: int, data: dict[str, Any]) -> tuple[StreamRecord, list[int]]:
    stream_id = int(data["id"])
    stream = db.get(StreamRecord, stream_id)
    if stream is None:
        stream = StreamRecord(id=stream_id, campaign_id=campaign_id, offers=[])
        db.add(stream)
    stream.campaign_id = campaign_id
    stream.name = data.get("name") or ""
    stream.type = data.get("type") or ""
    stream.schema = data.get("schema") or ""
    stream.position = int(data.get("position") or 0)
    stream.state = data.get("state") or "active"
    stream.data = {key: value for key, value in data.items() if key != "offers"}
    stream.synced_at = datetime.now(timezone.utc)
    vanished = sync_offers(stream, data.get("offers") or [])
    if any(has_intent(row) for row in stream.offers):
        try:
            rebalance(stream)
        except ServiceError:
            pass
    return stream, vanished


def sync_offers(stream: StreamRecord, remote_offers: list[dict[str, Any]]) -> list[int]:
    remote = {int(item["offer_id"]): item for item in remote_offers if item.get("offer_id") is not None}
    rows = {row.offer_id: row for row in stream.offers}
    vanished: list[int] = []

    for offer_id, item in remote.items():
        share = parse_share(item.get("share"))
        state = item.get("state") or ACTIVE
        row = rows.get(offer_id)
        if row is None:
            stream.offers.append(
                StreamOffer(
                    offer_id=offer_id,
                    status=ACTIVE,
                    share=share,
                    pinned=False,
                    keitaro_state=state,
                    committed_status=ACTIVE,
                    committed_share=share,
                    committed_pinned=False,
                )
            )
            continue
        clean = not has_intent(row)
        row.committed_status = ACTIVE
        row.committed_share = share
        row.keitaro_state = state
        if clean:
            row.status = ACTIVE
            row.share = share

    for offer_id, row in rows.items():
        if offer_id in remote or row.committed_status != ACTIVE:
            continue
        clean = not has_intent(row)
        row.committed_status = REMOVED
        row.committed_share = 0
        if clean:
            row.status = REMOVED
            row.share = 0
            row.pinned = False
        vanished.append(offer_id)
    return vanished


def log(db: Session, campaign_id: int, action: str, details: dict[str, Any], stream_id: int | None = None) -> None:
    db.add(Operation(campaign_id=campaign_id, stream_id=stream_id, action=action, details=details))


def shares_map(stream: StreamRecord) -> dict[str, int]:
    return {str(row.offer_id): row.share for row in active_rows(stream)}


def campaign_streams(db: Session, campaign_id: int) -> list[StreamRecord]:
    return list(
        db.scalars(
            select(StreamRecord).where(StreamRecord.campaign_id == campaign_id).order_by(StreamRecord.position, StreamRecord.id)
        )
    )


def sync_campaign(client: KeitaroClient, db: Session, campaign_id: int) -> list[StreamRecord]:
    remote = client.list_streams(campaign_id)
    if not isinstance(remote, list):
        raise KeitaroError(502, key="unexpected_streams")
    seen: set[int] = set()
    vanished: dict[str, list[int]] = {}
    for data in remote:
        stream, gone = upsert_stream(db, campaign_id, data)
        seen.add(stream.id)
        if gone:
            vanished[str(stream.id)] = gone
    for stream in campaign_streams(db, campaign_id):
        if stream.id not in seen:
            db.delete(stream)
    details: dict[str, Any] = {"streams": len(seen)}
    if vanished:
        details["vanished"] = vanished
    log(db, campaign_id, "sync", details)
    db.commit()
    return campaign_streams(db, campaign_id)


def ensure_synced(client: KeitaroClient, db: Session, campaign_id: int) -> list[StreamRecord]:
    streams = campaign_streams(db, campaign_id)
    return streams if streams else sync_campaign(client, db, campaign_id)


def get_offers_stream(db: Session, stream_id: int) -> StreamRecord:
    stream = db.get(StreamRecord, stream_id)
    if stream is None:
        raise ServiceError(404, "stream_not_loaded", stream_id=stream_id)
    if stream.schema != OFFERS_SCHEMA:
        raise ServiceError(400, "stream_without_offers", stream_id=stream_id, schema=stream.schema)
    return stream


def find_row(stream: StreamRecord, offer_id: int) -> StreamOffer:
    for row in stream.offers:
        if row.offer_id == offer_id:
            return row
    raise ServiceError(404, "offer_not_in_stream", offer_id=offer_id)


def remember_pins(stream: StreamRecord) -> None:
    for row in stream.offers:
        row.committed_pinned = row.pinned


def finish(db: Session, stream: StreamRecord, action: str, details: dict[str, Any]) -> dict[str, Any]:
    if not stream_dirty(stream):
        remember_pins(stream)
    log(db, stream.campaign_id, action, {**details, "shares": shares_map(stream)}, stream.id)
    db.commit()
    db.refresh(stream)
    return stream_view(stream)


def add_offer(client: KeitaroClient, db: Session, stream_id: int, offer_id: int) -> dict[str, Any]:
    stream = get_offers_stream(db, stream_id)
    existing = next((row for row in stream.offers if row.offer_id == offer_id), None)
    if existing is not None and existing.status == ACTIVE:
        raise ServiceError(409, "offer_already_in_stream", offer_id=offer_id)
    if existing is not None:
        return restore_offer(db, stream_id, offer_id)

    try:
        offer = client.get_offer(offer_id)
    except KeitaroError as error:
        if error.status_code == 404:
            raise ServiceError(404, "offer_not_found", offer_id=offer_id) from error
        raise
    stream.offers.append(
        StreamOffer(offer_id=offer_id, status=ACTIVE, share=0, pinned=False, committed_status=None, committed_share=0)
    )
    rebalance(stream)
    return finish(db, stream, "add_offer", {"offer_id": offer_id, "offer_name": offer.get("name")})


def remove_offer(db: Session, stream_id: int, offer_id: int) -> dict[str, Any]:
    stream = get_offers_stream(db, stream_id)
    row = find_row(stream, offer_id)
    if row.status == REMOVED:
        raise ServiceError(409, "offer_already_removed", offer_id=offer_id)
    if row.committed_status is None:
        stream.offers.remove(row)
    else:
        row.status = REMOVED
    rebalance(stream)
    return finish(db, stream, "remove_offer", {"offer_id": offer_id})


def restore_offer(db: Session, stream_id: int, offer_id: int) -> dict[str, Any]:
    stream = get_offers_stream(db, stream_id)
    row = find_row(stream, offer_id)
    if row.status == ACTIVE:
        raise ServiceError(409, "offer_already_active", offer_id=offer_id)
    row.status = ACTIVE
    row.pinned = False
    rebalance(stream)
    return finish(db, stream, "restore_offer", {"offer_id": offer_id})


def set_share(db: Session, stream_id: int, offer_id: int, share: int) -> dict[str, Any]:
    stream = get_offers_stream(db, stream_id)
    row = find_row(stream, offer_id)
    if row.status != ACTIVE:
        raise ServiceError(400, "share_only_active")
    previous = (row.share, row.pinned)
    row.share = share
    row.pinned = True
    try:
        rebalance(stream)
    except ServiceError:
        row.share, row.pinned = previous
        db.rollback()
        raise
    return finish(db, stream, "set_share", {"offer_id": offer_id, "share": share})


def set_pinned(db: Session, stream_id: int, offer_id: int, pinned: bool) -> dict[str, Any]:
    stream = get_offers_stream(db, stream_id)
    row = find_row(stream, offer_id)
    if row.status != ACTIVE:
        raise ServiceError(400, "pin_only_active")
    if row.pinned == pinned:
        return stream_view(stream)
    row.pinned = pinned
    if pinned:
        pinned_total = sum(item.share for item in active_rows(stream) if item.pinned)
        if pinned_total > 100:
            db.rollback()
            raise ServiceError(400, "pinned_over_100", total=pinned_total)
    else:
        rebalance(stream)
    return finish(db, stream, "pin" if pinned else "unpin", {"offer_id": offer_id})


def cancel_draft(db: Session, stream_id: int) -> dict[str, Any]:
    stream = get_offers_stream(db, stream_id)
    if not stream_dirty(stream):
        return stream_view(stream)
    for row in list(stream.offers):
        if row.committed_status is None:
            stream.offers.remove(row)
            continue
        row.status = row.committed_status
        row.share = row.committed_share
        row.pinned = row.committed_pinned and row.status == ACTIVE
    return finish(db, stream, "cancel", {})


def publish(client: KeitaroClient, db: Session, stream_id: int) -> dict[str, Any]:
    stream = get_offers_stream(db, stream_id)
    if not stream_dirty(stream):
        raise ServiceError(400, "nothing_to_publish")
    active = active_rows(stream)
    if not active:
        raise ServiceError(400, "need_active_offer")
    total = sum(row.share for row in active)
    if total != 100:
        raise ServiceError(400, "shares_sum", total=total)

    remote = client.get_stream(stream_id)
    remote_shares = {
        int(item["offer_id"]): parse_share(item.get("share"))
        for item in remote.get("offers") or []
        if item.get("offer_id") is not None
    }
    committed = {row.offer_id: row.committed_share for row in stream.offers if row.committed_status == ACTIVE}
    if remote_shares != committed:
        raise ServiceError(409, "stream_changed")

    payload = [{"offer_id": row.offer_id, "share": row.share, "state": row.keitaro_state or ACTIVE} for row in active]
    updated = client.update_stream(stream_id, {"offers": payload})
    if not isinstance(updated, dict) or "offers" not in updated:
        updated = client.get_stream(stream_id)

    for row in stream.offers:
        row.committed_status = row.status
        row.committed_share = row.share
    stream.data = {key: value for key, value in updated.items() if key != "offers"}
    stream.name = updated.get("name") or stream.name
    stream.synced_at = datetime.now(timezone.utc)
    sync_offers(stream, updated.get("offers") or [])
    return finish(db, stream, "publish", {})
