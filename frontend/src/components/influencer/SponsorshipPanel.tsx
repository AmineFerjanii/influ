import { ExternalLink, Info } from 'lucide-react'
import type { SponsoredPost } from '@/types'
import { proxyImage } from '@/utils/formatters'

interface SponsorshipPanelProps {
  sponsorships: SponsoredPost[]
}

export function SponsorshipPanel({ sponsorships }: SponsorshipPanelProps) {
  return (
    <div className="bg-gray-800/50 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Sponsorship History</h4>
        {sponsorships.length > 0 && (
          <span className="text-xs bg-brand-500/20 text-brand-400 px-1.5 py-0.5 rounded-full font-medium">
            {sponsorships.length}
          </span>
        )}
      </div>

      {sponsorships.length === 0 ? (
        <p className="text-xs text-gray-600">No sponsored content detected</p>
      ) : (
        <div className="space-y-2">
          {sponsorships.map((s) => (
            <div key={s.post_id} className="flex gap-2 items-start">
              {s.thumbnail_url ? (
                <img
                  src={proxyImage(s.thumbnail_url)}
                  alt=""
                  className="w-10 h-10 rounded object-cover shrink-0 bg-gray-700"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                />
              ) : (
                <div className="w-10 h-10 rounded bg-gray-700 shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                {s.caption_snippet && (
                  <p className="text-xs text-gray-400 line-clamp-1 mb-1">{s.caption_snippet}</p>
                )}
                <div className="flex flex-wrap gap-1">
                  {s.matched_tags.map((t) => (
                    <span key={t} className="text-[10px] bg-yellow-500/15 text-yellow-400 px-1.5 py-0.5 rounded font-medium">
                      {t}
                    </span>
                  ))}
                  {s.matched_brands.map((b) => (
                    <span key={b} className="text-[10px] bg-brand-500/15 text-brand-400 px-1.5 py-0.5 rounded font-medium">
                      {b}
                    </span>
                  ))}
                </div>
              </div>
              {s.post_url && (
                <a
                  href={s.post_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-600 hover:text-gray-400 shrink-0 mt-0.5"
                >
                  <ExternalLink size={11} />
                </a>
              )}
            </div>
          ))}
        </div>
      )}

      <p className="mt-3 text-[10px] text-gray-600 flex items-center gap-1">
        <Info size={9} />
        Detected from post captions · Official Meta Branded Content API not available without approved credentials
      </p>
    </div>
  )
}
