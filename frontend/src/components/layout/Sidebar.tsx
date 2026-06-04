import { RotateCcw } from 'lucide-react'
import { useFilterStore } from '@/store/filterStore'
import type { Platform } from '@/types'

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

export function Sidebar() {
  const {
    platform, setPlatform,
    minFollowers, maxFollowers, setFollowersRange,
    minEr, maxEr, setErRange,
    sortBy, setSortBy,
    order, toggleOrder,
    niche, setNiche,
    reset,
  } = useFilterStore()

  return (
    <aside className="w-60 shrink-0 bg-ealan-surface border-r border-ealan-border flex flex-col overflow-y-auto scrollbar-thin">
      <div className="p-4 border-b border-ealan-border flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-300">Filters</span>
        <button onClick={reset} className="text-gray-500 hover:text-gray-300 transition-colors" title="Reset filters">
          <RotateCcw size={13} />
        </button>
      </div>

      <div className="p-4 space-y-6">
        {/* Platform */}
        <section>
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">
            Platform
          </label>
          <div className="space-y-1">
            {PLATFORMS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setPlatform(value)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  platform === value
                    ? 'bg-brand-500/20 text-brand-400 font-medium'
                    : 'text-gray-400 hover:bg-ealan-hover hover:text-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </section>

        {/* Followers */}
        <section>
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">
            Followers
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={minFollowers}
              onChange={(e) => setFollowersRange(e.target.value ? Number(e.target.value) : '', maxFollowers)}
              className="w-full bg-ealan-bg border border-ealan-border rounded-lg px-2 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500"
            />
            <input
              type="number"
              placeholder="Max"
              value={maxFollowers}
              onChange={(e) => setFollowersRange(minFollowers, e.target.value ? Number(e.target.value) : '')}
              className="w-full bg-ealan-bg border border-ealan-border rounded-lg px-2 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500"
            />
          </div>
        </section>

        {/* Engagement Rate */}
        <section>
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">
            Engagement Rate (%)
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              step="0.1"
              placeholder="Min"
              value={minEr}
              onChange={(e) => setErRange(e.target.value ? Number(e.target.value) : '', maxEr)}
              className="w-full bg-ealan-bg border border-ealan-border rounded-lg px-2 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500"
            />
            <input
              type="number"
              step="0.1"
              placeholder="Max"
              value={maxEr}
              onChange={(e) => setErRange(minEr, e.target.value ? Number(e.target.value) : '')}
              className="w-full bg-ealan-bg border border-ealan-border rounded-lg px-2 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500"
            />
          </div>
        </section>

        {/* Category / Niche */}
        <section>
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">
            Category
          </label>
          <div className="flex flex-wrap gap-1.5">
            {NICHES.map((n) => (
              <button
                key={n}
                onClick={() => setNiche(niche === n ? '' : n)}
                className={`px-2 py-1 rounded-md text-xs transition-colors ${
                  niche === n
                    ? 'bg-brand-500/30 text-brand-300 border border-brand-500/50 font-medium'
                    : 'bg-ealan-bg text-gray-400 border border-ealan-border hover:text-gray-200 hover:border-gray-500'
                }`}
              >
                {n}
              </button>
            ))}
          </div>
        </section>

        {/* Sort */}
        <section>
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">
            Sort By
          </label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full bg-ealan-bg border border-ealan-border rounded-lg px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:border-brand-500 mb-2"
          >
            {SORT_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <button
            onClick={toggleOrder}
            className="w-full text-xs text-gray-400 hover:text-gray-200 bg-ealan-bg border border-ealan-border rounded-lg px-2 py-1.5 transition-colors"
          >
            {order === 'desc' ? '↓ Descending' : '↑ Ascending'}
          </button>
        </section>
      </div>
    </aside>
  )
}
