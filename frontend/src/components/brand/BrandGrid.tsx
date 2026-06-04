import { Plus } from 'lucide-react'
import type { Brand } from '@/types'
import { BrandCard } from './BrandCard'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'

interface BrandGridProps {
  brands: Brand[]
  isLoading: boolean
  onSelect: (id: number) => void
  onDelete: (id: number) => void
  onAddClick: () => void
}

export function BrandGrid({ brands, isLoading, onSelect, onDelete, onAddClick }: BrandGridProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (brands.length === 0) {
    return (
      <div className="flex-1">
        <EmptyState
          title="No brands yet"
          description="Add a brand to start matching it with the right influencers"
          action={
            <button
              onClick={onAddClick}
              className="bg-brand-500 hover:bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Add Brand
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
          {brands.map((brand) => (
            <BrandCard
              key={brand.id}
              brand={brand}
              onClick={() => onSelect(brand.id)}
              onDelete={() => onDelete(brand.id)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
