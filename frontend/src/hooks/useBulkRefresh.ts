import { useState, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { influencerApi, scrapeApi } from '@/api/client'

const POLL_MS = 3_000
const JOB_TIMEOUT_MS = 5 * 60_000  // skip influencer after 5 min stuck

export function useBulkRefresh() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [progress, setProgress] = useState({ current: 0, total: 0 })
  // Use a ref for the running guard so the async function never reads stale state
  const runningRef = useRef(false)
  const cancelRef = useRef(false)
  const queryClient = useQueryClient()

  // No isRefreshing in deps — guard is via runningRef to avoid stale closure
  const start = useCallback(async () => {
    if (runningRef.current) return
    runningRef.current = true
    cancelRef.current = false
    setIsRefreshing(true)
    setProgress({ current: 0, total: 0 })

    try {
      const all = await influencerApi.list({ page_size: 10000 })
      const ids = all.data.map((inf) => inf.id)
      if (ids.length === 0) return

      setProgress({ current: 0, total: ids.length })

      for (let i = 0; i < ids.length; i++) {
        if (cancelRef.current) break

        const id = ids[i]
        setProgress({ current: i + 1, total: ids.length })

        try {
          await scrapeApi.trigger(id)
        } catch {
          // backend rejected (not found, etc.) — skip this influencer
          continue
        }

        // Wait for job to reach a terminal state, with a 5-min timeout
        await new Promise<void>((resolve) => {
          let waited = 0
          const interval = setInterval(async () => {
            if (cancelRef.current || waited >= JOB_TIMEOUT_MS) {
              clearInterval(interval)
              resolve()
              return
            }
            waited += POLL_MS
            try {
              const job = await scrapeApi.status(id)
              if (job.status === 'success' || job.status === 'failed') {
                clearInterval(interval)
                queryClient.invalidateQueries({ queryKey: ['influencers'] })
                resolve()
              }
            } catch {
              // network hiccup — keep polling
            }
          }, POLL_MS)
        })
      }
    } catch {
      // list() failed (server offline, etc.) — fall through to finally
    } finally {
      runningRef.current = false
      setIsRefreshing(false)
      setProgress({ current: 0, total: 0 })
      queryClient.invalidateQueries({ queryKey: ['influencers'] })
    }
  }, [queryClient])

  const cancel = useCallback(() => {
    cancelRef.current = true
  }, [])

  return { isRefreshing, progress, start, cancel }
}
