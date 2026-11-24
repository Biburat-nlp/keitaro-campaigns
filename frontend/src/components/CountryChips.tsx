import { useId, useState } from 'react'
import { useI18n } from '../i18n'
import { countryName } from '../utils'

type Props = {
  codes: string[]
  allCodes: string[]
  onAdd: (codes: string[]) => boolean | Promise<boolean>
  onRemove: (code: string) => void
  canRemove?: boolean
  commitOnBlur?: boolean
  disabled?: boolean
  placeholder?: string
  id?: string
  ariaLabel?: string
  onPendingChange?: (text: string) => void
}

function parseCodes(text: string): string[] {
  return text
    .split(/[\s,;]+/)
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean)
}

export default function CountryChips({
  codes,
  allCodes,
  onAdd,
  onRemove,
  canRemove = true,
  commitOnBlur = false,
  disabled,
  placeholder,
  id,
  ariaLabel,
  onPendingChange,
}: Props) {
  const { t, lang } = useI18n()
  const listId = useId()
  const [text, setTextState] = useState('')

  function setText(value: string) {
    setTextState(value)
    onPendingChange?.(value.trim())
  }
  const [error, setError] = useState<string | null>(null)

  async function commit() {
    const parsed = parseCodes(text)
    if (parsed.length === 0) return
    const unknown = parsed.filter((code) => !allCodes.includes(code))
    if (unknown.length > 0) {
      setError(t('chips.unknown', { codes: unknown.join(', ') }))
      return
    }
    const fresh = [...new Set(parsed)].filter((code) => !codes.includes(code))
    if (fresh.length === 0) {
      setError(t('chips.duplicate'))
      return
    }
    setError(null)
    if (await onAdd(fresh)) setText('')
  }

  return (
    <div className="chips-field">
      <div className={`chips ${disabled ? 'disabled' : ''}`}>
        {codes.map((code) => (
          <span key={code} className="chip" title={countryName(code, lang)}>
            <b>{code}</b>
            <span>{countryName(code, lang)}</span>
            {canRemove && (
              <button
                type="button"
                aria-label={t('chips.remove', { code })}
                disabled={disabled}
                onClick={() => onRemove(code)}
              >
                ×
              </button>
            )}
          </span>
        ))}
        <input
          id={id}
          aria-label={ariaLabel}
          list={listId}
          value={text}
          disabled={disabled}
          placeholder={placeholder ?? (codes.length ? t('chips.more') : t('chips.placeholder'))}
          onChange={(e) => {
            setText(e.target.value)
            setError(null)
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ',') {
              e.preventDefault()
              void commit()
            }
          }}
          onBlur={() => {
            if (commitOnBlur) void commit()
          }}
        />
        <datalist id={listId}>
          {allCodes
            .filter((code) => !codes.includes(code))
            .map((code) => (
              <option key={code} value={code}>
                {countryName(code, lang)}
              </option>
            ))}
        </datalist>
      </div>
      {error && <p className="error small">{error}</p>}
    </div>
  )
}
