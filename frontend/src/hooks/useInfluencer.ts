import { useQuery } from '@tanstack/react-query'
import { influencerApi } from '@/api/client'

export function useInfluencer(id: number | null) {
  return useQuery({
    queryKey: ['influencer', id],
    queryFn: () => influencerApi.get(id!),
    enabled: id !== null,
  })
}
