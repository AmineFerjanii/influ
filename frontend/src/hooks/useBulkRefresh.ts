import { useState, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { influencerApi, scrapeApi } from '@/api/client'

export function useBulkRefresh() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [progress, setProgress] = useState({ current: 0, total: 0 })
  const cancelRef = useRef(false)
  const queryClient = useQueryClient()

  const start = useCallback(async () => {
    if (isRefreshing) return
    cancelRef.current = false
    setIsRefreshing(true)

    try {
      const all = await influencerApi.list({ page_size: 10000 })
      const ids = all.data.map((inf) => inf.id)
      setProgress({ current: 0, total: ids.length })

      for (let i = 0; i < ids.length; i++) {
        if (cancelRef.current) break
        const id = ids[i]
        setProgress({ current: i + 1, total: ids.length })

        try {
          await scrapeApi.trigger(id)
        } catch {
          // already running or other transient error — skip
          continue
        }

        // Poll until this job finishes before moving to the next
        await new Promise<void>((resolve) => {
          const interval = setInterval(async () => {
            if (cancelRef.current) {
              clearInterval(interval)
              resolve()
              return
            }
            try {
              const job = await scrapeApi.status(id)
              if (job.status === 'success' || job.status === 'failed') {
                clearInterval(interval)
                queryClient.invalidateQueries({ queryKey: ['influencers'] })
                resolve()
              }
            } catch {
              // keep polling
            }
          }, 3000)
        })
      }
    } finally {
      setIsRefreshing(false)
      setProgress({ current: 0, total: 0 })
      queryClient.invalidateQueries({ queryKey: ['influencers'] })
    }
  }, [isRefreshing, queryClient])

  const cancel = useCallback(() => {
    cancelRef.current = true
  }, [])

  return { isRefreshing, progress, start, cancel }
}
