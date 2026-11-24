import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, type Campaign, type CampaignDetails, type Catalog, type Offer, type Operation, type OperationsPage, type Stream, type StreamFilter } from '../api'
import CampaignTitle from '../components/CampaignTitle'
import GeoFilterEditor from '../components/GeoFilterEditor'
import OffersEditor from '../components/OffersEditor'
import { useConfirm } from '../confirm'
import { useI18n, type I18n, type MessageKey } from '../i18n'
import { campaignUrl, countryName, formatDate, navigate, safeHref } from '../utils'

type Props = { campaignId: number; catalog: Catalog; offers: Offer[] }

const HISTORY_PAGE_SIZE = 10

const EMPTY_HISTORY: OperationsPage = { items: [], total: 0, offset: 0, limit: HISTORY_PAGE_SIZE }

function label(i18n: I18n, prefix: string, value: string): string {
  const key = `${prefix}.${value}` as MessageKey
  const text = i18n.t(key)
  return text === key ? value : text
}

function describeFilter(filter: StreamFilter, i18n: I18n): string {
  const mode = label(i18n, 'filter', filter.mode)
  if (filter.name === 'country' && Array.isArray(filter.payload)) {
    const list = filter.payload.map((code) => `${countryName(String(code), i18n.lang)} (${code})`).join(', ')
    return i18n.t('filter.countries', { mode, list })
  }
  return `${filter.name}: ${mode} ${JSON.stringify(filter.payload)}`
}

function codesText(value: unknown): string {
  return (Array.isArray(value) ? value : [value]).filter(Boolean).join(', ')
}

function StreamFilters({
  stream,
  allCodes,
  onChanged,
}: {
  stream: Stream
  allCodes: string[]
  onChanged: (stream: Stream) => void
}) {
  const i18n = useI18n()
  const filters = stream.filters ?? []
  const geo = filters.filter((filter) => filter.name === 'country')
  const editable = geo.length === 1 ? geo[0] : null
  const rest = editable ? filters.filter((filter) => filter !== editable) : filters
  return (
    <div>
      <h3>{i18n.t('editor.filters')}</h3>
      {editable && <GeoFilterEditor stream={stream} filter={editable} allCodes={allCodes} onChanged={onChanged} />}
      {rest.length > 0 && (
        <ul className="filters">
          {rest.map((filter, index) => (
            <li key={index}>{describeFilter(filter, i18n)}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

function describeOperation(operation: Operation, offersById: Map<number, Offer>, i18n: I18n): string {
  const { t } = i18n
  const details = operation.details
  const offerName = (id: unknown) => offersById.get(Number(id))?.name ?? t('op.offer', { id: String(id) })
  const shares = (value: unknown) =>
    Object.entries((value as Record<string, number>) ?? {})
      .map(([id, share]) => `${id}: ${share}%`)
      .join(', ')
  const common = {
    offer: offerName(details.offer_id),
    shares: shares(details.shares),
    countries: codesText(details.countries ?? details.country),
    result: codesText(details.result),
  }
  switch (operation.action) {
    case 'sync': {
      const vanished = Object.values((details.vanished as Record<string, number[]>) ?? {}).flat()
      return vanished.length
        ? t('op.syncVanished', { offers: vanished.map(offerName).join(', ') })
        : t('op.sync', { count: String(details.streams ?? 0) })
    }
    case 'set_share':
      return t('op.set_share', { ...common, share: String(details.share) })
    case 'rename_campaign':
      return t('op.rename_campaign', { old: String(details.old_name), name: String(details.name) })
    default: {
      const key = `op.${operation.action}` as MessageKey
      const text = t(key, common)
      return text === key ? operation.action : text
    }
  }
}

export default function CampaignEditor({ campaignId, catalog, offers }: Props) {
  const i18n = useI18n()
  const { t, locale } = i18n
  const [details, setDetails] = useState<CampaignDetails | null>(null)
  const [history, setHistory] = useState<OperationsPage>(EMPTY_HISTORY)
  const [historyBusy, setHistoryBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const confirm = useConfirm()

  const offersById = useMemo(() => new Map(offers.map((offer) => [offer.id, offer])), [offers])

  const loadHistory = useCallback(
    (offset = 0) => {
      api
        .operations(campaignId, offset, HISTORY_PAGE_SIZE)
        .then(setHistory)
        .catch(() => setHistory(EMPTY_HISTORY))
        .finally(() => setHistoryBusy(false))
    },
    [campaignId],
  )

  const load = useCallback(() => {
    api
      .campaign(campaignId)
      .then(setDetails)
      .catch((e: Error) => setError(e.message))
    loadHistory()
  }, [campaignId, loadHistory])

  useEffect(load, [load])

  function showHistory(offset: number) {
    setHistoryBusy(true)
    loadHistory(offset)
  }

  function onStreamChanged(stream: Stream) {
    setDetails(
      (current) =>
        current && {
          ...current,
          streams: current.streams.map((item) => (item.id === stream.id ? stream : item)),
        },
    )
    loadHistory()
  }

  function onRenamed(campaign: Campaign) {
    setDetails((current) => current && { ...current, campaign: { ...current.campaign, ...campaign } })
    loadHistory()
  }

  async function sync() {
    setSyncing(true)
    setError(null)
    try {
      setDetails(await api.syncCampaign(campaignId))
      loadHistory()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSyncing(false)
    }
  }

  async function remove() {
    if (!details) return
    const ok = await confirm(t('editor.deleteText', { name: details.campaign.name }), {
      title: t('editor.deleteTitle'),
      confirmLabel: t('editor.deleteConfirm'),
      danger: true,
    })
    if (!ok) return
    setDeleting(true)
    try {
      await api.deleteCampaign(campaignId)
      navigate('/')
    } catch (e) {
      setError((e as Error).message)
      setDeleting(false)
    }
  }

  if (error && !details) {
    return (
      <div className="card">
        <p className="error">{error}</p>
        <div className="actions">
          <button
            onClick={() => {
              setError(null)
              load()
            }}
          >
            {t('common.retry')}
          </button>
          <a className="button" href="#/">
            {t('editor.toList')}
          </a>
        </div>
      </div>
    )
  }
  if (!details) return <p className="muted">{t('common.loading')}</p>

  const { campaign, streams } = details
  const domain = catalog.domains.find((item) => item.id === campaign.domain_id)
  const group = catalog.groups.find((item) => item.id === campaign.group_id)
  const source = catalog.traffic_sources.find((item) => item.id === campaign.traffic_source_id)
  const url = campaignUrl(domain, campaign.alias)

  return (
    <section>
      <div className="page-head">
        <div className="title-block">
          <a href="#/" className="small">
            {t('editor.back')}
          </a>
          <CampaignTitle campaign={campaign} onRenamed={onRenamed} />
        </div>
        <div className="actions">
          <button disabled={syncing} onClick={() => void sync()}>
            {syncing ? t('editor.syncing') : t('editor.sync')}
          </button>
          <a className="button" href={details.admin_url} target="_blank" rel="noreferrer">
            {t('editor.open')}
          </a>
          <button className="danger" disabled={deleting} onClick={remove}>
            {deleting ? t('editor.deleting') : t('editor.delete')}
          </button>
        </div>
      </div>
      {error && <p className="error">{error}</p>}

      <div className="layout">
        <div className="main-col">
          {streams.length === 0 && <div className="card muted">{t('editor.noStreams')}</div>}
          {streams.map((stream) => (
            <article key={stream.id} className={`card stream ${stream.dirty ? 'dirty' : ''}`}>
              <header>
                <span className={`dot ${stream.state}`} />
                <h2>{stream.name}</h2>
                <span className="badge">{label(i18n, 'streamType', stream.type)}</span>
                <span className="badge">{label(i18n, 'schema', stream.schema)}</span>
                <span className="muted small push">{t('editor.streamNumber', { id: stream.id })}</span>
              </header>
              {stream.schema === 'redirect' && stream.action_payload && (
                <p>
                  {t('editor.redirectTo')}{' '}
                  {safeHref(stream.action_payload) ? (
                    <a href={safeHref(stream.action_payload)!} target="_blank" rel="noreferrer">
                      {stream.action_payload}
                    </a>
                  ) : (
                    <span className="mono">{stream.action_payload}</span>
                  )}
                </p>
              )}
              {(stream.filters ?? []).length > 0 && (
                <StreamFilters stream={stream} allCodes={catalog.countries} onChanged={onStreamChanged} />
              )}
              {stream.schema === 'landings' && (
                <div>
                  <h3>{t('editor.offers')}</h3>
                  <OffersEditor stream={stream} offersById={offersById} allOffers={offers} onChanged={onStreamChanged} />
                </div>
              )}
            </article>
          ))}
        </div>

        <aside className="side-col">
          <div className="card">
            <h3>{t('editor.settings')}</h3>
            <dl>
              <dt>ID</dt>
              <dd>{campaign.id}</dd>
              <dt>{t('editor.link')}</dt>
              <dd className="mono small">{url ?? campaign.alias}</dd>
              <dt>{t('common.domain')}</dt>
              <dd>{domain?.name ?? campaign.domain_id ?? '—'}</dd>
              <dt>{t('common.group')}</dt>
              <dd>{group?.name ?? campaign.group_id ?? '—'}</dd>
              <dt>{t('common.source')}</dt>
              <dd>{source?.name ?? campaign.traffic_source_id ?? '—'}</dd>
              <dt>{t('editor.rotation')}</dt>
              <dd>{campaign.type === 'weight' ? t('editor.rotationWeight') : t('editor.rotationPosition')}</dd>
            </dl>
          </div>
          <div className="card">
            <h3>{t('editor.history')}</h3>
            {history.total === 0 ? (
              <p className="small muted">{t('editor.noHistory')}</p>
            ) : (
              <>
                <ul className="history">
                  {history.items.map((operation) => (
                    <li key={operation.id}>
                      <span className="small muted">{formatDate(operation.created_at, locale)}</span>
                      <span className="small">{describeOperation(operation, offersById, i18n)}</span>
                    </li>
                  ))}
                </ul>
                {history.total > history.limit && (
                  <nav className="pager" aria-label={t('history.pager')}>
                    <button
                      disabled={historyBusy || history.offset === 0}
                      onClick={() => showHistory(Math.max(0, history.offset - history.limit))}
                    >
                      {t('history.newer')}
                    </button>
                    <span className="small muted">
                      {t('history.range', {
                        from: history.offset + 1,
                        to: Math.min(history.offset + history.items.length, history.total),
                        total: history.total,
                      })}
                    </span>
                    <button
                      disabled={historyBusy || history.offset + history.limit >= history.total}
                      onClick={() => showHistory(history.offset + history.limit)}
                    >
                      {t('history.older')}
                    </button>
                  </nav>
                )}
              </>
            )}
          </div>
        </aside>
      </div>
    </section>
  )
}
