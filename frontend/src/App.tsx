import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { TopBar } from '@/components/layout/TopBar'
import { Sidebar } from '@/components/layout/Sidebar'
import { InfluencerGrid } from '@/components/influencer/InfluencerGrid'
import { InfluencerModal } from '@/components/influencer/InfluencerModal'
import { AddInfluencerModal } from '@/components/influencer/AddInfluencerModal'
import { BrandGrid } from '@/components/brand/BrandGrid'
import { BrandModal } from '@/components/brand/BrandModal'
import { AddBrandModal } from '@/components/brand/AddBrandModal'
import { useInfluencers } from '@/hooks/useInfluencers'
import { useInfluencer } from '@/hooks/useInfluencer'
import { useScrape } from '@/hooks/useScrape'
import { useBrands } from '@/hooks/useBrands'
import { useViewStore } from '@/store/viewStore'
import { influencerApi, brandApi } from '@/api/client'
import type { Brand } from '@/types'

export default function App() {
  const { activeView } = useViewStore()

  // Influencer state
  const [selectedInfluencerId, setSelectedInfluencerId] = useState<number | null>(null)
  const [addInfluencerOpen, setAddInfluencerOpen] = useState(false)
  const queryClient = useQueryClient()
  const { data, isLoading } = useInfluencers()
  const { data: detail, isLoading: detailLoading } = useInfluencer(selectedInfluencerId)
  const { trigger, scrapingIds } = useScrape()

  // Brand state
  const [selectedBrand, setSelectedBrand] = useState<Brand | null>(null)
  const [addBrandOpen, setAddBrandOpen] = useState(false)
  const { data: brands, isLoading: brandsLoading } = useBrands()

  const handleDeleteInfluencer = async (id: number) => {
    if (!confirm('Remove this influencer?')) return
    await influencerApi.delete(id)
    queryClient.invalidateQueries({ queryKey: ['influencers'] })
    if (selectedInfluencerId === id) setSelectedInfluencerId(null)
  }

  const handleClearAll = async () => {
    if (!confirm('Remove ALL influencers? This cannot be undone.')) return
    await influencerApi.deleteAll()
    queryClient.invalidateQueries({ queryKey: ['influencers'] })
    setSelectedInfluencerId(null)
  }

  const handleDeleteBrand = async (id: number) => {
    if (!confirm('Remove this brand?')) return
    await brandApi.delete(id)
    queryClient.invalidateQueries({ queryKey: ['brands'] })
    if (selectedBrand?.id === id) setSelectedBrand(null)
  }

  const handleAddClick = () => {
    if (activeView === 'brands') setAddBrandOpen(true)
    else setAddInfluencerOpen(true)
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-ealan-bg">
      <TopBar onAddClick={handleAddClick} onClearAll={handleClearAll} total={activeView === 'influencers' ? data?.total : undefined} />

      <div className="flex-1 flex overflow-hidden">
        {activeView === 'influencers' && <Sidebar />}

        <main className="flex-1 flex flex-col overflow-hidden">
          {activeView === 'influencers' ? (
            <InfluencerGrid
              influencers={data?.data ?? []}
              total={data?.total ?? 0}
              isLoading={isLoading}
              onSelect={setSelectedInfluencerId}
              onRefresh={trigger}
              onDelete={handleDeleteInfluencer}
              scrapingIds={scrapingIds}
              onAddClick={() => setAddInfluencerOpen(true)}
            />
          ) : (
            <BrandGrid
              brands={brands ?? []}
              isLoading={brandsLoading}
              onSelect={(id) => setSelectedBrand(brands?.find((b) => b.id === id) ?? null)}
              onDelete={handleDeleteBrand}
              onAddClick={() => setAddBrandOpen(true)}
            />
          )}
        </main>
      </div>

      <InfluencerModal
        influencer={detail}
        isLoading={detailLoading}
        open={selectedInfluencerId !== null}
        onClose={() => setSelectedInfluencerId(null)}
        onRefresh={() => selectedInfluencerId && trigger(selectedInfluencerId)}
        isScraping={selectedInfluencerId !== null && scrapingIds.has(selectedInfluencerId)}
      />

      <AddInfluencerModal open={addInfluencerOpen} onClose={() => setAddInfluencerOpen(false)} />

      <BrandModal
        brand={selectedBrand}
        open={selectedBrand !== null}
        onClose={() => setSelectedBrand(null)}
      />

      <AddBrandModal open={addBrandOpen} onClose={() => setAddBrandOpen(false)} />
    </div>
  )
}
