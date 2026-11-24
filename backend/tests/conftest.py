import json
import os
import re
import tempfile
from pathlib import Path

os.environ["DATABASE_URL"] = f"sqlite:///{(Path(tempfile.mkdtemp()) / 'test.db').as_posix()}"
os.environ["KEITARO_API_KEY"] = "test-key"

import httpx
import pytest
from fastapi.testclient import TestClient

from app.db import engine
from app.keitaro import KeitaroClient
from app.main import create_app
from app.models import Base


class FakeKeitaro:
    def __init__(self):
        self.offers = {
            18001: {"id": 18001, "name": "18001 Detoxin", "country": ["CL"], "state": "active"},
            18002: {"id": 18002, "name": "18002 Fungiclean", "country": ["TH"], "state": "active"},
            18003: {"id": 18003, "name": "18003 Cardio", "country": ["RO"], "state": "active"},
            18004: {"id": 18004, "name": "18004 Slim", "country": ["RO"], "state": "active"},
        }
        self.campaigns: dict[int, dict] = {}
        self.streams: dict[int, dict] = {}
        self.next_id = 100
        self.fail_stream_create = False
        self.requests: list[tuple[str, str]] = []

    def _id(self) -> int:
        self.next_id += 1
        return self.next_id

    def handler(self, request: httpx.Request) -> httpx.Response:
        assert request.headers["Api-Key"] == "test-key"
        method, path = request.method, request.url.path.removeprefix("/admin_api/v1")
        self.requests.append((method, path))
        body = json.loads(request.content) if request.content else {}

        if method == "GET" and path == "/offers":
            return httpx.Response(200, json=list(self.offers.values()))
        if match := re.fullmatch(r"/offers/(\d+)", path):
            offer = self.offers.get(int(match[1]))
            return httpx.Response(200, json=offer) if offer else httpx.Response(404, json={"error": "Not found"})
        if method == "GET" and path == "/campaigns":
            return httpx.Response(200, json=sorted(self.campaigns.values(), key=lambda c: -c["id"]))
        if method == "POST" and path == "/campaigns":
            campaign = {"id": self._id(), "alias": "abc123", "state": "active", **body}
            self.campaigns[campaign["id"]] = campaign
            return httpx.Response(200, json=campaign)
        if match := re.fullmatch(r"/campaigns/(\d+)", path):
            campaign_id = int(match[1])
            if campaign_id not in self.campaigns:
                return httpx.Response(404, json={"error": "Not found"})
            if method == "DELETE":
                del self.campaigns[campaign_id]
                self.streams = {k: v for k, v in self.streams.items() if v["campaign_id"] != campaign_id}
                return httpx.Response(204)
            if method == "PUT":
                self.campaigns[campaign_id].update(body)
            return httpx.Response(200, json=self.campaigns[campaign_id])
        if match := re.fullmatch(r"/campaigns/(\d+)/streams", path):
            streams = [s for s in self.streams.values() if s["campaign_id"] == int(match[1])]
            return httpx.Response(200, json=sorted(streams, key=lambda s: s["position"]))
        if method == "POST" and path == "/streams":
            if self.fail_stream_create:
                return httpx.Response(500, json={"error": "boom"})
            stream = {"id": self._id(), "filters": [], "offers": [], **body}
            self.streams[stream["id"]] = stream
            return httpx.Response(200, json=stream)
        if match := re.fullmatch(r"/streams/(\d+)", path):
            stream = self.streams.get(int(match[1]))
            if stream is None:
                return httpx.Response(404, json={"error": "Not found"})
            if method == "PUT":
                stream.update(body)
            return httpx.Response(200, json=stream)
        return httpx.Response(404, json={"error": f"Unsupported {method} {path}"})


@pytest.fixture
def fake() -> FakeKeitaro:
    return FakeKeitaro()


@pytest.fixture
def client(fake: FakeKeitaro):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app = create_app()
    app.state.keitaro = KeitaroClient(
        "https://keitaro.test/admin_api/v1", "test-key", transport=httpx.MockTransport(fake.handler)
    )
    with TestClient(app) as test_client:
        yield test_client
