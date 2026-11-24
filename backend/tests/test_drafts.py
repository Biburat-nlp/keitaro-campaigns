import pytest


def create(client, **overrides):
    payload = {"name": "Draft campaign", "countries": ["AU"], "offer_id": 18001, **overrides}
    response = client.post("/api/campaigns", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def setup(client, fake):
    data = create(client)
    campaign_id = data["campaign"]["id"]
    stream_id = next(s["id"] for s in data["streams"] if s["schema"] == "landings")
    return campaign_id, stream_id


def active(stream):
    return {item["offer_id"]: item["share"] for item in stream["offers"] if item["status"] == "active"}


def removed(stream):
    return [item["offer_id"] for item in stream["offers"] if item["status"] == "removed"]


def keitaro_offers(fake, stream_id):
    return {item["offer_id"]: item["share"] for item in fake.streams[stream_id]["offers"]}


def puts(fake):
    return [path for method, path in fake.requests if method == "PUT"]


def add(client, stream_id, offer_id):
    return client.post(f"/api/streams/{stream_id}/offers", json={"offer_id": offer_id})


def act(client, stream_id, offer_id, action):
    return client.post(f"/api/streams/{stream_id}/offers/{offer_id}/{action}")


def publish(client, stream_id):
    return client.post(f"/api/streams/{stream_id}/publish")


def offers_stream(client, campaign_id, stream_id):
    streams = client.get(f"/api/campaigns/{campaign_id}").json()["streams"]
    return next(s for s in streams if s["id"] == stream_id)


def synced_stream(client, campaign_id, stream_id):
    streams = client.post(f"/api/campaigns/{campaign_id}/sync").json()["streams"]
    return next(s for s in streams if s["id"] == stream_id)


def test_new_campaign_streams_are_stored_and_clean(client, fake, setup):
    campaign_id, stream_id = setup
    stream = offers_stream(client, campaign_id, stream_id)
    assert stream["dirty"] is False
    assert active(stream) == {18001: 100}
    assert stream["total"] == 100


def test_add_is_a_draft_until_published(client, fake, setup):
    _, stream_id = setup
    puts_before = len(puts(fake))

    stream = add(client, stream_id, 18002).json()
    assert stream["dirty"] is True
    assert active(stream) == {18001: 50, 18002: 50}
    stream = add(client, stream_id, 18003).json()
    assert active(stream) == {18001: 34, 18002: 33, 18003: 33}
    assert sorted(item["offer_id"] for item in stream["offers"] if item["is_new"]) == [18002, 18003]

    assert len(puts(fake)) == puts_before
    assert keitaro_offers(fake, stream_id) == {18001: 100}

    stream = publish(client, stream_id).json()
    assert stream["dirty"] is False
    assert keitaro_offers(fake, stream_id) == {18001: 34, 18002: 33, 18003: 33}


def test_cancel_drops_unpublished_offers(client, fake, setup):
    _, stream_id = setup
    add(client, stream_id, 18002)
    add(client, stream_id, 18003)

    stream = client.post(f"/api/streams/{stream_id}/cancel").json()
    assert stream["dirty"] is False
    assert active(stream) == {18001: 100}
    assert [item["offer_id"] for item in stream["offers"]] == [18001]
    assert keitaro_offers(fake, stream_id) == {18001: 100}


def test_remove_keeps_offer_in_archive_and_bring_back_returns_it(client, fake, setup):
    campaign_id, stream_id = setup
    add(client, stream_id, 18002)
    add(client, stream_id, 18003)
    publish(client, stream_id)

    stream = act(client, stream_id, 18002, "remove").json()
    assert stream["dirty"] is True
    assert active(stream) == {18001: 50, 18003: 50}
    assert removed(stream) == [18002]
    assert stream["offers"][-1]["share"] == 0

    publish(client, stream_id)
    assert keitaro_offers(fake, stream_id) == {18001: 50, 18003: 50}
    stream = offers_stream(client, campaign_id, stream_id)
    assert removed(stream) == [18002]
    assert stream["dirty"] is False

    stream = act(client, stream_id, 18002, "restore").json()
    assert stream["dirty"] is True
    assert active(stream) == {18001: 34, 18002: 33, 18003: 33}
    publish(client, stream_id)
    assert keitaro_offers(fake, stream_id) == {18001: 34, 18002: 33, 18003: 33}


def test_removing_unpublished_offer_deletes_it(client, fake, setup):
    _, stream_id = setup
    add(client, stream_id, 18002)
    stream = act(client, stream_id, 18002, "remove").json()
    assert [item["offer_id"] for item in stream["offers"]] == [18001]
    assert stream["dirty"] is False


def test_cancel_restores_removed_offer(client, fake, setup):
    _, stream_id = setup
    add(client, stream_id, 18002)
    publish(client, stream_id)
    act(client, stream_id, 18002, "remove")
    stream = client.post(f"/api/streams/{stream_id}/cancel").json()
    assert active(stream) == {18001: 50, 18002: 50}
    assert stream["dirty"] is False


def test_adding_removed_offer_brings_it_back(client, fake, setup):
    _, stream_id = setup
    add(client, stream_id, 18002)
    publish(client, stream_id)
    act(client, stream_id, 18002, "remove")
    stream = add(client, stream_id, 18002).json()
    assert active(stream) == {18001: 50, 18002: 50}
    assert stream["dirty"] is False


def test_sync_marks_offers_deleted_in_keitaro_as_removed(client, fake, setup):
    campaign_id, stream_id = setup
    add(client, stream_id, 18002)
    add(client, stream_id, 18003)
    publish(client, stream_id)

    fake.streams[stream_id]["offers"] = [
        {"offer_id": 18001, "share": 25, "state": "active"},
        {"offer_id": 18004, "share": 75, "state": "active"},
    ]
    stream = synced_stream(client, campaign_id, stream_id)

    assert active(stream) == {18001: 25, 18004: 75}
    assert sorted(removed(stream)) == [18002, 18003]
    assert stream["dirty"] is False

    history = client.get(f"/api/campaigns/{campaign_id}/operations").json()["items"]
    assert history[0]["action"] == "sync"
    assert sorted(history[0]["details"]["vanished"][str(stream_id)]) == [18002, 18003]


def test_sync_keeps_local_draft(client, fake, setup):
    campaign_id, stream_id = setup
    add(client, stream_id, 18002)
    stream = synced_stream(client, campaign_id, stream_id)
    assert stream["dirty"] is True
    assert active(stream) == {18001: 50, 18002: 50}


def test_fractional_share_from_keitaro_is_rounded(client, fake, setup):
    campaign_id, stream_id = setup
    fake.streams[stream_id]["offers"][0]["share"] = "99.6"
    stream = synced_stream(client, campaign_id, stream_id)
    assert active(stream) == {18001: 100}


def test_pinned_share_survives_rebalancing(client, fake, setup):
    _, stream_id = setup
    for offer_id in (18002, 18003):
        add(client, stream_id, offer_id)
    publish(client, stream_id)

    stream = client.put(f"/api/streams/{stream_id}/offers/18002/share", json={"share": 25}).json()
    assert active(stream) == {18001: 38, 18002: 25, 18003: 37}
    assert next(item for item in stream["offers"] if item["offer_id"] == 18002)["pinned"] is True

    stream = add(client, stream_id, 18004).json()
    assert active(stream) == {18001: 25, 18002: 25, 18003: 25, 18004: 25}
    stream = act(client, stream_id, 18001, "remove").json()
    assert active(stream) == {18002: 25, 18003: 38, 18004: 37}

    stream = client.put(f"/api/streams/{stream_id}/offers/18002/pin", json={"pinned": False}).json()
    assert active(stream) == {18002: 34, 18003: 33, 18004: 33}


def test_pin_keeps_current_share(client, fake, setup):
    _, stream_id = setup
    add(client, stream_id, 18002)
    stream = client.put(f"/api/streams/{stream_id}/offers/18001/pin", json={"pinned": True}).json()
    assert active(stream) == {18001: 50, 18002: 50}
    stream = add(client, stream_id, 18003).json()
    assert active(stream) == {18001: 50, 18002: 25, 18003: 25}


def test_cancel_reverts_pins_made_in_draft(client, fake, setup):
    _, stream_id = setup
    client.put(f"/api/streams/{stream_id}/offers/18001/share", json={"share": 90})
    stream = client.post(f"/api/streams/{stream_id}/cancel").json()
    assert stream["offers"][0]["pinned"] is False
    stream = add(client, stream_id, 18002).json()
    assert active(stream) == {18001: 50, 18002: 50}


def test_pin_on_clean_stream_survives_cancel(client, fake, setup):
    _, stream_id = setup
    add(client, stream_id, 18002)
    publish(client, stream_id)
    stream = client.put(f"/api/streams/{stream_id}/offers/18001/pin", json={"pinned": True}).json()
    assert stream["dirty"] is False
    add(client, stream_id, 18003)
    stream = client.post(f"/api/streams/{stream_id}/cancel").json()
    assert next(item for item in stream["offers"] if item["offer_id"] == 18001)["pinned"] is True
    stream = add(client, stream_id, 18003).json()
    assert active(stream) == {18001: 50, 18002: 25, 18003: 25}


def test_pinned_total_cannot_exceed_100(client, fake, setup):
    campaign_id, stream_id = setup
    add(client, stream_id, 18002)
    add(client, stream_id, 18003)
    client.put(f"/api/streams/{stream_id}/offers/18001/share", json={"share": 60})
    response = client.put(f"/api/streams/{stream_id}/offers/18002/share", json={"share": 50})
    assert response.status_code == 400
    assert active(offers_stream(client, campaign_id, stream_id)) == {18001: 60, 18002: 20, 18003: 20}


def test_publish_validation(client, fake, setup):
    _, stream_id = setup
    assert publish(client, stream_id).status_code == 400

    add(client, stream_id, 18002)
    client.put(f"/api/streams/{stream_id}/offers/18001/share", json={"share": 30})
    client.put(f"/api/streams/{stream_id}/offers/18002/share", json={"share": 30})
    response = publish(client, stream_id)
    assert response.status_code == 400
    assert "60%" in response.json()["detail"]

    act(client, stream_id, 18001, "remove")
    act(client, stream_id, 18002, "remove")
    assert publish(client, stream_id).status_code == 400
    assert keitaro_offers(fake, stream_id) == {18001: 100}


def test_publish_detects_changes_made_in_keitaro(client, fake, setup):
    campaign_id, stream_id = setup
    add(client, stream_id, 18002)
    fake.streams[stream_id]["offers"] = [{"offer_id": 18003, "share": 100, "state": "active"}]

    response = publish(client, stream_id)
    assert response.status_code == 409
    assert keitaro_offers(fake, stream_id) == {18003: 100}

    synced_stream(client, campaign_id, stream_id)
    assert publish(client, stream_id).status_code == 200
    assert keitaro_offers(fake, stream_id) == {18003: 50, 18002: 50}


def test_draft_errors(client, fake, setup):
    campaign_id, stream_id = setup
    streams = client.get(f"/api/campaigns/{campaign_id}").json()["streams"]
    geo_id = next(s["id"] for s in streams if s["schema"] == "redirect")
    assert add(client, stream_id, 18001).status_code == 409
    assert add(client, stream_id, 99999).status_code == 404
    assert add(client, geo_id, 18002).status_code == 400
    assert act(client, stream_id, 18002, "remove").status_code == 404
    assert act(client, stream_id, 18001, "restore").status_code == 409
    assert add(client, 424242, 18002).status_code == 404
    assert client.put(f"/api/streams/{stream_id}/offers/18001/share", json={"share": 101}).status_code == 422


def test_streams_deleted_in_keitaro_disappear_after_sync(client, fake, setup):
    campaign_id, stream_id = setup
    del fake.streams[stream_id]
    data = client.post(f"/api/campaigns/{campaign_id}/sync").json()
    assert [s["schema"] for s in data["streams"]] == ["redirect"]
