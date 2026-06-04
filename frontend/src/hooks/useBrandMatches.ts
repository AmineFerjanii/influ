import { useQuery } from '@tanstack/react-query'
import { brandApi } from '@/api/client'

export function useBrandMatches(brandId: number | null) {
  return useQuery({
    queryKey: ['brand-matches', brandId],
    queryFn: () => brandApi.matches(brandId!),
    enabled: brandId !== null,
  })
}
