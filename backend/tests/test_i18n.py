def create(client, headers=None, **overrides):
    payload = {"name": "Lang campaign", "countries": ["AU"], "offer_id": 18001, **overrides}
    return client.post("/api/campaigns", json=payload, headers=headers or {})


def test_errors_default_to_russian(client, fake):
    assert create(client, offer_id=99999).json()["detail"] == "Оффер 99999 не найден"
    assert create(client, countries=["ZZ"]).json()["detail"] == "Неизвестный код страны: ZZ"


def test_errors_follow_accept_language(client, fake):
    english = {"Accept-Language": "en-US,en;q=0.9"}
    assert create(client, english, offer_id=99999).json()["detail"] == "Offer 99999 not found"
    assert create(client, english, countries=["ZZ"]).json()["detail"] == "Unknown country code: ZZ"
    assert create(client, english, name="  ").json()["detail"] == "Name can't be empty"

    response = client.post("/api/campaigns", json={"countries": ["AU"]}, headers=english)
    assert response.status_code == 422
    assert response.json()["detail"] == "name: required; offer: required"


def test_russian_validation_messages(client, fake):
    response = client.post("/api/campaigns", json={"name": "x", "countries": ["AU"], "offer_id": "abc"})
    assert response.json()["detail"] == "оффер: неверный формат"


def test_service_errors_are_translated(client, fake):
    data = create(client).json()
    stream_id = next(s["id"] for s in data["streams"] if s["schema"] == "landings")
    url = f"/api/streams/{stream_id}/publish"
    assert client.post(url, headers={"Accept-Language": "en"}).json()["detail"] == "There are no unpublished changes"
    assert client.post(url, headers={"Accept-Language": "ru"}).json()["detail"] == "Нет неопубликованных изменений"


def test_upstream_keitaro_errors_keep_their_text(client, fake):
    response = client.get("/api/campaigns/424242", headers={"Accept-Language": "en"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Keitaro: Not found"
