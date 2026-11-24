from typing import Any

from app.i18n import DEFAULT_LANGUAGE, translate


class ServiceError(Exception):
    def __init__(self, status_code: int, key: str, **params: Any):
        self.status_code = status_code
        self.key = key
        self.params = params
        super().__init__(self.message)

    @property
    def message(self) -> str:
        return translate(self.key, DEFAULT_LANGUAGE, **self.params)
