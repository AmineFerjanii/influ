import type { Influencer } from '@/types'
import { InfluencerCard } from './InfluencerCard'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { useFilterStore } from '@/store/filterStore'

interface InfluencerGridProps {
  influencers: Influencer[]
  total: number
  isLoading: boolean
  onSelect: (id: number) => void
  onRefresh: (id: number) => void
  onDelete: (id: number) => void
  scrapingIds: Set<number>
  onAddClick: () => void
}

const PAGE_SIZE = 20

export function InfluencerGrid({
  influencers,
  total,
  isLoading,
  onSelect,
  onRefresh,
  onDelete,
  scrapingIds,
  onAddClick,
}: InfluencerGridProps) {
  const { page, setPage } = useFilterStore()
  const totalPages = Math.ceil(total / PAGE_SIZE)

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (influencers.length === 0) {
    return (
      <div className="flex-1">
        <EmptyState
          title="No influencers found"
          description="Add your first Tunisian influencer or adjust your filters"
          action={
            <button
              onClick={onAddClick}
              className="bg-brand-500 hover:bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Add Influencer
            </button>
          }
        />
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {influencers.map((inf) => (
            <InfluencerCard
              key={inf.id}
              influencer={inf}
              onClick={() => onSelect(inf.id)}
              onRefresh={() => onRefresh(inf.id)}
              onDelete={() => onDelete(inf.id)}
              isScraping={scrapingIds.has(inf.id)}
            />
          ))}
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="border-t border-gray-800 px-4 py-3 flex items-center justify-between bg-gray-900 shrink-0">
          <span className="text-xs text-gray-500">
            {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} of {total.toLocaleString()}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
              className="px-3 py-1 text-xs rounded-lg border border-gray-700 text-gray-400 hover:bg-gray-800 disabled:opacity-40 transition-colors"
            >
              Prev
            </button>
            <span className="px-3 py-1 text-xs text-gray-400">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages}
              className="px-3 py-1 text-xs rounded-lg border border-gray-700 text-gray-400 hover:bg-gray-800 disabled:opacity-40 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
