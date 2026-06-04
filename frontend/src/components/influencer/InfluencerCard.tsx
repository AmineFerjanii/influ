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

export function InfluencerCard({
  influencer,
  onClick,
  onRefresh,
  onDelete,
  isScraping,
}: InfluencerCardProps) {
  const isLoading = isScraping || influencer.scrape_status === 'scraping'

  return (
    <div
      className="bg-ealan-card border border-ealan-border rounded-2xl p-4 hover:border-brand-500/40 transition-all cursor-pointer group flex flex-col gap-3"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="relative shrink-0">
          {influencer.profile_pic_url ? (
            <img
              src={proxyImage(influencer.profile_pic_url)}
              alt={influencer.username}
              className="w-11 h-11 rounded-full object-cover bg-gray-800"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          ) : (
            <div className="w-11 h-11 rounded-full bg-ealan-hover flex items-center justify-center">
              <User size={20} className="text-gray-600" />
            </div>
          )}
          {isLoading && (
            <div className="absolute inset-0 bg-gray-900/70 rounded-full flex items-center justify-center">
              <LoadingSpinner size="sm" />
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1 flex-wrap">
            <span className="font-semibold text-sm text-white truncate">
              {influencer.display_name || influencer.username}
            </span>
            {influencer.is_verified && <VerifiedBadge />}
          </div>
          <span className="text-xs text-gray-500">@{influencer.username}</span>
          <div className="mt-1 flex items-center gap-1.5 flex-wrap">
            <PlatformBadge platform={influencer.platform} />
            {influencer.inferred_niches?.length > 0 && (
              <NicheTagList niches={influencer.inferred_niches} size="xs" />
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div
          className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-1.5 rounded-lg hover:bg-ealan-hover text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-40"
            title="Re-scrape"
          >
            <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={onDelete}
            className="p-1.5 rounded-lg hover:bg-red-900/40 text-gray-500 hover:text-red-400 transition-colors"
            title="Delete"
          >
            <Trash2 size={13} />
          </button>
        </div>
      </div>

      {/* KPIs */}
      {influencer.scrape_status === 'success' || influencer.followers > 0 ? (
        <div className="grid grid-cols-3 gap-2">
          <div className="flex flex-col">
            <span className="text-xs text-gray-500">Followers</span>
            <span className="text-sm font-bold text-white">{formatNumber(influencer.followers)}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-gray-500">Avg. Likes</span>
            <span className="text-sm font-bold text-white">{formatNumber(Math.round(influencer.avg_likes))}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-gray-500">Eng. Rate</span>
            <span className={clsx('text-sm font-bold', erColor(influencer.engagement_rate).split(' ')[0])}>
              {formatEngagementRate(influencer.engagement_rate)}
            </span>
          </div>
        </div>
      ) : (
        <div className="text-xs text-gray-600 italic">
          {influencer.scrape_status === 'error'
            ? `Error: ${influencer.scrape_error?.slice(0, 60)}`
            : isLoading
            ? 'Scraping profile…'
            : 'Not yet scraped'}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-600 border-t border-ealan-border pt-2">
        <span>{influencer.total_posts > 0 ? `${formatNumber(influencer.total_posts)} posts` : ''}</span>
        <span>{timeAgo(influencer.last_scraped_at)}</span>
      </div>
    </div>
  )
}
