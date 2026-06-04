import { useQuery } from '@tanstack/react-query'
import { influencerApi, type ListParams } from '@/api/client'
import { useFilterStore } from '@/store/filterStore'

export function useInfluencers() {
  const {
    platform, minFollowers, maxFollowers, minEr, maxEr,
    sortBy, order, search, niche, page,
  } = useFilterStore()

  const params: ListParams = {
    sort_by: sortBy,
    order,
    page,
    page_size: 20,
  }
  if (platform) params.platform = platform
  if (search) params.search = search
  if (niche) params.niche = niche
  if (minFollowers !== '') params.min_followers = Number(minFollowers)
  if (maxFollowers !== '') params.max_followers = Number(maxFollowers)
  if (minEr !== '') params.min_er = Number(minEr)
  if (maxEr !== '') params.max_er = Number(maxEr)

  return useQuery({
    queryKey: ['influencers', params],
    queryFn: () => influencerApi.list(params),
  })
}
