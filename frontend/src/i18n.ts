import { createContext, useContext } from 'react'

export type Lang = 'ru' | 'en'

export const LANGS: Lang[] = ['ru', 'en']

const ru = {
  'lang.label': 'Язык интерфейса',
  'nav.campaigns': 'Кампании',
  'nav.new': 'Новая кампания',
  'common.loading': 'Загрузка…',
  'common.retry': 'Повторить',
  'common.cancel': 'Отмена',
  'common.save': 'Сохранить',
  'common.saving': 'Сохраняем…',
  'common.backendDown': 'Бэкенд недоступен',
  'common.domain': 'Домен',
  'common.group': 'Группа',
  'common.source': 'Источник',
  'app.catalogError': 'Не удалось загрузить справочники: {error}',

  'list.title': 'Кампании',
  'list.create': 'Создать кампанию',
  'list.empty': 'Кампаний пока нет.',
  'list.createFirst': 'Создать первую',
  'list.colName': 'Название',
  'list.colLink': 'Ссылка',
  'list.colState': 'Статус',
  'list.colCreated': 'Создана',
  'list.createdHere': 'создана здесь',

  'create.title': 'Новая кампания',
  'create.name': 'Название кампании',
  'create.countries': 'Страны (ISO-коды)',
  'create.offer': 'Оффер',
  'create.summaryTitle': 'Будет создано два потока:',
  'create.summaryGeo': 'Обычный: посетители из {countries} → редирект на google.com',
  'create.selectedCountries': 'выбранных стран',
  'create.summaryOffers': 'Запасной: все остальные → выбранный оффер (100%)',
  'create.submit': 'Создать кампанию',
  'create.submitting': 'Создаём…',
  'create.missing': 'Заполните: {fields}',
  'create.missingName': 'название',
  'create.missingCountries': 'страны',
  'create.missingOffer': 'оффер',
  'create.pendingCountry': 'Добавьте или удалите введённую страну «{code}»',

  'chips.unknown': 'Неизвестные коды: {codes}',
  'chips.duplicate': 'Эти страны уже добавлены',
  'chips.remove': 'Убрать {code}',
  'chips.more': 'Ещё страна',
  'chips.placeholder': 'Код страны, например AU',

  'picker.placeholder': 'Поиск по ID или названию',
  'picker.nothing': 'Ничего не найдено',
  'picker.more': 'Ещё {count} — уточните запрос',

  'title.rename': 'Переименовать',
  'title.inputLabel': 'Название кампании',

  'confirm.title': 'Подтвердите действие',
  'confirm.continue': 'Продолжить',

  'geo.accept': 'Страны: принимать',
  'geo.reject': 'Страны: отклонять',
  'geo.lastHint': ' · последнюю страну удалить нельзя',
  'geo.placeholder': 'Добавить страну: AU или несколько через запятую',
  'geo.addLabel': 'Добавить страну в фильтр потока «{stream}»',

  'editor.back': '← Кампании',
  'editor.sync': 'Загрузить из Keitaro',
  'editor.syncing': 'Загружаем…',
  'editor.open': 'Открыть в Keitaro',
  'editor.delete': 'Удалить',
  'editor.deleting': 'Удаляем…',
  'editor.deleteTitle': 'Удалить кампанию?',
  'editor.deleteText': 'Кампания «{name}» будет удалена из Keitaro вместе со всеми потоками. Восстановить её будет нельзя.',
  'editor.deleteConfirm': 'Удалить кампанию',
  'editor.toList': 'К списку',
  'editor.noStreams': 'У кампании нет потоков.',
  'editor.streamNumber': 'поток #{id}',
  'editor.redirectTo': 'Редирект на',
  'editor.filters': 'Фильтры',
  'editor.offers': 'Офферы',
  'editor.settings': 'Параметры',
  'editor.link': 'Ссылка',
  'editor.rotation': 'Ротация',
  'editor.rotationWeight': 'По весу',
  'editor.rotationPosition': 'По позиции',
  'editor.history': 'История изменений',
  'editor.noHistory': 'Изменений через этот инструмент ещё не было.',

  'streamType.forced': 'Перехватывающий',
  'streamType.regular': 'Обычный',
  'streamType.default': 'Запасной',
  'schema.redirect': 'Редирект',
  'schema.landings': 'Лендинги и офферы',
  'schema.action': 'Действие',
  'filter.accept': 'принимать',
  'filter.reject': 'отклонять',
  'filter.countries': 'Страны: {mode} {list}',

  'op.offer': 'оффер {id}',
  'op.create_campaign': 'Кампания создана: {countries}, {offer}',
  'op.add_countries': 'Добавлены страны: {countries}. Сейчас: {result}',
  'op.remove_country': 'Удалена страна {countries}. Сейчас: {result}',
  'op.add_offer': 'Черновик: добавлен {offer}. Доли: {shares}',
  'op.remove_offer': 'Черновик: удалён {offer}. Доли: {shares}',
  'op.restore_offer': 'Черновик: возвращён {offer}. Доли: {shares}',
  'op.set_share': 'Черновик: доля {offer} закреплена на {share}%. Доли: {shares}',
  'op.pin': 'Закреплена доля {offer}',
  'op.unpin': 'Откреплена доля {offer}. Доли: {shares}',
  'op.publish': 'Опубликовано в Keitaro. Доли: {shares}',
  'op.cancel': 'Черновик отменён. Доли: {shares}',
  'op.sync': 'Загружено из Keitaro (потоков: {count})',
  'op.syncVanished': 'Загружено из Keitaro. Удалены в Keitaro: {offers}',
  'op.rename_campaign': 'Переименована: «{old}» → «{name}»',
  'op.update_shares': 'Изменены доли: {shares}',
  'op.delete_campaign': 'Кампания удалена',

  'offers.noteNew': 'новый',
  'offers.noteWillRemove': 'будет удалён',
  'offers.noteWillReturn': 'вернётся',
  'offers.noteRemoved': 'удалён',
  'offers.dirty': 'Есть неопубликованные изменения',
  'offers.publish': 'Опубликовать в Keitaro',
  'offers.cancel': 'Отменить',
  'offers.needActive': 'Нужен хотя бы один активный оффер',
  'offers.sumWrong': 'Сумма долей {total}%, должна быть 100%',
  'offers.cancelTitle': 'Отменить изменения?',
  'offers.cancelText': 'Все неопубликованные изменения потока будут отменены, добавленные офферы удалятся из черновика.',
  'offers.cancelConfirm': 'Отменить изменения',
  'offers.shareInvalid': 'Доля должна быть целым числом от 0 до 100',
  'offers.empty': 'В потоке нет офферов.',
  'offers.colOffer': 'Оффер',
  'offers.colGeo': 'Гео',
  'offers.colShare': 'Доля',
  'offers.unknown': 'неизвестный оффер',
  'offers.shareLabel': 'Доля оффера {id}',
  'offers.pin': 'Закрепить долю оффера {id}',
  'offers.unpin': 'Открепить долю оффера {id}',
  'offers.pinnedHint': 'Доля закреплена и не меняется при пересчёте',
  'offers.pinHint': 'Закрепить долю',
  'offers.was': 'было {share}%',
  'offers.restore': 'Вернуть',
  'offers.remove': 'Удалить',
  'offers.removeLabel': 'Удалить оффер {id}',
  'offers.total': 'Итого',
  'offers.addPlaceholder': 'Добавить оффер: поиск по ID или названию',
  'offers.addLabel': 'Добавить оффер в поток «{stream}»',
  'offers.add': 'Добавить',
  'offers.help':
    'Изменения сохраняются в черновик и попадают в Keitaro только после публикации. Доли незакреплённых офферов пересчитываются поровну; закреплённые (булавка или ручной ввод доли) не меняются.',
}

export type MessageKey = keyof typeof ru

const en: Record<MessageKey, string> = {
  'lang.label': 'Interface language',
  'nav.campaigns': 'Campaigns',
  'nav.new': 'New campaign',
  'common.loading': 'Loading…',
  'common.retry': 'Retry',
  'common.cancel': 'Cancel',
  'common.save': 'Save',
  'common.saving': 'Saving…',
  'common.backendDown': 'Backend is unavailable',
  'common.domain': 'Domain',
  'common.group': 'Group',
  'common.source': 'Traffic source',
  'app.catalogError': 'Failed to load reference data: {error}',

  'list.title': 'Campaigns',
  'list.create': 'Create campaign',
  'list.empty': 'No campaigns yet.',
  'list.createFirst': 'Create the first one',
  'list.colName': 'Name',
  'list.colLink': 'Link',
  'list.colState': 'Status',
  'list.colCreated': 'Created',
  'list.createdHere': 'created here',

  'create.title': 'New campaign',
  'create.name': 'Campaign name',
  'create.countries': 'Countries (ISO codes)',
  'create.offer': 'Offer',
  'create.summaryTitle': 'Two streams will be created:',
  'create.summaryGeo': 'Regular: visitors from {countries} → redirect to google.com',
  'create.selectedCountries': 'the selected countries',
  'create.summaryOffers': 'Default: everyone else → the selected offer (100%)',
  'create.submit': 'Create campaign',
  'create.submitting': 'Creating…',
  'create.missing': 'Fill in: {fields}',
  'create.missingName': 'name',
  'create.missingCountries': 'countries',
  'create.missingOffer': 'offer',
  'create.pendingCountry': 'Add or clear the typed country “{code}”',

  'chips.unknown': 'Unknown codes: {codes}',
  'chips.duplicate': 'These countries are already added',
  'chips.remove': 'Remove {code}',
  'chips.more': 'Another country',
  'chips.placeholder': 'Country code, e.g. AU',

  'picker.placeholder': 'Search by ID or name',
  'picker.nothing': 'Nothing found',
  'picker.more': '{count} more — refine the search',

  'title.rename': 'Rename',
  'title.inputLabel': 'Campaign name',

  'confirm.title': 'Please confirm',
  'confirm.continue': 'Continue',

  'geo.accept': 'Countries: accept',
  'geo.reject': 'Countries: reject',
  'geo.lastHint': ' · the last country can’t be removed',
  'geo.placeholder': 'Add a country: AU or several, comma-separated',
  'geo.addLabel': 'Add a country to the filter of stream “{stream}”',

  'editor.back': '← Campaigns',
  'editor.sync': 'Fetch from Keitaro',
  'editor.syncing': 'Fetching…',
  'editor.open': 'View in Keitaro',
  'editor.delete': 'Delete',
  'editor.deleting': 'Deleting…',
  'editor.deleteTitle': 'Delete campaign?',
  'editor.deleteText': 'Campaign “{name}” will be deleted from Keitaro with all its streams. It can’t be restored.',
  'editor.deleteConfirm': 'Delete campaign',
  'editor.toList': 'Back to list',
  'editor.noStreams': 'The campaign has no streams.',
  'editor.streamNumber': 'stream #{id}',
  'editor.redirectTo': 'Redirect to',
  'editor.filters': 'Filters',
  'editor.offers': 'Offers',
  'editor.settings': 'Settings',
  'editor.link': 'Link',
  'editor.rotation': 'Rotation',
  'editor.rotationWeight': 'By weight',
  'editor.rotationPosition': 'By position',
  'editor.history': 'Change history',
  'editor.noHistory': 'No changes have been made through this tool yet.',

  'streamType.forced': 'Forced',
  'streamType.regular': 'Regular',
  'streamType.default': 'Default',
  'schema.redirect': 'Redirect',
  'schema.landings': 'Landings & offers',
  'schema.action': 'Action',
  'filter.accept': 'accept',
  'filter.reject': 'reject',
  'filter.countries': 'Countries: {mode} {list}',

  'op.offer': 'offer {id}',
  'op.create_campaign': 'Campaign created: {countries}, {offer}',
  'op.add_countries': 'Countries added: {countries}. Now: {result}',
  'op.remove_country': 'Country removed: {countries}. Now: {result}',
  'op.add_offer': 'Draft: added {offer}. Shares: {shares}',
  'op.remove_offer': 'Draft: removed {offer}. Shares: {shares}',
  'op.restore_offer': 'Draft: brought back {offer}. Shares: {shares}',
  'op.set_share': 'Draft: {offer} pinned at {share}%. Shares: {shares}',
  'op.pin': 'Pinned the share of {offer}',
  'op.unpin': 'Unpinned the share of {offer}. Shares: {shares}',
  'op.publish': 'Pushed to Keitaro. Shares: {shares}',
  'op.cancel': 'Draft discarded. Shares: {shares}',
  'op.sync': 'Fetched from Keitaro (streams: {count})',
  'op.syncVanished': 'Fetched from Keitaro. Deleted in Keitaro: {offers}',
  'op.rename_campaign': 'Renamed: “{old}” → “{name}”',
  'op.update_shares': 'Shares changed: {shares}',
  'op.delete_campaign': 'Campaign deleted',

  'offers.noteNew': 'new',
  'offers.noteWillRemove': 'to be removed',
  'offers.noteWillReturn': 'to be restored',
  'offers.noteRemoved': 'removed',
  'offers.dirty': 'Unpublished changes',
  'offers.publish': 'Push to Keitaro',
  'offers.cancel': 'Cancel',
  'offers.needActive': 'At least one active offer is required',
  'offers.sumWrong': 'Shares add up to {total}%, must be 100%',
  'offers.cancelTitle': 'Discard changes?',
  'offers.cancelText': 'All unpublished changes in this stream will be discarded; offers added in the draft will be removed.',
  'offers.cancelConfirm': 'Discard changes',
  'offers.shareInvalid': 'Share must be a whole number from 0 to 100',
  'offers.empty': 'The stream has no offers.',
  'offers.colOffer': 'Offer',
  'offers.colGeo': 'Geo',
  'offers.colShare': 'Share',
  'offers.unknown': 'unknown offer',
  'offers.shareLabel': 'Share of offer {id}',
  'offers.pin': 'Pin the share of offer {id}',
  'offers.unpin': 'Unpin the share of offer {id}',
  'offers.pinnedHint': 'The share is pinned and kept when rebalancing',
  'offers.pinHint': 'Pin the share',
  'offers.was': 'was {share}%',
  'offers.restore': 'Bring back',
  'offers.remove': 'Remove',
  'offers.removeLabel': 'Remove offer {id}',
  'offers.total': 'Total',
  'offers.addPlaceholder': 'Add an offer: search by ID or name',
  'offers.addLabel': 'Add an offer to stream “{stream}”',
  'offers.add': 'Add',
  'offers.help':
    'Changes are saved to a draft and reach Keitaro only after pushing. Unpinned shares are split equally; pinned ones (pin icon or a typed share) are kept.',
}

const DICTIONARIES: Record<Lang, Record<MessageKey, string>> = { ru, en }

const LOCALES: Record<Lang, string> = { ru: 'ru-RU', en: 'en-GB' }

const STORAGE_KEY = 'keitaro-campaigns.lang'

export type Params = Record<string, string | number>

let currentLang: Lang = 'ru'

export function translate(lang: Lang, key: MessageKey, params?: Params): string {
  const template = DICTIONARIES[lang][key] ?? DICTIONARIES.ru[key] ?? key
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in params ? String(params[name]) : match))
}

export function getLanguage(): Lang {
  return currentLang
}

export function setLanguage(lang: Lang) {
  currentLang = lang
  try {
    window.localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    return
  }
}

export function initialLanguage(): Lang {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    if (stored === 'ru' || stored === 'en') return stored
  } catch {
    return 'ru'
  }
  return navigator.language?.toLowerCase().startsWith('ru') ? 'ru' : 'en'
}

export function localeOf(lang: Lang): string {
  return LOCALES[lang]
}

export type I18n = {
  lang: Lang
  locale: string
  setLang: (lang: Lang) => void
  t: (key: MessageKey, params?: Params) => string
}

export const I18nContext = createContext<I18n>({
  lang: 'ru',
  locale: LOCALES.ru,
  setLang: () => undefined,
  t: (key, params) => translate('ru', key, params),
})

export function useI18n(): I18n {
  return useContext(I18nContext)
}
