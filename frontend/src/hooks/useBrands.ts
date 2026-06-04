import { useQuery } from '@tanstack/react-query'
import { brandApi } from '@/api/client'

export function useBrands() {
  return useQuery({
    queryKey: ['brands'],
    queryFn: () => brandApi.list(),
  })
}
