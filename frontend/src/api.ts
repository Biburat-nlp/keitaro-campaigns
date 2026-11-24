import { getLanguage, translate } from './i18n'

export type NamedItem = { id: number; name: string }

export type Domain = NamedItem & { is_ssl?: boolean }

export type Catalog = {
  domains: Domain[]
  groups: NamedItem[]
  traffic_sources: NamedItem[]
  countries: string[]
  defaults: { domain_id: number; group_id: number; traffic_source_id: number }
}

export type Offer = {
  id: number
  name: string
  country: string[]
  state: string | null
  payout_value: number | null
  payout_currency: string | null
}

export type StreamOffer = {
  offer_id: number
  share: number
  pinned: boolean
  status: 'active' | 'removed'
  state: string
  committed_status: 'active' | 'removed' | null
  committed_share: number
  is_new: boolean
  dirty: boolean
}

export type StreamFilter = { name: string; mode: string; payload: unknown }

export type Stream = {
  id: number
  campaign_id: number
  name: string
  type: string
  schema: string
  position: number
  state: string
  action_type?: string | null
  action_payload?: string | null
  filters?: StreamFilter[]
  offers: StreamOffer[]
  dirty: boolean
  total: number
  active_count: number
  synced_at: string | null
}

export type Campaign = {
  id: number
  name: string
  alias: string
  state: string
  type?: string
  domain_id?: number | null
  group_id?: number | null
  traffic_source_id?: number | null
  created_at?: string
  created_here?: boolean
}

export type CampaignDetails = {
  campaign: Campaign
  streams: Stream[]
  admin_url: string
  created_here: boolean
}

export type Operation = {
  id: number
  campaign_id: number
  stream_id: number | null
  action: string
  details: Record<string, unknown>
  created_at: string
}

export type OperationsPage = {
  items: Operation[]
  total: number
  offset: number
  limit: number
}

export type CampaignCreate = {
  name: string
  countries: string[]
  offer_id: number
  domain_id: number
  group_id: number
  traffic_source_id: number
}

function formatDetail(detail: unknown): string | null {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => String(item?.msg ?? item).replace(/^Value error, /, ''))
      .join('; ')
  }
  return null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', 'Accept-Language': getLanguage(), ...init?.headers },
    })
  } catch {
    throw new Error(translate(getLanguage(), 'common.backendDown'))
  }
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`
    try {
      message = formatDetail((await response.json()).detail) ?? message
    } catch {
      message = `${response.status} ${response.statusText}`
    }
    throw new Error(message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  catalog: () => request<Catalog>('/catalog'),
  offers: () => request<Offer[]>('/offers'),
  campaigns: () => request<Campaign[]>('/campaigns?limit=200'),
  campaign: (id: number) => request<CampaignDetails>(`/campaigns/${id}`),
  operations: (id: number, offset: number, limit: number) =>
    request<OperationsPage>(`/campaigns/${id}/operations?offset=${offset}&limit=${limit}`),
  createCampaign: (data: CampaignCreate) =>
    request<CampaignDetails>('/campaigns', { method: 'POST', body: JSON.stringify(data) }),
  renameCampaign: (id: number, name: string) =>
    request<Campaign>(`/campaigns/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
  deleteCampaign: (id: number) => request<void>(`/campaigns/${id}`, { method: 'DELETE' }),
  syncCampaign: (id: number) => request<CampaignDetails>(`/campaigns/${id}/sync`, { method: 'POST' }),
  addOffer: (streamId: number, offerId: number) =>
    request<Stream>(`/streams/${streamId}/offers`, {
      method: 'POST',
      body: JSON.stringify({ offer_id: offerId }),
    }),
  removeOffer: (streamId: number, offerId: number) =>
    request<Stream>(`/streams/${streamId}/offers/${offerId}/remove`, { method: 'POST' }),
  restoreOffer: (streamId: number, offerId: number) =>
    request<Stream>(`/streams/${streamId}/offers/${offerId}/restore`, { method: 'POST' }),
  setShare: (streamId: number, offerId: number, share: number) =>
    request<Stream>(`/streams/${streamId}/offers/${offerId}/share`, {
      method: 'PUT',
      body: JSON.stringify({ share }),
    }),
  setPinned: (streamId: number, offerId: number, pinned: boolean) =>
    request<Stream>(`/streams/${streamId}/offers/${offerId}/pin`, {
      method: 'PUT',
      body: JSON.stringify({ pinned }),
    }),
  publishStream: (streamId: number) => request<Stream>(`/streams/${streamId}/publish`, { method: 'POST' }),
  cancelDraft: (streamId: number) => request<Stream>(`/streams/${streamId}/cancel`, { method: 'POST' }),
  addCountries: (streamId: number, countries: string[]) =>
    request<Stream>(`/streams/${streamId}/countries`, {
      method: 'POST',
      body: JSON.stringify({ countries }),
    }),
  removeCountry: (streamId: number, code: string) =>
    request<Stream>(`/streams/${streamId}/countries/${encodeURIComponent(code)}`, { method: 'DELETE' }),
}
