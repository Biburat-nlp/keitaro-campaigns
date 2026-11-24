import { useEffect, useState } from 'react'
import { api, type Campaign, type Catalog } from '../api'
import { useI18n } from '../i18n'
import { campaignUrl, formatDate, navigate } from '../utils'

export default function CampaignList({ catalog }: { catalog: Catalog }) {
  const { t, locale } = useI18n()
  const [campaigns, setCampaigns] = useState<Campaign[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .campaigns()
      .then(setCampaigns)
      .catch((e: Error) => setError(e.message))
  }, [])

  const domains = new Map(catalog.domains.map((domain) => [domain.id, domain]))

  return (
    <section>
      <div className="page-head">
        <h1>{t('list.title')}</h1>
        <a className="button primary" href="#/new">
          {t('list.create')}
        </a>
      </div>
      {error && <p className="error">{error}</p>}
      {!campaigns && !error && <p className="muted">{t('common.loading')}</p>}
      {campaigns?.length === 0 && (
        <div className="card empty">
          <p>{t('list.empty')}</p>
          <a className="button primary" href="#/new">
            {t('list.createFirst')}
          </a>
        </div>
      )}
      {campaigns && campaigns.length > 0 && (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('list.colName')}</th>
                <th>{t('list.colLink')}</th>
                <th>{t('list.colState')}</th>
                <th>{t('list.colCreated')}</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((campaign) => {
                const url = campaignUrl(domains.get(campaign.domain_id ?? -1), campaign.alias)
                return (
                  <tr key={campaign.id} className="clickable" onClick={() => navigate(`/campaigns/${campaign.id}`)}>
                    <td className="num">{campaign.id}</td>
                    <td>
                      <a href={`#/campaigns/${campaign.id}`}>{campaign.name}</a>
                      {campaign.created_here && <span className="badge">{t('list.createdHere')}</span>}
                    </td>
                    <td className="mono small">{url ?? campaign.alias}</td>
                    <td>
                      <span className={`state ${campaign.state}`}>{campaign.state}</span>
                    </td>
                    <td className="small muted">{formatDate(campaign.created_at, locale)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
