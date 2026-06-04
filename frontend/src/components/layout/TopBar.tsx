import { Search, Plus, X, Trash2, Download } from 'lucide-react'
import { clsx } from 'clsx'
import { useFilterStore } from '@/store/filterStore'
import { useViewStore } from '@/store/viewStore'
import { influencerApi } from '@/api/client'
import { useEffect, useRef, useState } from 'react'

interface TopBarProps {
  onAddClick: () => void
  onClearAll?: () => void
  total?: number
}

export function TopBar({ onAddClick, onClearAll, total }: TopBarProps) {
  const { search, setSearch, platform, minFollowers, maxFollowers, minEr, maxEr, sortBy, order, niche } = useFilterStore()
  const { activeView, setActiveView } = useViewStore()

  function handleExport() {
    influencerApi.exportCsv({
      platform: platform || undefined,
      min_followers: minFollowers !== '' ? Number(minFollowers) : undefined,
      max_followers: maxFollowers !== '' ? Number(maxFollowers) : undefined,
      min_er: minEr !== '' ? Number(minEr) : undefined,
      max_er: maxEr !== '' ? Number(maxEr) : undefined,
      sort_by: sortBy,
      order,
      search: search || undefined,
      niche: niche || undefined,
    })
  }
  const [localSearch, setLocalSearch] = useState(search)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => setSearch(localSearch), 350)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [localSearch, setSearch])

  return (
    <header className="h-14 bg-ealan-surface border-b border-ealan-border flex items-center px-4 gap-4 shrink-0">
      <div className="flex items-center gap-3 shrink-0">
        <img src="/ealan-logo-white.png" alt="Ealan Group" className="h-7 w-auto" />
      </div>

      {/* View toggle */}
      <div className="flex bg-ealan-bg rounded-lg p-0.5 gap-0.5 border border-ealan-border">
        {(['influencers', 'brands'] as const).map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={clsx(
              'px-3 py-1 rounded-md text-xs font-medium transition-colors capitalize',
              activeView === view
                ? 'bg-ealan-hover text-white'
                : 'text-gray-500 hover:text-gray-300'
            )}
          >
            {view}
          </button>
        ))}
      </div>

      {activeView === 'influencers' && (
        <div className="flex-1 max-w-md relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            placeholder="Search by username or name…"
            className="w-full bg-ealan-bg border border-ealan-border rounded-lg pl-9 pr-8 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
          />
          {localSearch && (
            <button
              onClick={() => { setLocalSearch(''); setSearch('') }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
            >
              <X size={12} />
            </button>
          )}
        </div>
      )}

      <div className="ml-auto flex items-center gap-2">
        {activeView === 'influencers' && total !== undefined && (
          <span className="text-gray-500 text-sm">{total.toLocaleString()} influencer{total !== 1 ? 's' : ''}</span>
        )}
        {activeView === 'influencers' && (total ?? 0) > 0 && (
          <button
            onClick={handleExport}
            title="Export current list as CSV"
            className="flex items-center gap-1.5 border border-ealan-border hover:border-gray-500 text-gray-400 hover:text-gray-200 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
          >
            <Download size={14} />
            Export
          </button>
        )}
        {activeView === 'influencers' && onClearAll && (total ?? 0) > 0 && (
          <button
            onClick={onClearAll}
            title="Remove all influencers"
            className="flex items-center gap-1.5 border border-red-800 hover:border-red-600 text-red-500 hover:text-red-400 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
          >
            <Trash2 size={14} />
            Clear All
          </button>
        )}
        <button
          onClick={onAddClick}
          className="flex items-center gap-1.5 bg-brand-500 hover:bg-brand-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={14} />
          {activeView === 'brands' ? 'Add Brand' : 'Add Influencer'}
        </button>
      </div>
    </header>
  )
}
