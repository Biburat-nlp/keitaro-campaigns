import { useState } from 'react'
import { api, type Offer, type Stream, type StreamOffer } from '../api'
import { useConfirm } from '../confirm'
import { useI18n, type MessageKey } from '../i18n'
import OfferPicker from './OfferPicker'

type Props = {
  stream: Stream
  offersById: Map<number, Offer>
  allOffers: Offer[]
  onChanged: (stream: Stream) => void
}

function rowNote(row: StreamOffer): MessageKey | null {
  if (row.is_new) return 'offers.noteNew'
  if (row.status === 'removed' && row.committed_status === 'active') return 'offers.noteWillRemove'
  if (row.status === 'active' && row.committed_status === 'removed') return 'offers.noteWillReturn'
  if (row.status === 'removed') return 'offers.noteRemoved'
  return null
}

function PinIcon({ filled }: { filled: boolean }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M16 3l5 5-3 1-4 4 1 5-2 2-4-4-5 5-1-1 5-5-4-4 2-2 5 1 4-4z"
        fill={filled ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default function OffersEditor({ stream, offersById, allOffers, onChanged }: Props) {
  const [newOfferId, setNewOfferId] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const confirm = useConfirm()
  const { t } = useI18n()

  const offers = stream.offers
  const presentIds = offers.map((row) => row.offer_id)
  const canPublish = stream.dirty && stream.active_count > 0 && stream.total === 100

  async function run(action: () => Promise<Stream>): Promise<boolean> {
    setBusy(true)
    setError(null)
    try {
      onChanged(await action())
      return true
    } catch (e) {
      setError((e as Error).message)
      return false
    } finally {
      setBusy(false)
    }
  }

  async function add() {
    if (newOfferId === null) return
    if (await run(() => api.addOffer(stream.id, newOfferId))) setNewOfferId(null)
  }

  async function cancelDraft() {
    const ok = await confirm(t('offers.cancelText'), {
      title: t('offers.cancelTitle'),
      confirmLabel: t('offers.cancelConfirm'),
      danger: true,
    })
    if (ok) await run(() => api.cancelDraft(stream.id))
  }

  function commitShare(row: StreamOffer, input: HTMLInputElement) {
    const value = Number(input.value)
    if (input.value.trim() === '' || !Number.isInteger(value) || value < 0 || value > 100) {
      input.value = String(row.share)
      setError(t('offers.shareInvalid'))
      return
    }
    if (value === row.share && row.pinned) return
    void run(() => api.setShare(stream.id, row.offer_id, value)).then((ok) => {
      if (!ok) input.value = String(row.share)
    })
  }

  return (
    <div className="offers-editor">
      {stream.dirty && (
        <div className="draft-bar">
          <span>{t('offers.dirty')}</span>
          <button className="primary" disabled={busy || !canPublish} onClick={() => void run(() => api.publishStream(stream.id))}>
            {t('offers.publish')}
          </button>
          <button disabled={busy} onClick={() => void cancelDraft()}>
            {t('offers.cancel')}
          </button>
          {stream.active_count === 0 && <span className="error small">{t('offers.needActive')}</span>}
          {stream.active_count > 0 && stream.total !== 100 && (
            <span className="error small">{t('offers.sumWrong', { total: stream.total })}</span>
          )}
        </div>
      )}

      {offers.length === 0 ? (
        <p className="muted">{t('offers.empty')}</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('offers.colOffer')}</th>
                <th>{t('offers.colGeo')}</th>
                <th className="share-col">{t('offers.colShare')}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {offers.map((row) => {
                const offer = offersById.get(row.offer_id)
                const note = rowNote(row)
                const removed = row.status === 'removed'
                return (
                  <tr key={row.offer_id} className={`${removed ? 'removed' : ''} ${row.dirty ? 'changed' : ''}`}>
                    <td className="num">{row.offer_id}</td>
                    <td>
                      {offer ? offer.name : <span className="muted">{t('offers.unknown')}</span>}
                      {note && <span className={`badge ${note === 'offers.noteRemoved' ? '' : 'badge-warn'}`}>{t(note)}</span>}
                      {row.state !== 'active' && <span className="badge">{row.state}</span>}
                    </td>
                    <td className="small muted">{offer?.country.join(', ')}</td>
                    <td className="share-col">
                      <div className="share">
                        <input
                          key={`${row.offer_id}-${row.share}`}
                          type="number"
                          min={0}
                          max={100}
                          defaultValue={row.share}
                          disabled={busy || removed}
                          aria-label={t('offers.shareLabel', { id: row.offer_id })}
                          onBlur={(e) => {
                            if (busy) return
                            if (Number(e.currentTarget.value) !== row.share) commitShare(row, e.currentTarget)
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !busy) commitShare(row, e.currentTarget)
                            if (e.key === 'Escape') e.currentTarget.value = String(row.share)
                          }}
                        />
                        <span>%</span>
                        <button
                          className={`pin ${row.pinned ? 'on' : ''}`}
                          disabled={busy || removed}
                          aria-pressed={row.pinned}
                          aria-label={t(row.pinned ? 'offers.unpin' : 'offers.pin', { id: row.offer_id })}
                          title={row.pinned ? t('offers.pinnedHint') : t('offers.pinHint')}
                          onClick={() => void run(() => api.setPinned(stream.id, row.offer_id, !row.pinned))}
                        >
                          <PinIcon filled={row.pinned} />
                        </button>
                        {!removed && row.share !== row.committed_share && !row.is_new && (
                          <span className="small muted">{t('offers.was', { share: row.committed_share })}</span>
                        )}
                      </div>
                    </td>
                    <td className="right">
                      {removed ? (
                        <button disabled={busy} onClick={() => void run(() => api.restoreOffer(stream.id, row.offer_id))}>
                          {t('offers.restore')}
                        </button>
                      ) : (
                        <button
                          className="danger ghost"
                          disabled={busy}
                          aria-label={t('offers.removeLabel', { id: row.offer_id })}
                          onClick={() => void run(() => api.removeOffer(stream.id, row.offer_id))}
                        >
                          {t('offers.remove')}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={3} className="right muted">
                  {t('offers.total')}
                </td>
                <td className={`share-col total ${stream.total === 100 ? 'ok' : 'error'}`}>{stream.total}%</td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      <form
        className="add-offer"
        onSubmit={(event) => {
          event.preventDefault()
          void add()
        }}
      >
        <OfferPicker
          offers={allOffers}
          value={newOfferId}
          onChange={setNewOfferId}
          excludeIds={presentIds}
          placeholder={t('offers.addPlaceholder')}
          ariaLabel={t('offers.addLabel', { stream: stream.name })}
          disabled={busy}
        />
        <button type="submit" className="primary" disabled={busy || newOfferId === null}>
          {t('offers.add')}
        </button>
      </form>
      <p className="small muted">{t('offers.help')}</p>
      {error && <p className="error">{error}</p>}
    </div>
  )
}
