import { RefreshCw, Trash2, User } from 'lucide-react'
import { clsx } from 'clsx'
import type { Influencer } from '@/types'
import { formatNumber, formatEngagementRate, erColor, timeAgo, proxyImage } from '@/utils/formatters'
import { PlatformBadge, VerifiedBadge } from '@/components/common/Badge'
import { NicheTagList } from './NicheTagList'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

interface InfluencerCardProps {
  influencer: Influencer
  onClick: () => void
  onRefresh: () => void
  onDelete: () => void
  isScraping: boolean
}

export function InfluencerCard({ influencer, onClick, onRefresh, onDelete, isScraping }: InfluencerCardProps) {
  const isLoading = isScraping || influencer.scrape_status === 'scraping'
  const hasData = influencer.scrape_status === 'success' || influencer.followers > 0

  return (
    <div
      className="card-interactive group flex flex-col p-4 gap-3.5"
      onClick={onClick}
    >
      {/* Header: avatar + info + actions */}
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="relative shrink-0">
          <div className="w-11 h-11 rounded-full ring-1 ring-ealan-border overflow-hidden bg-ealan-hover flex items-center justify-center">
            {influencer.profile_pic_url ? (
              <img
                src={proxyImage(influencer.profile_pic_url)}
                alt={influencer.username}
                className="w-full h-full object-cover"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
              />
            ) : (
              <User size={18} className="text-gray-600" />
            )}
          </div>
          {isLoading && (
            <div className="absolute inset-0 bg-ealan-bg/75 rounded-full flex items-center justify-center">
              <LoadingSpinner size="sm" />
            </div>
          )}
        </div>

        {/* Name / handle / badges */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1 min-w-0">
            <span className="font-semibold text-sm text-white truncate leading-tight">
              {influencer.display_name || influencer.username}
            </span>
            {influencer.is_verified && <VerifiedBadge />}
          </div>
          <p className="text-[11px] text-ealan-muted truncate">@{influencer.username}</p>
          <div className="mt-1.5 flex items-center gap-1 flex-wrap">
            <PlatformBadge platform={influencer.platform} />
            {influencer.inferred_niches?.length > 0 && (
              <NicheTagList niches={influencer.inferred_niches} size="xs" max={1} />
            )}
          </div>
        </div>

        {/* Actions */}
        <div
          className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-1.5 rounded-lg hover:bg-ealan-hover text-gray-600 hover:text-gray-300 transition-colors disabled:opacity-30"
            title="Re-scrape"
          >
            <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={onDelete}
            className="p-1.5 rounded-lg hover:bg-red-950/50 text-gray-600 hover:text-red-400 transition-colors"
            title="Delete"
          >
            <Trash2 size={12} />
          </button>
        </div>
      </div>

      {/* KPIs */}
      {hasData ? (
        <div className="grid grid-cols-3 gap-2 pt-0.5">
          <div>
            <p className="text-[10px] text-ealan-muted mb-0.5">Followers</p>
            <p className="text-sm font-bold text-white">{formatNumber(influencer.followers)}</p>
          </div>
          <div>
            <p className="text-[10px] text-ealan-muted mb-0.5">Avg Likes</p>
            <p className="text-sm font-bold text-white">{formatNumber(Math.round(influencer.avg_likes))}</p>
          </div>
          <div>
            <p className="text-[10px] text-ealan-muted mb-0.5">Eng. Rate</p>
            <p className={clsx('text-sm font-bold', erColor(influencer.engagement_rate).split(' ')[0])}>
              {formatEngagementRate(influencer.engagement_rate)}
            </p>
          </div>
        </div>
      ) : (
        <p className={clsx('text-xs italic', influencer.scrape_status === 'error' ? 'text-red-400/80' : 'text-gray-600')}>
          {influencer.scrape_status === 'error'
            ? influencer.scrape_error?.slice(0, 55) + '…'
            : isLoading ? 'Scraping profile…' : 'Not yet scraped'}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-ealan-border/60 text-[11px] text-gray-600">
        <span>{influencer.total_posts > 0 ? `${formatNumber(influencer.total_posts)} posts` : ''}</span>
        <span>{timeAgo(influencer.last_scraped_at)}</span>
      </div>
    </div>
  )
}
