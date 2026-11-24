import type { Domain, Offer } from './api'
import type { Lang } from './i18n'

const regionNames = new Map<Lang, Intl.DisplayNames>()

export function countryName(code: string, lang: Lang): string {
  let names = regionNames.get(lang)
  if (!names) {
    names = new Intl.DisplayNames([lang], { type: 'region' })
    regionNames.set(lang, names)
  }
  try {
    return names.of(code.toUpperCase()) ?? code
  } catch {
    return code
  }
}

export function offerLabel(offer: Offer): string {
  return offer.name.startsWith(String(offer.id)) ? offer.name : `[${offer.id}] ${offer.name}`
}

export function campaignUrl(domain: Domain | undefined, alias: string): string | null {
  if (!domain || !alias) return null
  const host = domain.name.replace(/^https?:\/\//, '').replace(/\/+$/, '')
  return `${domain.is_ssl === false ? 'http' : 'https'}://${host}/${alias}`
}

export function formatDate(value: string | undefined, locale: string): string {
  if (!value) return ''
  const iso = value.trim().replace(' ', 'T')
  const date = new Date(/(Z|[+-]\d{2}:?\d{2})$/.test(iso) ? iso : `${iso}Z`)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(locale)
}

export function safeHref(value: string | null | undefined): string | null {
  if (!value) return null
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null
  } catch {
    return null
  }
}

export function navigate(path: string) {
  window.location.hash = path
}
