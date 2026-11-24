import json
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base


def make_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def migrate_campaign_countries(target: Engine) -> None:
    columns = {column["name"] for column in inspect(target).get_columns("campaigns")}
    if "countries" in columns:
        return
    with target.begin() as connection:
        connection.execute(text("ALTER TABLE campaigns ADD COLUMN countries JSON NOT NULL DEFAULT '[]'"))
        if "country" in columns:
            rows = connection.execute(text("SELECT id, country FROM campaigns")).all()
            if rows:
                connection.execute(
                    text("UPDATE campaigns SET countries = :countries WHERE id = :id"),
                    [{"id": row.id, "countries": json.dumps([row.country] if row.country else [])} for row in rows],
                )
            connection.execute(text("ALTER TABLE campaigns DROP COLUMN country"))


def migrate_committed_pins(target: Engine) -> None:
    columns = {column["name"] for column in inspect(target).get_columns("stream_offers")}
    if "committed_pinned" in columns:
        return
    with target.begin() as connection:
        connection.execute(text("ALTER TABLE stream_offers ADD COLUMN committed_pinned BOOLEAN NOT NULL DEFAULT 0"))
        connection.execute(text("UPDATE stream_offers SET committed_pinned = pinned"))


def init_db(target: Engine = engine) -> None:
    Base.metadata.create_all(target)
    migrate_campaign_countries(target)
    migrate_committed_pins(target)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
