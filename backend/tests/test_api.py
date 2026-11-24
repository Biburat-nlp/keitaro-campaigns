import pytest
from sqlalchemy import create_engine, inspect, text

from app.db import init_db
from app.drafts import distribute_shares


@pytest.mark.parametrize(
    ("count", "expected"),
    [(1, [100]), (2, [50, 50]), (3, [34, 33, 33]), (6, [17, 17, 17, 17, 16, 16]), (0, [])],
)
def test_distribute_shares(count, expected):
    assert distribute_shares(count) == expected
    assert sum(expected) == (100 if count else 0)


def create(client, **overrides):
    payload = {"name": "Test campaign", "countries": ["au"], "offer_id": 18001, **overrides}
    return client.post("/api/campaigns", json=payload)


def offers_of(stream):
    return {item["offer_id"]: item["share"] for item in stream["offers"]}


def test_create_campaign_builds_two_streams(client, fake):
    response = create(client)
    assert response.status_code == 201
    data = response.json()

    campaign = data["campaign"]
    assert campaign["name"] == "Test campaign"
    assert (campaign["domain_id"], campaign["group_id"], campaign["traffic_source_id"]) == (1813, 10332, 836)

    geo, offers = data["streams"]
    assert geo["type"] == "regular" and geo["schema"] == "redirect"
    assert geo["action_type"] == "http" and geo["action_payload"] == "https://google.com"
    assert geo["filters"] == [{"name": "country", "mode": "accept", "payload": ["AU"]}]
    assert offers["type"] == "default" and offers["schema"] == "landings"
    assert offers_of(offers) == {18001: 100}
    assert data["created_here"] is True

    history = client.get(f"/api/campaigns/{campaign['id']}/operations").json()
    assert [item["action"] for item in history] == ["create_campaign"]


def test_create_campaign_validates_input(client, fake):
    assert create(client, countries=["ZZ"]).status_code == 422
    assert create(client, countries=[]).status_code == 422
    assert create(client, countries=["AU", " "]).status_code == 422
    assert create(client, name="   ").status_code == 422
    response = create(client, offer_id=99999)
    assert response.status_code == 404
    assert "99999" in response.json()["detail"]
    assert fake.campaigns == {}


def test_create_campaign_rolls_back_when_stream_fails(client, fake):
    fake.fail_stream_create = True
    response = create(client)
    assert response.status_code == 502
    assert fake.campaigns == {}
    assert client.get("/api/campaigns").json() == []


def test_delete_campaign(client, fake):
    campaign_id = create(client).json()["campaign"]["id"]
    assert client.delete(f"/api/campaigns/{campaign_id}").status_code == 204
    assert fake.campaigns == {}
    assert client.get(f"/api/campaigns/{campaign_id}").status_code == 404


def test_rename_campaign(client, fake):
    campaign_id = create(client).json()["campaign"]["id"]
    url = f"/api/campaigns/{campaign_id}"

    response = client.patch(url, json={"name": "  New name  "})
    assert response.status_code == 200
    assert response.json()["name"] == "New name"
    assert fake.campaigns[campaign_id]["name"] == "New name"
    assert client.get(url).json()["campaign"]["name"] == "New name"

    puts_before = fake.requests.count(("PUT", url.removeprefix("/api")))
    assert client.patch(url, json={"name": "New name"}).status_code == 200
    assert fake.requests.count(("PUT", url.removeprefix("/api"))) == puts_before

    assert client.patch(url, json={"name": "   "}).status_code == 422
    assert client.patch("/api/campaigns/99999", json={"name": "x"}).status_code == 404

    history = client.get(f"{url}/operations").json()
    assert history[0]["action"] == "rename_campaign"
    assert history[0]["details"] == {"old_name": "Test campaign", "name": "New name"}


def test_create_campaign_with_several_countries(client, fake):
    data = create(client, countries=["au", "NZ", "au", " gb "]).json()
    geo = data["streams"][0]
    assert geo["name"] == "Geo AU, NZ, GB"
    assert geo["filters"] == [{"name": "country", "mode": "accept", "payload": ["AU", "NZ", "GB"]}]

    many = create(client, countries=["AU", "NZ", "GB", "US", "CA", "DE", "FR"]).json()
    assert many["streams"][0]["name"] == "Geo AU, NZ, GB, US, CA +2"


def geo_codes(stream):
    return [item for item in stream["filters"] if item["name"] == "country"][0]["payload"]


def test_add_and_remove_countries(client, fake):
    data = create(client).json()
    campaign_id, geo_id = data["campaign"]["id"], data["streams"][0]["id"]
    fake.streams[geo_id]["filters"].append({"id": 7, "stream_id": geo_id, "name": "os", "mode": "reject", "payload": ["iOS"]})
    url = f"/api/streams/{geo_id}/countries"

    stream = client.post(url, json={"countries": ["nz", "AU", "GB"]}).json()
    assert geo_codes(stream) == ["AU", "NZ", "GB"]
    assert stream["name"] == "Geo AU, NZ, GB"
    assert {"name": "os", "mode": "reject", "payload": ["iOS"]} in fake.streams[geo_id]["filters"]

    stream = client.delete(f"{url}/au").json()
    assert geo_codes(stream) == ["NZ", "GB"]
    assert stream["name"] == "Geo NZ, GB"

    history = client.get(f"/api/campaigns/{campaign_id}/operations").json()
    assert [item["action"] for item in history[:2]] == ["remove_country", "add_countries"]
    assert history[0]["details"] == {"countries": ["AU"], "result": ["NZ", "GB"]}
    assert history[1]["details"] == {"countries": ["NZ", "GB"], "result": ["AU", "NZ", "GB"]}


def test_custom_stream_name_is_kept(client, fake):
    geo_id = create(client).json()["streams"][0]["id"]
    fake.streams[geo_id]["name"] = "Australia to Google"
    stream = client.post(f"/api/streams/{geo_id}/countries", json={"countries": ["NZ"]}).json()
    assert stream["name"] == "Australia to Google"


def test_country_edit_errors(client, fake):
    data = create(client).json()
    geo_id, offers_id = data["streams"][0]["id"], data["streams"][1]["id"]
    url = f"/api/streams/{geo_id}/countries"

    assert client.post(url, json={"countries": ["AU"]}).status_code == 409
    assert client.post(url, json={"countries": ["ZZ"]}).status_code == 422
    assert client.post(f"/api/streams/{offers_id}/countries", json={"countries": ["NZ"]}).status_code == 400
    assert client.delete(f"{url}/NZ").status_code == 404
    assert client.delete(f"{url}/AU").status_code == 400
    assert geo_codes(fake.streams[geo_id]) == ["AU"]

    fake.streams[geo_id]["filters"].append({"name": "country", "mode": "reject", "payload": ["NZ"]})
    assert client.post(url, json={"countries": ["GB"]}).status_code == 400


def test_migration_moves_single_country_to_list(tmp_path):
    old = create_engine(f"sqlite:///{(tmp_path / 'old.db').as_posix()}")
    with old.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE campaigns (id INTEGER PRIMARY KEY, keitaro_id INTEGER NOT NULL, name VARCHAR(255) NOT NULL, "
                "alias VARCHAR(255) NOT NULL, country VARCHAR(2) NOT NULL, offer_id INTEGER NOT NULL, "
                "geo_stream_id INTEGER NOT NULL, offers_stream_id INTEGER NOT NULL, created_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            text("INSERT INTO campaigns VALUES (1, 28, 'old', 'abc', 'AU', 18001, 49, 50, '2026-11-24 09:17:03')")
        )

    init_db(old)
    init_db(old)

    with old.connect() as connection:
        pin_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(stream_offers)"))}
    assert "committed_pinned" in pin_columns

    columns = {column["name"] for column in inspect(old).get_columns("campaigns")}
    assert "country" not in columns and "countries" in columns
    with old.connect() as connection:
        assert connection.execute(text("SELECT countries FROM campaigns")).scalar_one() == '["AU"]'


def test_operations_are_returned_in_utc(client, fake):
    campaign_id = create(client).json()["campaign"]["id"]
    created_at = client.get(f"/api/campaigns/{campaign_id}/operations").json()[0]["created_at"]
    assert created_at.endswith(("Z", "+00:00"))


def test_create_rolls_back_when_db_write_fails(client, fake, monkeypatch):
    from sqlalchemy.orm import Session

    def broken_commit(self):
        raise RuntimeError("db is down")

    monkeypatch.setattr(Session, "commit", broken_commit)
    with pytest.raises(RuntimeError):
        create(client)
    assert fake.campaigns == {}
