from typing import Any

import httpx

from app.i18n import DEFAULT_LANGUAGE, translate


class KeitaroError(Exception):
    def __init__(self, status_code: int, message: str = "", key: str | None = None, **params: Any):
        self.status_code = status_code
        self.key = key
        self.params = params
        self.message = translate(key, DEFAULT_LANGUAGE, **params) if key else message
        super().__init__(self.message)


class KeitaroClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Api-Key": api_key, "Accept": "application/json"},
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as error:
            raise KeitaroError(502, key="keitaro_unavailable", error=str(error)) from error
        if response.is_error:
            raise KeitaroError(response.status_code, self._error_message(response))
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as error:
            raise KeitaroError(502, key="keitaro_not_json") from error

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            return response.text.strip() or response.reason_phrase
        if isinstance(data, dict):
            for key in ("error", "message", "detail", "errors"):
                value = data.get(key)
                if value:
                    return value if isinstance(value, str) else str(value)
        return str(data)

    def list_campaigns(self, offset: int = 0, limit: int = 100) -> list[dict]:
        return self._request("GET", "/campaigns", params={"offset": offset, "limit": limit})

    def get_campaign(self, campaign_id: int) -> dict:
        return self._request("GET", f"/campaigns/{campaign_id}")

    def create_campaign(self, payload: dict) -> dict:
        return self._request("POST", "/campaigns", json=payload)

    def update_campaign(self, campaign_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/campaigns/{campaign_id}", json=payload)

    def delete_campaign(self, campaign_id: int) -> None:
        self._request("DELETE", f"/campaigns/{campaign_id}")

    def list_streams(self, campaign_id: int) -> list[dict]:
        return self._request("GET", f"/campaigns/{campaign_id}/streams")

    def get_stream(self, stream_id: int) -> dict:
        return self._request("GET", f"/streams/{stream_id}")

    def create_stream(self, payload: dict) -> dict:
        return self._request("POST", "/streams", json=payload)

    def update_stream(self, stream_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/streams/{stream_id}", json=payload)

    def delete_stream(self, stream_id: int) -> None:
        self._request("DELETE", f"/streams/{stream_id}")

    def list_offers(self) -> list[dict]:
        return self._request("GET", "/offers")

    def get_offer(self, offer_id: int) -> dict:
        return self._request("GET", f"/offers/{offer_id}")

    def list_domains(self) -> list[dict]:
        return self._request("GET", "/domains")

    def list_campaign_groups(self) -> list[dict]:
        return self._request("GET", "/groups", params={"type": "campaigns"})

    def list_traffic_sources(self) -> list[dict]:
        return self._request("GET", "/traffic_sources")
