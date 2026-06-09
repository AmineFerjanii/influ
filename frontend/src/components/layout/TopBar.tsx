import { Search, Plus, X, Trash2, Download, RefreshCw, SlidersHorizontal } from 'lucide-react'
import { clsx } from 'clsx'
import { useFilterStore } from '@/store/filterStore'
import { useViewStore } from '@/store/viewStore'
import { influencerApi } from '@/api/client'
import { useEffect, useRef, useState } from 'react'

interface BulkRefreshState {
  isRefreshing: boolean
  progress: { current: number; total: number }
  start: () => void
  cancel: () => void
}

interface TopBarProps {
  onAddClick: () => void
  onClearAll?: () => void
  onFilterToggle?: () => void
  total?: number
  bulkRefresh?: BulkRefreshState
}

export function TopBar({ onAddClick, onClearAll, onFilterToggle, total, bulkRefresh }: TopBarProps) {
  const { search, setSearch, platform, minFollowers, maxFollowers, minEr, maxEr, sortBy, order, niche } = useFilterStore()
  const { activeView, setActiveView } = useViewStore()
  const [localSearch, setLocalSearch] = useState(search)
  const [searchExpanded, setSearchExpanded] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const searchRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => setSearch(localSearch), 350)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [localSearch, setSearch])

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

  const showInfluencerActions = activeView === 'influencers'

  return (
    <header className="bg-ealan-surface border-b border-ealan-border shrink-0 z-30">
      <div className="h-14 flex items-center px-3 sm:px-4 gap-2 sm:gap-3">

        {/* Logo */}
        <div className="shrink-0">
          <img src="/ealan-logo-white.png" alt="Ealan Group" className="h-6 sm:h-7 w-auto" />
        </div>

        {/* View toggle */}
        <div className="flex bg-ealan-bg rounded-lg p-0.5 gap-0.5 border border-ealan-border shrink-0">
          {(['influencers', 'brands'] as const).map((view) => (
            <button
              key={view}
              onClick={() => setActiveView(view)}
              className={clsx(
                'px-2.5 sm:px-3 py-1 rounded-md text-[11px] sm:text-xs font-medium transition-colors capitalize',
                activeView === view
                  ? 'bg-brand-500 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-300'
              )}
            >
              {view}
            </button>
          ))}
        </div>

        {/* Search — hidden on mobile when collapsed */}
        {showInfluencerActions && (
          <div className={clsx(
            'relative transition-all duration-200',
            searchExpanded
              ? 'flex-1'
              : 'flex-1 max-w-xs hidden sm:block'
          )}>
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-ealan-muted pointer-events-none" />
            <input
              ref={searchRef}
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              placeholder="Search influencers…"
              className="w-full bg-ealan-bg border border-ealan-border rounded-xl pl-8 pr-8 py-2 text-sm text-gray-200 placeholder-ealan-muted focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20 transition-colors"
            />
            {localSearch && (
              <button
                onClick={() => { setLocalSearch(''); setSearch('') }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ealan-muted hover:text-gray-300 p-0.5"
              >
                <X size={11} />
              </button>
            )}
          </div>
        )}

        {/* Right actions */}
        <div className="ml-auto flex items-center gap-1.5">

          {/* Mobile search toggle */}
          {showInfluencerActions && (
            <button
              onClick={() => {
                setSearchExpanded((v) => !v)
                setTimeout(() => searchRef.current?.focus(), 50)
              }}
              className="sm:hidden p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-ealan-hover transition-colors"
              title="Search"
            >
              {searchExpanded ? <X size={16} /> : <Search size={16} />}
            </button>
          )}

          {/* Total count — desktop only */}
          {showInfluencerActions && total !== undefined && (
            <span className="hidden md:block text-ealan-muted text-xs mr-1">
              {total.toLocaleString()} {total === 1 ? 'influencer' : 'influencers'}
            </span>
          )}

          {/* Export — desktop only */}
          {showInfluencerActions && (total ?? 0) > 0 && (
            <button
              onClick={handleExport}
              title="Export as CSV"
              className="hidden sm:flex btn-ghost"
            >
              <Download size={13} />
              <span className="hidden md:inline">Export</span>
            </button>
          )}

          {/* Refresh All */}
          {showInfluencerActions && bulkRefresh && (total ?? 0) > 0 && (
            <button
              onClick={bulkRefresh.isRefreshing ? bulkRefresh.cancel : bulkRefresh.start}
              title={bulkRefresh.isRefreshing ? 'Cancel refresh' : 'Re-scrape all influencers'}
              className={clsx(
                'flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                bulkRefresh.isRefreshing
                  ? 'border-amber-700/60 text-amber-400 hover:border-amber-500'
                  : 'btn-ghost'
              )}
            >
              <RefreshCw size={13} className={bulkRefresh.isRefreshing ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">
                {bulkRefresh.isRefreshing
                  ? `${bulkRefresh.progress.current}/${bulkRefresh.progress.total}`
                  : 'Refresh All'}
              </span>
              {bulkRefresh.isRefreshing && (
                <span className="sm:hidden text-[10px]">
                  {bulkRefresh.progress.current}/{bulkRefresh.progress.total}
                </span>
              )}
            </button>
          )}

          {/* Clear All */}
          {showInfluencerActions && onClearAll && (total ?? 0) > 0 && (
            <button
              onClick={onClearAll}
              title="Remove all influencers"
              className="hidden sm:flex btn-danger"
            >
              <Trash2 size={13} />
              <span className="hidden lg:inline">Clear All</span>
            </button>
          )}

          {/* Filter toggle — mobile only */}
          {showInfluencerActions && onFilterToggle && (
            <button
              onClick={onFilterToggle}
              className="sm:hidden p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-ealan-hover transition-colors border border-ealan-border"
              title="Filters"
            >
              <SlidersHorizontal size={16} />
            </button>
          )}

          {/* Add button */}
          <button
            onClick={onAddClick}
            className="btn-primary px-2.5 sm:px-4"
          >
            <Plus size={14} />
            <span className="hidden sm:inline">
              {activeView === 'brands' ? 'Add Brand' : 'Add Influencer'}
            </span>
          </button>
        </div>
      </div>
    </header>
  )
}
