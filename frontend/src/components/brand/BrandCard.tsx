import { Trash2, Users, Building2, Instagram, Music2 } from 'lucide-react'
import { clsx } from 'clsx'
import type { Brand } from '@/types'
import { proxyImage } from '@/utils/formatters'

const TIER_COLORS: Record<string, string> = {
  nano:  'bg-ealan-hover text-gray-400 border-ealan-border',
  micro: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  macro: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  mega:  'bg-amber-500/10 text-amber-400 border-amber-500/20',
}

const TIER_LABELS: Record<string, string> = {
  nano:  'Nano <10K',
  micro: 'Micro 10K–100K',
  macro: 'Macro 100K–1M',
  mega:  'Mega 1M+',
}

interface BrandCardProps {
  brand: Brand
  onClick: () => void
  onDelete: () => void
}

export function BrandCard({ brand, onClick, onDelete }: BrandCardProps) {
  return (
    <div
      className="card-interactive group flex flex-col p-4 gap-3.5"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="w-11 h-11 rounded-full bg-ealan-hover flex items-center justify-center shrink-0 overflow-hidden ring-1 ring-ealan-border">
          {brand.profile_pic_url ? (
            <img
              src={proxyImage(brand.profile_pic_url)}
              alt={brand.name}
              className="w-full h-full object-cover"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          ) : (
            <Building2 size={18} className="text-gray-500" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-white truncate leading-tight">{brand.name}</p>
          {brand.description && (
            <p className="text-[11px] text-ealan-muted line-clamp-1 mt-0.5">{brand.description}</p>
          )}
          <div className="mt-1.5 flex flex-wrap gap-1">
            {brand.ig_link && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-pink-500/10 text-pink-400 border border-pink-500/20">
                <Instagram size={9} /> IG
              </span>
            )}
            {brand.tt_link && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Music2 size={9} /> TT
              </span>
            )}
            <span className={clsx(
              'text-[10px] px-1.5 py-0.5 rounded-full font-medium border',
              TIER_COLORS[brand.budget_tier] ?? 'bg-ealan-hover text-gray-400 border-ealan-border'
            )}>
              {TIER_LABELS[brand.budget_tier] ?? brand.budget_tier}
            </span>
          </div>
        </div>

        <button
          className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-red-950/50 text-gray-600 hover:text-red-400 transition-colors shrink-0"
          onClick={(e) => { e.stopPropagation(); onDelete() }}
          title="Delete brand"
        >
          <Trash2 size={12} />
        </button>
      </div>

      {/* Category chips */}
      {brand.categories.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {brand.categories.slice(0, 3).map((cat) => (
            <span key={cat} className="text-[10px] bg-ealan-hover text-gray-400 px-2 py-0.5 rounded-full border border-ealan-border">
              {cat}
            </span>
          ))}
          {brand.categories.length > 3 && (
            <span className="text-[10px] text-ealan-muted">+{brand.categories.length - 3}</span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-ealan-border/60 text-[11px] text-gray-600">
        <span className="flex items-center gap-1">
          <Users size={10} />
          {brand.collaboration_count} collab{brand.collaboration_count !== 1 ? 's' : ''}
        </span>
        {brand.min_er > 0 && <span>Min ER {brand.min_er}%</span>}
      </div>
    </div>
  )
}
