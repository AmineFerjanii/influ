import * as Dialog from '@radix-ui/react-dialog'
import { X, Building2, Instagram, Music2 } from 'lucide-react'
import { useState } from 'react'
import { clsx } from 'clsx'
import type { Brand, CollabStatus, MatchResult } from '@/types'
import { useBrandMatches } from '@/hooks/useBrandMatches'
import { useCollaboration } from '@/hooks/useCollaboration'
import { MatchedInfluencerRow } from './MatchedInfluencerRow'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { formatNumber, proxyImage } from '@/utils/formatters'
import { PlatformBadge } from '@/components/common/Badge'

const TIER_LABELS: Record<string, string> = {
  nano: 'Nano <10K',
  micro: 'Micro 10–100K',
  macro: 'Macro 100K–1M',
  mega: 'Mega 1M+',
}

const STATUS_OPTIONS: { value: CollabStatus; label: string }[] = [
  { value: 'potential', label: 'Potential' },
  { value: 'contacted', label: 'Contacted' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'done', label: 'Done' },
]

const STATUS_COLORS: Record<CollabStatus, string> = {
  potential: 'text-gray-400',
  contacted: 'text-blue-400',
  in_progress: 'text-yellow-400',
  done: 'text-green-400',
}

interface PipelineRowProps {
  match: MatchResult
  brandId: number
  onStatusChange: (influencerId: number, status: string) => void
  onRemove: (influencerId: number) => void
}

function PipelineRow({ match, brandId, onStatusChange, onRemove }: PipelineRowProps) {
  const collab = match.collaboration!
  return (
    <div className="flex items-center gap-3 py-3 border-b border-gray-800 last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-semibold text-white truncate">
            {match.display_name || match.username}
          </span>
          <PlatformBadge platform={match.platform} />
        </div>
        <div className="text-xs text-gray-500 mt-0.5">
          {formatNumber(match.followers)} followers · ER {match.engagement_rate.toFixed(1)}%
        </div>
      </div>

      <select
        value={collab.status}
        onChange={(e) => onStatusChange(match.id, e.target.value)}
        className={clsx(
          'text-xs bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 focus:outline-none focus:border-brand-500 transition-colors',
          STATUS_COLORS[collab.status as CollabStatus]
        )}
      >
        {STATUS_OPTIONS.map(({ value, label }) => (
          <option key={value} value={value}>{label}</option>
        ))}
      </select>

      <button
        onClick={() => onRemove(match.id)}
        className="text-xs text-gray-600 hover:text-red-400 transition-colors px-1"
        title="Remove from pipeline"
      >
        <X size={12} />
      </button>
    </div>
  )
}

interface BrandModalProps {
  brand: Brand | null
  open: boolean
  onClose: () => void
}

export function BrandModal({ brand, open, onClose }: BrandModalProps) {
  const [tab, setTab] = useState<'matches' | 'pipeline'>('matches')
  const [addingId, setAddingId] = useState<number | null>(null)

  const { data: matches, isLoading } = useBrandMatches(brand?.id ?? null)
  const { add, update, remove } = useCollaboration(brand?.id ?? 0)

  const pipeline = (matches ?? []).filter((m) => m.collaboration !== null)

  const handleAddToPipeline = async (influencerId: number) => {
    if (!brand) return
    setAddingId(influencerId)
    try {
      await add.mutateAsync({ influencerId, status: 'potential' })
    } finally {
      setAddingId(null)
    }
  }

  const handleStatusChange = (influencerId: number, status: string) => {
    if (!brand) return
    update.mutate({ influencerId, status })
  }

  const handleRemove = (influencerId: number) => {
    if (!brand) return
    remove.mutate({ influencerId })
  }

  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl flex flex-col max-h-[85vh]">
          <Dialog.Close className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors z-10">
            <X size={16} />
          </Dialog.Close>

          {brand && (
            <>
              {/* Header */}
              <div className="p-6 border-b border-gray-800 shrink-0">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-full bg-gray-800 flex items-center justify-center shrink-0 overflow-hidden">
                    {brand.profile_pic_url ? (
                      <img
                        src={proxyImage(brand.profile_pic_url)}
                        alt={brand.name}
                        className="w-full h-full object-cover"
                        onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                      />
                    ) : (
                      <Building2 size={22} className="text-gray-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <Dialog.Title className="text-lg font-bold text-white">{brand.name}</Dialog.Title>
                    {brand.description && (
                      <p className="text-sm text-gray-400 mt-0.5">{brand.description}</p>
                    )}
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {brand.ig_link && (
                        <a href={brand.ig_link} target="_blank" rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium bg-pink-500/15 text-pink-400 hover:bg-pink-500/25 transition-colors"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Instagram size={10} /> Instagram
                        </a>
                      )}
                      {brand.tt_link && (
                        <a href={brand.tt_link} target="_blank" rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium bg-cyan-500/15 text-cyan-400 hover:bg-cyan-500/25 transition-colors"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Music2 size={10} /> TikTok
                        </a>
                      )}
                      <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                        {TIER_LABELS[brand.budget_tier] ?? brand.budget_tier}
                      </span>
                      {brand.min_er > 0 && (
                        <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                          Min ER {brand.min_er}%
                        </span>
                      )}
                      {brand.categories.map((cat) => (
                        <span key={cat} className="text-xs bg-brand-500/10 text-brand-400 px-2 py-0.5 rounded-full">
                          {cat}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-1 mt-4">
                  {(['matches', 'pipeline'] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setTab(t)}
                      className={clsx(
                        'px-4 py-1.5 rounded-lg text-sm font-medium transition-colors',
                        tab === t
                          ? 'bg-brand-500/20 text-brand-400'
                          : 'text-gray-500 hover:text-gray-300'
                      )}
                    >
                      {t === 'matches'
                        ? `Matched Influencers${matches ? ` (${matches.length})` : ''}`
                        : `Pipeline${pipeline.length > 0 ? ` (${pipeline.length})` : ''}`
                      }
                    </button>
                  ))}
                </div>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-2">
                {isLoading ? (
                  <div className="flex justify-center py-12">
                    <LoadingSpinner size="lg" />
                  </div>
                ) : tab === 'matches' ? (
                  matches && matches.length > 0 ? (
                    matches.map((match) => (
                      <MatchedInfluencerRow
                        key={match.id}
                        match={match}
                        onAddToPipeline={handleAddToPipeline}
                        isAdding={addingId === match.id}
                      />
                    ))
                  ) : (
                    <p className="text-sm text-gray-500 text-center py-12">
                      No influencers in the database match this brand's criteria yet.
                    </p>
                  )
                ) : (
                  pipeline.length > 0 ? (
                    pipeline.map((match) => (
                      <PipelineRow
                        key={match.id}
                        match={match}
                        brandId={brand.id}
                        onStatusChange={handleStatusChange}
                        onRemove={handleRemove}
                      />
                    ))
                  ) : (
                    <p className="text-sm text-gray-500 text-center py-12">
                      No influencers in the pipeline yet. Add some from the Matched Influencers tab.
                    </p>
                  )
                )}
              </div>
            </>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
