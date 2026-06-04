import { useMutation, useQueryClient } from '@tanstack/react-query'
import { brandApi } from '@/api/client'

export function useCollaboration(brandId: number) {
  const qc = useQueryClient()

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['brands'] })
    qc.invalidateQueries({ queryKey: ['brand-matches', brandId] })
  }

  const add = useMutation({
    mutationFn: ({ influencerId, status }: { influencerId: number; status?: string }) =>
      brandApi.addCollaboration(brandId, influencerId, status),
    onSuccess: invalidate,
  })

  const update = useMutation({
    mutationFn: ({ influencerId, status, notes }: { influencerId: number; status: string; notes?: string }) =>
      brandApi.updateCollaboration(brandId, influencerId, status, notes),
    onSuccess: invalidate,
  })

  const remove = useMutation({
    mutationFn: ({ influencerId }: { influencerId: number }) =>
      brandApi.deleteCollaboration(brandId, influencerId),
    onSuccess: invalidate,
  })

  return { add, update, remove }
}
