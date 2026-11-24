import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { I18nContext, initialLanguage, localeOf, setLanguage, translate, type Lang, type MessageKey, type Params } from '../i18n'

export default function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    const initial = initialLanguage()
    setLanguage(initial)
    return initial
  })

  const setLang = useCallback((next: Lang) => {
    setLanguage(next)
    setLangState(next)
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  const value = useMemo(
    () => ({
      lang,
      locale: localeOf(lang),
      setLang,
      t: (key: MessageKey, params?: Params) => translate(lang, key, params),
    }),
    [lang, setLang],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}
