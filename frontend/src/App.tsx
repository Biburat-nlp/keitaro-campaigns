import { useCallback, useEffect, useState } from 'react'
import { api, type Catalog, type Offer } from './api'
import ConfirmProvider from './components/ConfirmProvider'
import I18nProvider from './components/I18nProvider'
import LanguageSwitcher from './components/LanguageSwitcher'
import { useI18n } from './i18n'
import CampaignEditor from './pages/CampaignEditor'
import CampaignList from './pages/CampaignList'
import CreateCampaign from './pages/CreateCampaign'

function currentRoute(): string {
  return window.location.hash.replace(/^#/, '') || '/'
}

function Shell() {
  const { t } = useI18n()
  const [route, setRoute] = useState(currentRoute)
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [offers, setOffers] = useState<Offer[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    Promise.all([api.catalog(), api.offers()])
      .then(([catalogData, offersData]) => {
        setCatalog(catalogData)
        setOffers(offersData)
      })
      .catch((e: Error) => setError(e.message))
  }, [])

  useEffect(() => {
    const onChange = () => setRoute(currentRoute())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  useEffect(load, [load])

  const editorMatch = route.match(/^\/campaigns\/(\d+)$/)

  let page
  if (error) {
    page = (
      <div className="card">
        <p className="error">{t('app.catalogError', { error })}</p>
        <button
          onClick={() => {
            setError(null)
            load()
          }}
        >
          {t('common.retry')}
        </button>
      </div>
    )
  } else if (!catalog) {
    page = <p className="muted">{t('common.loading')}</p>
  } else if (route === '/new') {
    page = <CreateCampaign catalog={catalog} offers={offers} />
  } else if (editorMatch) {
    page = <CampaignEditor key={editorMatch[1]} campaignId={Number(editorMatch[1])} catalog={catalog} offers={offers} />
  } else {
    page = <CampaignList catalog={catalog} />
  }

  return (
    <ConfirmProvider>
      <header className="topbar">
        <a href="#/" className="brand">
          Keitaro Campaigns
        </a>
        <nav>
          <a href="#/" className={route === '/' ? 'active' : ''}>
            {t('nav.campaigns')}
          </a>
          <a href="#/new" className={route === '/new' ? 'active' : ''}>
            {t('nav.new')}
          </a>
        </nav>
        <LanguageSwitcher />
      </header>
      <main className="container">{page}</main>
    </ConfirmProvider>
  )
}

export default function App() {
  return (
    <I18nProvider>
      <Shell />
    </I18nProvider>
  )
}
