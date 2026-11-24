from typing import Any

DEFAULT_LANGUAGE = "ru"
LANGUAGES = ("ru", "en")

MESSAGES: dict[str, dict[str, str]] = {
    "ru": {
        "offer_not_found": "Оффер {offer_id} не найден",
        "campaign_without_id": "Keitaro не вернул ID созданной кампании",
        "no_country_filter": "У потока {stream_id} нет фильтра по стране",
        "many_country_filters": "У потока {stream_id} несколько фильтров по стране, отредактируйте их в Keitaro",
        "countries_already_added": "Эти страны уже есть в фильтре",
        "country_not_in_filter": "Страны {code} нет в фильтре",
        "last_country": "Нельзя удалить последнюю страну: фильтр останется пустым",
        "pinned_over_100": "Сумма закреплённых долей {total}% больше 100%",
        "unexpected_streams": "Keitaro вернул неожиданный ответ на список потоков",
        "stream_not_loaded": "Поток {stream_id} не загружен, нажмите «Загрузить из Keitaro»",
        "stream_without_offers": "Поток {stream_id} не работает с офферами (schema={schema})",
        "offer_not_in_stream": "Оффера {offer_id} нет в потоке",
        "offer_already_in_stream": "Оффер {offer_id} уже есть в потоке",
        "offer_already_removed": "Оффер {offer_id} уже удалён",
        "offer_already_active": "Оффер {offer_id} и так активен",
        "share_only_active": "Долю можно задать только активному офферу",
        "pin_only_active": "Закрепить можно только активный оффер",
        "nothing_to_publish": "Нет неопубликованных изменений",
        "need_active_offer": "В потоке должен остаться хотя бы один активный оффер",
        "shares_sum": "Сумма долей должна быть 100%, сейчас {total}%",
        "stream_changed": (
            "Поток изменили в Keitaro после последней загрузки. "
            "Нажмите «Загрузить из Keitaro» и опубликуйте снова — черновик сохранится"
        ),
        "keitaro_unavailable": "Keitaro недоступен: {error}",
        "keitaro_not_json": "Keitaro вернул ответ не в формате JSON",
        "keitaro_rejected_key": "Keitaro отклонил API-ключ: {message}",
        "keitaro_failed": "Ошибка Keitaro: {message}",
        "keitaro_says": "Keitaro: {message}",
        "empty_name": "Название не может быть пустым",
        "unknown_country": "Неизвестный код страны: {code}",
        "need_country": "Нужна хотя бы одна страна",
        "field_name": "название",
        "field_countries": "страны",
        "field_offer_id": "оффер",
        "field_share": "доля",
        "field_pinned": "закрепление",
        "field_domain_id": "домен",
        "field_group_id": "группа",
        "field_traffic_source_id": "источник",
        "field_body": "тело запроса",
        "validation_missing": "{field}: обязательное поле",
        "validation_too_short": "{field}: слишком короткое значение",
        "validation_too_long": "{field}: слишком длинное значение",
        "validation_number_range": "{field}: значение вне допустимого диапазона",
        "validation_type": "{field}: неверный формат",
        "validation_other": "{field}: {message}",
    },
    "en": {
        "offer_not_found": "Offer {offer_id} not found",
        "campaign_without_id": "Keitaro did not return the ID of the created campaign",
        "no_country_filter": "Stream {stream_id} has no country filter",
        "many_country_filters": "Stream {stream_id} has several country filters, edit them in Keitaro",
        "countries_already_added": "These countries are already in the filter",
        "country_not_in_filter": "Country {code} is not in the filter",
        "last_country": "The last country can't be removed: the filter would be empty",
        "pinned_over_100": "Pinned shares add up to {total}%, more than 100%",
        "unexpected_streams": "Keitaro returned an unexpected stream list",
        "stream_not_loaded": "Stream {stream_id} is not loaded, click “Fetch from Keitaro”",
        "stream_without_offers": "Stream {stream_id} doesn't work with offers (schema={schema})",
        "offer_not_in_stream": "Offer {offer_id} is not in the stream",
        "offer_already_in_stream": "Offer {offer_id} is already in the stream",
        "offer_already_removed": "Offer {offer_id} is already removed",
        "offer_already_active": "Offer {offer_id} is already active",
        "share_only_active": "Only an active offer can have a share",
        "pin_only_active": "Only an active offer can be pinned",
        "nothing_to_publish": "There are no unpublished changes",
        "need_active_offer": "The stream must keep at least one active offer",
        "shares_sum": "Shares must add up to 100%, now {total}%",
        "stream_changed": (
            "The stream was changed in Keitaro after the last fetch. "
            "Click “Fetch from Keitaro” and publish again — your draft will be kept"
        ),
        "keitaro_unavailable": "Keitaro is unavailable: {error}",
        "keitaro_not_json": "Keitaro returned a non-JSON response",
        "keitaro_rejected_key": "Keitaro rejected the API key: {message}",
        "keitaro_failed": "Keitaro error: {message}",
        "keitaro_says": "Keitaro: {message}",
        "empty_name": "Name can't be empty",
        "unknown_country": "Unknown country code: {code}",
        "need_country": "At least one country is required",
        "field_name": "name",
        "field_countries": "countries",
        "field_offer_id": "offer",
        "field_share": "share",
        "field_pinned": "pinned",
        "field_domain_id": "domain",
        "field_group_id": "group",
        "field_traffic_source_id": "traffic source",
        "field_body": "request body",
        "validation_missing": "{field}: required",
        "validation_too_short": "{field}: value is too short",
        "validation_too_long": "{field}: value is too long",
        "validation_number_range": "{field}: value is out of range",
        "validation_type": "{field}: invalid format",
        "validation_other": "{field}: {message}",
    },
}


def pick_language(accept_language: str | None) -> str:
    for part in (accept_language or "").split(","):
        tag = part.split(";")[0].strip().lower()
        for language in LANGUAGES:
            if tag == language or tag.startswith(f"{language}-"):
                return language
    return DEFAULT_LANGUAGE


def translate(key: str, language: str, **params: Any) -> str:
    template = MESSAGES.get(language, MESSAGES[DEFAULT_LANGUAGE]).get(key) or MESSAGES[DEFAULT_LANGUAGE].get(key, key)
    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template
