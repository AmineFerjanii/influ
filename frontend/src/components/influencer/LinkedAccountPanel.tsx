import { useState } from 'react'
import { Link2, Link2Off, ExternalLink, Search, X } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import type { LinkedInfluencer, Platform } from '@/types'
import { influencerApi } from '@/api/client'
import { PlatformBadge } from '@/components/common/Badge'
import { formatNumber } from '@/utils/formatters'

interface LinkedAccountPanelProps {
  influencerId: number
  platform: Platform
  linkedInfluencer: LinkedInfluencer | null
}

export function LinkedAccountPanel({ influencerId, platform, linkedInfluencer }: LinkedAccountPanelProps) {
  const [searching, setSearching] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<LinkedInfluencer[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [linking, setLinking] = useState(false)
  const qc = useQueryClient()

  const otherPlatform: Platform = platform === 'instagram' ? 'tiktok' : 'instagram'

  const handleSearch = async (value: string) => {
    setQuery(value)
    if (value.length < 2) { setResults([]); return }
    setIsLoading(true)
    try {
      const resp = await influencerApi.list({ platform: otherPlatform, search: value, page_size: 8 })
      setResults(resp.data as unknown as LinkedInfluencer[])
    } finally {
      setIsLoading(false)
    }
  }

  const handleLink = async (targetId: number) => {
    setLinking(true)
    try {
      await influencerApi.link(influencerId, targetId)
      qc.invalidateQueries({ queryKey: ['influencer', influencerId] })
      setSearching(false)
      setQuery('')
      setResults([])
    } finally {
      setLinking(false)
    }
  }

  const handleUnlink = async () => {
    setLinking(true)
    try {
      await influencerApi.unlink(influencerId)
      qc.invalidateQueries({ queryKey: ['influencer', influencerId] })
    } finally {
      setLinking(false)
    }
  }

  if (linkedInfluencer) {
    const profileUrl = linkedInfluencer.platform === 'instagram'
      ? `https://www.instagram.com/${linkedInfluencer.username}/`
      : `https://www.tiktok.com/@${linkedInfluencer.username}`

    return (
      <div className="flex items-center gap-2 mt-2 px-2 py-1.5 bg-gray-800/60 rounded-lg text-sm">
        <Link2 size={12} className="text-brand-400 shrink-0" />
        <PlatformBadge platform={linkedInfluencer.platform} />
        <a
          href={profileUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-300 hover:text-white flex items-center gap-1 truncate"
        >
          @{linkedInfluencer.username}
          <ExternalLink size={10} />
        </a>
        <span className="text-gray-500 text-xs">{formatNumber(linkedInfluencer.followers)} followers</span>
        <button
          onClick={handleUnlink}
          disabled={linking}
          title="Unlink account"
          className="ml-auto text-gray-600 hover:text-red-400 transition-colors disabled:opacity-40"
        >
          <Link2Off size={12} />
        </button>
      </div>
    )
  }

  if (searching) {
    return (
      <div className="mt-2">
        <div className="flex items-center gap-2 px-2 py-1.5 bg-gray-800/60 rounded-lg">
          <Search size={12} className="text-gray-500 shrink-0" />
          <input
            autoFocus
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder={`Search ${otherPlatform} accounts…`}
            className="flex-1 bg-transparent text-sm text-white placeholder-gray-600 focus:outline-none"
          />
          <button onClick={() => { setSearching(false); setQuery(''); setResults([]) }} className="text-gray-600 hover:text-gray-300">
            <X size={12} />
          </button>
        </div>
        {isLoading && <p className="text-xs text-gray-600 mt-1 px-2">Searching…</p>}
        {results.length > 0 && (
          <div className="mt-1 bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
            {results.map((r) => (
              <button
                key={r.id}
                onClick={() => handleLink(r.id)}
                disabled={linking}
                className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-700 transition-colors text-sm disabled:opacity-40"
              >
                <PlatformBadge platform={r.platform as Platform} />
                <span className="text-gray-200 truncate">@{r.username}</span>
                <span className="text-gray-500 text-xs ml-auto shrink-0">{formatNumber(r.followers)}</span>
              </button>
            ))}
          </div>
        )}
        {!isLoading && query.length >= 2 && results.length === 0 && (
          <p className="text-xs text-gray-600 mt-1 px-2">No {otherPlatform} accounts found for "{query}"</p>
        )}
      </div>
    )
  }

  return (
    <button
      onClick={() => setSearching(true)}
      className="mt-2 flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors px-2 py-1 rounded-lg hover:bg-gray-800/60"
    >
      <Link2 size={11} />
      Link {otherPlatform} account
    </button>
  )
}
