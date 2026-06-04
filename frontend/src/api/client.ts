import axios from 'axios'
import type {
  Influencer,
  InfluencerDetail,
  InfluencerListResponse,
  ScrapeJob,
  ScrapeResponse,
  Brand,
  BrandDetail,
  MatchResult,
  Collaboration,
  LinkedInfluencer,
} from '@/types'

const api = axios.create({ baseURL: '/api' })

export interface ListParams {
  platform?: string
  min_followers?: number
  max_followers?: number
  min_er?: number
  max_er?: number
  sort_by?: string
  order?: string
  search?: string
  niche?: string
  page?: number
  page_size?: number
}

export const influencerApi = {
  list: (params: ListParams) =>
    api.get<InfluencerListResponse>('/influencers', { params }).then((r) => r.data),

  exportCsv: (params: Omit<ListParams, 'page' | 'page_size'>) => {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') query.append(k, String(v))
    })
    // Trigger browser download directly
    window.location.href = `/api/influencers/export?${query.toString()}`
  },

  get: (id: number) =>
    api.get<InfluencerDetail>(`/influencers/${id}`).then((r) => r.data),

  add: (platform: string, username: string) =>
    api.post<Influencer>('/influencers', { platform, username }).then((r) => r.data),

  bulkAdd: (items: { platform: string; username: string }[]) =>
    api.post<Influencer[]>('/influencers/bulk', { influencers: items }).then((r) => r.data),

  delete: (id: number) => api.delete(`/influencers/${id}`),

  deleteAll: () => api.delete('/influencers'),

  link: (id: number, linkedId: number) =>
    api.post<InfluencerDetail>(`/influencers/${id}/link`, { linked_id: linkedId }).then((r) => r.data),

  unlink: (id: number) =>
    api.delete(`/influencers/${id}/link`),

  csvUpload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<{ added: number; skipped: number; invalid: number; items: { id: number; platform: string; username: string }[] }>(
      '/influencers/csv',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    ).then((r) => r.data)
  },
}

export interface BrandPayload {
  name: string
  description?: string
  ig_link?: string
  tt_link?: string
  categories: string[]
  budget_tier: string
  min_er: number
}

export const brandApi = {
  list: () =>
    api.get<Brand[]>('/brands').then((r) => r.data),

  get: (id: number) =>
    api.get<BrandDetail>(`/brands/${id}`).then((r) => r.data),

  create: (payload: BrandPayload) =>
    api.post<Brand>('/brands', payload).then((r) => r.data),

  update: (id: number, payload: Partial<BrandPayload>) =>
    api.patch<Brand>(`/brands/${id}`, payload).then((r) => r.data),

  delete: (id: number) => api.delete(`/brands/${id}`),

  matches: (id: number) =>
    api.get<MatchResult[]>(`/brands/${id}/matches`).then((r) => r.data),

  addCollaboration: (brandId: number, influencerId: number, status = 'potential') =>
    api.post<Collaboration>(`/brands/${brandId}/collaborations`, { influencer_id: influencerId, status }).then((r) => r.data),

  updateCollaboration: (brandId: number, influencerId: number, status: string, notes?: string) =>
    api.patch<Collaboration>(`/brands/${brandId}/collaborations/${influencerId}`, { status, notes }).then((r) => r.data),

  deleteCollaboration: (brandId: number, influencerId: number) =>
    api.delete(`/brands/${brandId}/collaborations/${influencerId}`),

  fetchIg: (brandId: number) =>
    api.post<Brand>(`/brands/${brandId}/fetch-ig`).then((r) => r.data),
}

export const scrapeApi = {
  trigger: (id: number) =>
    api.post<ScrapeResponse>(`/scrape/${id}`).then((r) => r.data),

  status: (id: number) =>
    api.get<ScrapeJob>(`/scrape/status/${id}`).then((r) => r.data),
}
