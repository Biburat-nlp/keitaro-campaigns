from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import init_db
from app.keitaro import KeitaroClient, KeitaroError
from app.routes import router
from app.errors import ServiceError
from app.i18n import MESSAGES, pick_language, translate


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    if getattr(app.state, "keitaro", None) is None:
        app.state.keitaro = KeitaroClient(settings.keitaro_api_url, settings.keitaro_api_key, settings.keitaro_timeout)
    yield
    app.state.keitaro.close()


VALIDATION_KEYS = {
    "missing": "validation_missing",
    "string_too_short": "validation_too_short",
    "too_short": "validation_too_short",
    "string_too_long": "validation_too_long",
    "too_long": "validation_too_long",
    "greater_than": "validation_number_range",
    "greater_than_equal": "validation_number_range",
    "less_than": "validation_number_range",
    "less_than_equal": "validation_number_range",
}


def request_language(request: Request) -> str:
    return pick_language(request.headers.get("accept-language"))


def validation_message(item: dict, language: str) -> str:
    kind = item.get("type", "")
    context = item.get("ctx") or {}
    if kind in MESSAGES[language]:
        return translate(kind, language, **context)
    names = [part for part in item.get("loc", ()) if isinstance(part, str) and part != "body"]
    name = names[-1] if names else "body"
    field = translate(f"field_{name}", language) if f"field_{name}" in MESSAGES[language] else name
    if kind in VALIDATION_KEYS:
        return translate(VALIDATION_KEYS[kind], language, field=field)
    if kind.endswith(("_parsing", "_type")) or kind == "json_invalid":
        return translate("validation_type", language, field=field)
    return translate("validation_other", language, field=field, message=item.get("msg", ""))


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Keitaro campaign tool", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, error: ServiceError) -> JSONResponse:
        message = translate(error.key, request_language(request), **error.params)
        return JSONResponse(status_code=error.status_code, content={"detail": message})

    @app.exception_handler(KeitaroError)
    async def keitaro_error_handler(request: Request, error: KeitaroError) -> JSONResponse:
        language = request_language(request)
        if error.key:
            status, message = error.status_code, translate(error.key, language, **error.params)
        elif error.status_code in (401, 403):
            status, message = 502, translate("keitaro_rejected_key", language, message=error.message)
        elif error.status_code >= 500:
            status, message = 502, translate("keitaro_failed", language, message=error.message)
        else:
            status, message = error.status_code, translate("keitaro_says", language, message=error.message)
        return JSONResponse(status_code=status, content={"detail": message})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
        language = request_language(request)
        messages = [validation_message(item, language) for item in error.errors()]
        return JSONResponse(status_code=422, content={"detail": "; ".join(dict.fromkeys(messages))})

    app.include_router(router)
    return app


app = create_app()
