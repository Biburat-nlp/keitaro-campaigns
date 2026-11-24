import { useCallback, useEffect, useId, useRef, useState, type ReactNode } from 'react'
import { ConfirmContext, type ConfirmOptions } from '../confirm'
import { useI18n } from '../i18n'

type Pending = {
  message: string
  options: ConfirmOptions
  resolve: (value: boolean) => void
}

export default function ConfirmProvider({ children }: { children: ReactNode }) {
  const { t } = useI18n()
  const [pending, setPending] = useState<Pending | null>(null)
  const titleId = useId()
  const confirmRef = useRef<HTMLButtonElement>(null)
  const cancelRef = useRef<HTMLButtonElement>(null)
  const returnFocus = useRef<HTMLElement | null>(null)

  const confirm = useCallback(
    (message: string, options: ConfirmOptions = {}) =>
      new Promise<boolean>((resolve) => {
        returnFocus.current = document.activeElement as HTMLElement | null
        setPending({ message, options, resolve })
      }),
    [],
  )

  const close = useCallback(
    (value: boolean) => {
      pending?.resolve(value)
      setPending(null)
      returnFocus.current?.focus?.()
    },
    [pending],
  )

  useEffect(() => {
    if (!pending) return
    ;(pending.options.danger ? cancelRef : confirmRef).current?.focus()
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [pending, close])

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {pending && (
        <div className="modal-backdrop" onMouseDown={() => close(false)}>
          <div
            className="modal"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <h2 id={titleId}>{pending.options.title ?? t('confirm.title')}</h2>
            <p>{pending.message}</p>
            <div className="actions">
              <button
                ref={confirmRef}
                className={pending.options.danger ? 'danger-solid' : 'primary'}
                onClick={() => close(true)}
              >
                {pending.options.confirmLabel ?? t('confirm.continue')}
              </button>
              <button ref={cancelRef} onClick={() => close(false)}>
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  )
}
