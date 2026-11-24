import { useId, useMemo, useRef, useState } from 'react'
import type { Offer } from '../api'
import { useI18n } from '../i18n'
import { offerLabel } from '../utils'

type Props = {
  offers: Offer[]
  value: number | null
  onChange: (offerId: number | null) => void
  excludeIds?: number[]
  placeholder?: string
  disabled?: boolean
  id?: string
  ariaLabel?: string
}

const LIMIT = 50

export default function OfferPicker({
  offers,
  value,
  onChange,
  excludeIds = [],
  placeholder,
  disabled,
  id,
  ariaLabel,
}: Props) {
  const { t } = useI18n()
  const listId = useId()
  const selected = offers.find((offer) => offer.id === value) ?? null
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [highlight, setHighlight] = useState(0)
  const listRef = useRef<HTMLUListElement>(null)

  const matches = useMemo(() => {
    const excluded = new Set(excludeIds)
    const needle = query.trim().toLowerCase()
    return offers.filter(
      (offer) =>
        !excluded.has(offer.id) &&
        (!needle || String(offer.id).includes(needle) || offer.name.toLowerCase().includes(needle)),
    )
  }, [offers, excludeIds, query])

  const visible = matches.slice(0, LIMIT)

  function choose(offer: Offer) {
    onChange(offer.id)
    setQuery('')
    setOpen(false)
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      setOpen(true)
      if (visible.length === 0) return
      const base = open ? highlight : -1
      const next = Math.min(Math.max(base + (event.key === 'ArrowDown' ? 1 : -1), 0), visible.length - 1)
      setHighlight(next)
      listRef.current?.querySelector(`[data-index="${next}"]`)?.scrollIntoView({ block: 'nearest' })
    } else if (event.key === 'Enter' && open && visible[highlight]) {
      event.preventDefault()
      choose(visible[highlight])
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="picker">
      <input
        id={id}
        type="text"
        autoComplete="off"
        role="combobox"
        aria-label={ariaLabel}
        aria-autocomplete="list"
        aria-expanded={open}
        aria-controls={listId}
        aria-activedescendant={open && visible[highlight] ? `${listId}-${visible[highlight].id}` : undefined}
        disabled={disabled}
        placeholder={selected ? offerLabel(selected) : (placeholder ?? t('picker.placeholder'))}
        value={open ? query : selected ? offerLabel(selected) : query}
        onFocus={() => {
          setOpen(true)
          setHighlight(0)
        }}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onChange={(event) => {
          setQuery(event.target.value)
          setHighlight(0)
          setOpen(true)
          if (value !== null) onChange(null)
        }}
        onKeyDown={onKeyDown}
      />
      {open && (
        <ul className="picker-list" ref={listRef} role="listbox" id={listId}>
          {visible.length === 0 && <li className="muted">{t('picker.nothing')}</li>}
          {visible.map((offer, index) => (
            <li
              key={offer.id}
              id={`${listId}-${offer.id}`}
              data-index={index}
              role="option"
              aria-selected={index === highlight}
              className={index === highlight ? 'highlight' : ''}
              onMouseDown={(event) => {
                event.preventDefault()
                choose(offer)
              }}
              onMouseEnter={() => setHighlight(index)}
            >
              <span>
                {offerLabel(offer)}
                {offer.state && offer.state !== 'active' && <span className="badge">{offer.state}</span>}
              </span>
              <span className="muted small">{offer.country.join(', ')}</span>
            </li>
          ))}
          {matches.length > LIMIT && (
            <li className="muted small">{t('picker.more', { count: matches.length - LIMIT })}</li>
          )}
        </ul>
      )}
    </div>
  )
}
