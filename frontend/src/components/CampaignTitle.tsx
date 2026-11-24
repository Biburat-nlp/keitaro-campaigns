import { useState } from 'react'
import { api, type Campaign } from '../api'
import { useI18n } from '../i18n'

type Props = {
  campaign: Campaign
  onRenamed: (campaign: Campaign) => void
}

export default function CampaignTitle({ campaign, onRenamed }: Props) {
  const { t } = useI18n()
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(campaign.name)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const trimmed = value.trim()

  function start() {
    setValue(campaign.name)
    setError(null)
    setEditing(true)
  }

  function cancel() {
    setEditing(false)
    setError(null)
  }

  async function save(event: React.FormEvent) {
    event.preventDefault()
    if (!trimmed) return
    if (trimmed === campaign.name) {
      cancel()
      return
    }
    setBusy(true)
    setError(null)
    try {
      onRenamed(await api.renameCampaign(campaign.id, trimmed))
      setEditing(false)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  if (!editing) {
    return (
      <h1>
        <span>{campaign.name}</span>
        <span className={`state ${campaign.state}`}>{campaign.state}</span>
        <button className="ghost small" onClick={start}>
          {t('title.rename')}
        </button>
      </h1>
    )
  }

  return (
    <form className="title-form" onSubmit={save}>
      <input
        autoFocus
        aria-label={t('title.inputLabel')}
        value={value}
        maxLength={255}
        disabled={busy}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Escape') cancel()
        }}
      />
      <button type="submit" className="primary" disabled={busy || !trimmed}>
        {busy ? t('common.saving') : t('common.save')}
      </button>
      <button type="button" className="ghost" disabled={busy} onClick={cancel}>
        {t('common.cancel')}
      </button>
      {error && <p className="error small">{error}</p>}
    </form>
  )
}
