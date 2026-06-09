import { RotateCcw, X } from 'lucide-react'
import { clsx } from 'clsx'
import { useFilterStore } from '@/store/filterStore'
import type { Platform } from '@/types'

interface SidebarProps {
  open?: boolean
  onClose?: () => void
}

const PLATFORMS: { value: Platform | ''; label: string }[] = [
  { value: '', label: 'All Platforms' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
]

const SORT_OPTIONS = [
  { value: 'followers', label: 'Followers' },
  { value: 'engagement_rate', label: 'Engagement Rate' },
  { value: 'avg_likes', label: 'Avg. Likes' },
  { value: 'last_scraped_at', label: 'Last Updated' },
]

const NICHES = [
  'Fashion', 'Beauty', 'Food & Beverage', 'Travel', 'Fitness',
  'Lifestyle', 'Tech', 'Business', 'Art & Culture', 'Entertainment',
  'Education', 'Environment',
]

export function Sidebar({ open = false, onClose }: SidebarProps) {
  const {
    platform, setPlatform,
    minFollowers, maxFollowers, setFollowersRange,
    minEr, maxEr, setErRange,
    sortBy, setSortBy,
    order, toggleOrder,
    niche, setNiche,
    reset,
  } = useFilterStore()

  const content = (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 px-4 border-b border-ealan-border flex items-center justify-between shrink-0">
        <span className="text-sm font-semibold text-gray-200">Filters</span>
        <div className="flex items-center gap-1">
          <button
            onClick={reset}
            className="p-1.5 rounded-lg text-ealan-muted hover:text-gray-300 hover:bg-ealan-hover transition-colors"
            title="Reset filters"
          >
            <RotateCcw size={13} />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="sm:hidden p-1.5 rounded-lg text-ealan-muted hover:text-gray-300 hover:bg-ealan-hover transition-colors"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Filter sections */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-6">

        {/* Platform */}
        <section>
          <p className="section-label mb-2">Platform</p>
          <div className="space-y-0.5">
            {PLATFORMS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setPlatform(value)}
                className={clsx(
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                  platform === value
                    ? 'bg-brand-500/15 text-brand-300 font-medium'
                    : 'text-gray-400 hover:bg-ealan-hover hover:text-gray-200'
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </section>

        {/* Followers */}
        <section>
          <p className="section-label mb-2">Followers</p>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={minFollowers}
              onChange={(e) => setFollowersRange(e.target.value ? Number(e.target.value) : '', maxFollowers)}
              className="input-base py-2 text-xs"
            />
            <input
              type="number"
              placeholder="Max"
              value={maxFollowers}
              onChange={(e) => setFollowersRange(minFollowers, e.target.value ? Number(e.target.value) : '')}
              className="input-base py-2 text-xs"
            />
          </div>
        </section>

        {/* Engagement Rate */}
        <section>
          <p className="section-label mb-2">Engagement Rate (%)</p>
          <div className="flex gap-2">
            <input
              type="number"
              step="0.1"
              placeholder="Min"
              value={minEr}
              onChange={(e) => setErRange(e.target.value ? Number(e.target.value) : '', maxEr)}
              className="input-base py-2 text-xs"
            />
            <input
              type="number"
              step="0.1"
              placeholder="Max"
              value={maxEr}
              onChange={(e) => setErRange(minEr, e.target.value ? Number(e.target.value) : '')}
              className="input-base py-2 text-xs"
            />
          </div>
        </section>

        {/* Category */}
        <section>
          <p className="section-label mb-2">Category</p>
          <div className="flex flex-wrap gap-1.5">
            {NICHES.map((n) => (
              <button
                key={n}
                onClick={() => setNiche(niche === n ? '' : n)}
                className={clsx(
                  'px-2.5 py-1 rounded-lg text-xs font-medium transition-colors border',
                  niche === n
                    ? 'bg-brand-500/20 text-brand-300 border-brand-500/40'
                    : 'bg-ealan-bg text-gray-500 border-ealan-border hover:text-gray-300 hover:border-gray-600'
                )}
              >
                {n}
              </button>
            ))}
          </div>
        </section>

        {/* Sort */}
        <section>
          <p className="section-label mb-2">Sort By</p>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="input-base py-2 text-xs mb-2 appearance-none"
          >
            {SORT_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <button
            onClick={toggleOrder}
            className="w-full text-xs text-gray-400 hover:text-gray-200 bg-ealan-bg border border-ealan-border rounded-lg px-3 py-2 transition-colors hover:bg-ealan-hover"
          >
            {order === 'desc' ? '↓ Descending' : '↑ Ascending'}
          </button>
        </section>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop: static sidebar */}
      <aside className="hidden sm:flex w-60 shrink-0 flex-col bg-ealan-surface border-r border-ealan-border overflow-hidden">
        {content}
      </aside>

      {/* Mobile: overlay drawer */}
      {open && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm sm:hidden animate-fade-in"
            onClick={onClose}
          />
          <aside className="fixed inset-y-0 left-0 z-50 w-72 bg-ealan-surface border-r border-ealan-border flex flex-col sm:hidden animate-slide-in-left overflow-hidden">
            {content}
          </aside>
        </>
      )}
    </>
  )
}
