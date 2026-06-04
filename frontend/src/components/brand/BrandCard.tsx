import { Trash2, Users, Building2, Instagram, Music2 } from 'lucide-react'
import { clsx } from 'clsx'
import type { Brand } from '@/types'
import { proxyImage } from '@/utils/formatters'

const TIER_LABELS: Record<string, string> = {
  nano: 'Nano <10K',
  micro: 'Micro 10K–100K',
  macro: 'Macro 100K–1M',
  mega: 'Mega 1M+',
}

const TIER_COLORS: Record<string, string> = {
  nano: 'bg-ealan-hover text-gray-300',
  micro: 'bg-blue-500/15 text-blue-400',
  macro: 'bg-purple-500/15 text-purple-400',
  mega: 'bg-yellow-500/15 text-yellow-400',
}

interface BrandCardProps {
  brand: Brand
  onClick: () => void
  onDelete: () => void
}

export function BrandCard({ brand, onClick, onDelete }: BrandCardProps) {
  return (
    <div
      className="bg-ealan-card border border-ealan-border rounded-2xl p-4 hover:border-brand-500/40 transition-all cursor-pointer group flex flex-col gap-3"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="w-11 h-11 rounded-full bg-ealan-hover flex items-center justify-center shrink-0 overflow-hidden">
          {brand.profile_pic_url ? (
            <img
              src={proxyImage(brand.profile_pic_url)}
              alt={brand.name}
              className="w-full h-full object-cover"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          ) : (
            <Building2 size={20} className="text-gray-500" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <span className="font-semibold text-sm text-white block truncate">{brand.name}</span>
          {brand.description && (
            <span className="text-xs text-gray-500 line-clamp-1">{brand.description}</span>
          )}
          <div className="mt-1 flex flex-wrap gap-1">
            {brand.ig_link && (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium bg-pink-500/15 text-pink-400">
                <Instagram size={10} /> Instagram
              </span>
            )}
            {brand.tt_link && (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium bg-cyan-500/15 text-cyan-400">
                <Music2 size={10} /> TikTok
              </span>
            )}
            {!brand.ig_link && !brand.tt_link && (
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-ealan-hover text-gray-400">
                All platforms
              </span>
            )}
            <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', TIER_COLORS[brand.budget_tier] ?? 'bg-gray-700 text-gray-300')}>
              {TIER_LABELS[brand.budget_tier] ?? brand.budget_tier}
            </span>
          </div>
        </div>

        <button
          className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-red-900/40 text-gray-500 hover:text-red-400 transition-colors"
          onClick={(e) => { e.stopPropagation(); onDelete() }}
          title="Delete brand"
        >
          <Trash2 size={13} />
        </button>
      </div>

      {/* Niche chips */}
      {brand.categories.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {brand.categories.map((cat) => (
            <span key={cat} className="text-xs bg-ealan-hover text-gray-400 px-2 py-0.5 rounded-full">
              {cat}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-600 border-t border-ealan-border pt-2">
        <span className="flex items-center gap-1">
          <Users size={11} />
          {brand.collaboration_count} collaboration{brand.collaboration_count !== 1 ? 's' : ''}
        </span>
        {brand.min_er > 0 && (
          <span>Min ER {brand.min_er}%</span>
        )}
      </div>
    </div>
  )
}
