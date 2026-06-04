import { useState, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { scrapeApi } from '@/api/client'

export function useScrape() {
  const [scrapingIds, setScrapingIds] = useState<Set<number>>(new Set())
  const queryClient = useQueryClient()
  const timers = useRef<Map<number, ReturnType<typeof setInterval>>>(new Map())

  const trigger = async (influencerId: number) => {
    if (scrapingIds.has(influencerId)) return

    setScrapingIds((prev) => new Set(prev).add(influencerId))

    try {
      await scrapeApi.trigger(influencerId)
    } catch {
      setScrapingIds((prev) => {
        const next = new Set(prev)
        next.delete(influencerId)
        return next
      })
      return
    }

    const interval = setInterval(async () => {
      try {
        const job = await scrapeApi.status(influencerId)
        if (job.status === 'success' || job.status === 'failed') {
          clearInterval(timers.current.get(influencerId))
          timers.current.delete(influencerId)
          setScrapingIds((prev) => {
            const next = new Set(prev)
            next.delete(influencerId)
            return next
          })
          queryClient.invalidateQueries({ queryKey: ['influencer', influencerId] })
          queryClient.invalidateQueries({ queryKey: ['influencers'] })
        }
      } catch {
        // keep polling
      }
    }, 3000)

    timers.current.set(influencerId, interval)
  }

  return { trigger, scrapingIds }
}
