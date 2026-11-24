import { useState } from 'react'
import { api, type Stream, type StreamFilter } from '../api'
import { useI18n } from '../i18n'
import CountryChips from './CountryChips'

type Props = {
  stream: Stream
  filter: StreamFilter
  allCodes: string[]
  onChanged: (stream: Stream) => void
}

function filterCodes(filter: StreamFilter): string[] {
  const payload = Array.isArray(filter.payload) ? filter.payload : filter.payload ? [filter.payload] : []
  return payload.map((code) => String(code).toUpperCase())
}

export default function GeoFilterEditor({ stream, filter, allCodes, onChanged }: Props) {
  const { t } = useI18n()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const codes = filterCodes(filter)

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

  return (
    <div className="geo-editor">
      <p className="small muted">
        {filter.mode === 'reject' ? t('geo.reject') : t('geo.accept')}
        {codes.length === 1 && t('geo.lastHint')}
      </p>
      <CountryChips
        codes={codes}
        allCodes={allCodes}
        disabled={busy}
        canRemove={codes.length > 1}
        placeholder={t('geo.placeholder')}
        ariaLabel={t('geo.addLabel', { stream: stream.name })}
        onAdd={(fresh) => run(() => api.addCountries(stream.id, fresh))}
        onRemove={(code) => void run(() => api.removeCountry(stream.id, code))}
      />
      {error && <p className="error">{error}</p>}
    </div>
  )
}
