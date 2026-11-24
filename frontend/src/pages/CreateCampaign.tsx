import { useState } from 'react'
import { api, type Catalog, type Offer } from '../api'
import CountryChips from '../components/CountryChips'
import OfferPicker from '../components/OfferPicker'
import { useI18n } from '../i18n'
import { countryName, navigate } from '../utils'

type Props = { catalog: Catalog; offers: Offer[] }

function pickDefault(items: { id: number }[], id: number): number {
  return items.some((item) => item.id === id) ? id : (items[0]?.id ?? id)
}

export default function CreateCampaign({ catalog, offers }: Props) {
  const { t, lang } = useI18n()
  const [name, setName] = useState('')
  const [countries, setCountries] = useState<string[]>([])
  const [offerId, setOfferId] = useState<number | null>(null)
  const [domainId, setDomainId] = useState(() => pickDefault(catalog.domains, catalog.defaults.domain_id))
  const [groupId, setGroupId] = useState(() => pickDefault(catalog.groups, catalog.defaults.group_id))
  const [sourceId, setSourceId] = useState(() =>
    pickDefault(catalog.traffic_sources, catalog.defaults.traffic_source_id),
  )
  const [pendingCountry, setPendingCountry] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const missing = [
    name.trim() === '' && t('create.missingName'),
    countries.length === 0 && t('create.missingCountries'),
    offerId === null && t('create.missingOffer'),
  ].filter(Boolean)
  const canSubmit = missing.length === 0 && pendingCountry === '' && !busy
  const countriesText = countries.map((code) => `${countryName(code, lang)} (${code})`).join(', ')

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!canSubmit || offerId === null) return
    setBusy(true)
    setError(null)
    try {
      const result = await api.createCampaign({
        name: name.trim(),
        countries,
        offer_id: offerId,
        domain_id: domainId,
        group_id: groupId,
        traffic_source_id: sourceId,
      })
      navigate(`/campaigns/${result.campaign.id}`)
    } catch (e) {
      setError((e as Error).message)
      setBusy(false)
    }
  }

  return (
    <section>
      <div className="page-head">
        <h1>{t('create.title')}</h1>
      </div>
      <form className="card form" onSubmit={submit}>
        <label htmlFor="name">{t('create.name')}</label>
        <input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="campaign 2" maxLength={255} />

        <label htmlFor="countries">{t('create.countries')}</label>
        <CountryChips
          id="countries"
          codes={countries}
          allCodes={catalog.countries}
          commitOnBlur
          onPendingChange={setPendingCountry}
          onAdd={(codes) => {
            setCountries((current) => [...current, ...codes])
            return true
          }}
          onRemove={(code) => setCountries((current) => current.filter((item) => item !== code))}
        />

        <label htmlFor="offer">{t('create.offer')}</label>
        <OfferPicker id="offer" offers={offers} value={offerId} onChange={setOfferId} />

        <label htmlFor="domain">{t('common.domain')}</label>
        <select id="domain" value={domainId} onChange={(e) => setDomainId(Number(e.target.value))}>
          {catalog.domains.map((domain) => (
            <option key={domain.id} value={domain.id}>
              {domain.name}
            </option>
          ))}
        </select>

        <label htmlFor="group">{t('common.group')}</label>
        <select id="group" value={groupId} onChange={(e) => setGroupId(Number(e.target.value))}>
          {catalog.groups.map((group) => (
            <option key={group.id} value={group.id}>
              {group.name}
            </option>
          ))}
        </select>

        <label htmlFor="source">{t('common.source')}</label>
        <select id="source" value={sourceId} onChange={(e) => setSourceId(Number(e.target.value))}>
          {catalog.traffic_sources.map((source) => (
            <option key={source.id} value={source.id}>
              {source.name}
            </option>
          ))}
        </select>

        <div className="summary">
          <p className="small muted">{t('create.summaryTitle')}</p>
          <ol className="small">
            <li>{t('create.summaryGeo', { countries: countries.length ? countriesText : t('create.selectedCountries') })}</li>
            <li>{t('create.summaryOffers')}</li>
          </ol>
        </div>

        {error && <p className="error">{error}</p>}
        <div className="actions">
          <button type="submit" className="primary" disabled={!canSubmit}>
            {busy ? t('create.submitting') : t('create.submit')}
          </button>
          <a className="button" href="#/">
            {t('common.cancel')}
          </a>
          {!busy && missing.length > 0 && (
            <span className="small muted">{t('create.missing', { fields: missing.join(', ') })}</span>
          )}
          {!busy && missing.length === 0 && pendingCountry !== '' && (
            <span className="small error">{t('create.pendingCountry', { code: pendingCountry })}</span>
          )}
        </div>
      </form>
    </section>
  )
}
