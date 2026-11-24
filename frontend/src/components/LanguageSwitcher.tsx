import { LANGS, useI18n } from '../i18n'

export default function LanguageSwitcher() {
  const { lang, setLang, t } = useI18n()
  return (
    <div className="lang-switch" role="group" aria-label={t('lang.label')}>
      {LANGS.map((item) => (
        <button
          key={item}
          type="button"
          lang={item}
          aria-pressed={lang === item}
          className={lang === item ? 'on' : ''}
          onClick={() => setLang(item)}
        >
          {item.toUpperCase()}
        </button>
      ))}
    </div>
  )
}
