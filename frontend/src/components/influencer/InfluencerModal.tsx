import * as Dialog from '@radix-ui/react-dialog'
import { X, RefreshCw, ExternalLink, User, AlertCircle, Info } from 'lucide-react'
import type { InfluencerDetail } from '@/types'
import { formatNumber, formatEngagementRate, erColor, erLabel, timeAgo, proxyImage } from '@/utils/formatters'
import { PlatformBadge, VerifiedBadge } from '@/components/common/Badge'
import { KPIBadge } from '@/components/common/KPIBadge'
import { PostGrid } from './PostGrid'
import { HashtagMentionPanel } from './HashtagMentionPanel'
import { NicheTagList } from './NicheTagList'
import { LinkedAccountPanel } from './LinkedAccountPanel'
import { SponsorshipPanel } from './SponsorshipPanel'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

interface InfluencerModalProps {
  influencer: InfluencerDetail | undefined
  isLoading: boolean
  open: boolean
  onClose: () => void
  onRefresh: () => void
  isScraping: boolean
}

export function InfluencerModal({
  influencer,
  isLoading,
  open,
  onClose,
  onRefresh,
  isScraping,
}: InfluencerModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 animate-in fade-in" />
        <Dialog.Content
          className="fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl max-h-[90vh] overflow-y-auto scrollbar-thin bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl animate-in fade-in zoom-in-95"
          aria-describedby="influencer-detail"
        >
          {/* Close */}
          <Dialog.Close className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors z-10">
            <X size={16} />
          </Dialog.Close>

          {isLoading ? (
            <div className="flex items-center justify-center h-48">
              <LoadingSpinner size="lg" />
            </div>
          ) : influencer ? (
            <div id="influencer-detail">
              {/* Header */}
              <div className="p-6 pb-4 border-b border-gray-800">
                <div className="flex items-start gap-4">
                  {influencer.profile_pic_url ? (
                    <img
                      src={proxyImage(influencer.profile_pic_url)}
                      alt={influencer.username}
                      className="w-16 h-16 rounded-full object-cover bg-gray-800 shrink-0"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center shrink-0">
                      <User size={28} className="text-gray-600" />
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-0.5">
                      <Dialog.Title className="text-lg font-bold text-white">
                        {influencer.display_name || influencer.username}
                      </Dialog.Title>
                      {influencer.is_verified && <VerifiedBadge />}
                      <PlatformBadge platform={influencer.platform} />
                    </div>
                    <a
                      href={
                        influencer.platform === 'instagram'
                          ? `https://www.instagram.com/${influencer.username}/`
                          : `https://www.tiktok.com/@${influencer.username}`
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-gray-400 hover:text-gray-200 flex items-center gap-1 w-fit"
                    >
                      @{influencer.username}
                      <ExternalLink size={11} />
                    </a>
                    {influencer.bio && (
                      <p className="text-sm text-gray-400 mt-2 line-clamp-2">{influencer.bio}</p>
                    )}
                  </div>

                  <button
                    onClick={onRefresh}
                    disabled={isScraping}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors disabled:opacity-50"
                  >
                    <RefreshCw size={13} className={isScraping ? 'animate-spin' : ''} />
                    {isScraping ? 'Scraping…' : 'Refresh'}
                  </button>
                </div>

                <LinkedAccountPanel
                  influencerId={influencer.id}
                  platform={influencer.platform}
                  linkedInfluencer={influencer.linked_influencer ?? null}
                />

                <div className="mt-3 flex items-center gap-3 text-xs text-gray-500">
                  <span>Last scraped: {timeAgo(influencer.last_scraped_at)}</span>
                  {influencer.scrape_status === 'error' && (
                    <span className="flex items-center gap-1 text-red-400">
                      <AlertCircle size={11} />
                      {influencer.scrape_error?.slice(0, 80)}
                    </span>
                  )}
                </div>
              </div>

              {/* KPI Row */}
              <div className="p-6 pb-4">
                <div className="flex flex-wrap gap-2">
                  <KPIBadge label="Followers" value={formatNumber(influencer.followers)} />
                  <KPIBadge label="Avg. Likes" value={formatNumber(Math.round(influencer.avg_likes))} />
                  <KPIBadge
                    label="Avg. Comments"
                    value={influencer.has_comments_data ? formatNumber(Math.round(influencer.avg_comments)) : 'N/A'}
                    sub={!influencer.has_comments_data ? 'not available' : undefined}
                  />
                  <KPIBadge
                    label="Engagement"
                    value={formatEngagementRate(influencer.engagement_rate)}
                    sub={erLabel(influencer.engagement_rate)}
                    colorClass={erColor(influencer.engagement_rate).split(' ')[0]}
                  />
                  <KPIBadge
                    label="Total Posts"
                    value={formatNumber(influencer.total_posts)}
                  />
                  <KPIBadge
                    label="Posts/Week"
                    value={influencer.posts_per_week > 0 ? influencer.posts_per_week.toFixed(1) : '—'}
                  />
                  <KPIBadge label="Following" value={formatNumber(influencer.following)} />
                </div>

                {!influencer.has_comments_data && (
                  <p className="mt-2 text-xs text-gray-500 flex items-center gap-1">
                    <Info size={11} />
                    Engagement rate calculated from likes only (comment data not available for this platform)
                  </p>
                )}
              </div>

              {/* Popular Posts */}
              <div className="px-6 pb-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Popular Posts</h3>
                <PostGrid posts={influencer.posts} />
              </div>

              {/* Estimated Performance */}
              <div className="px-6 pb-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Estimated Performance</h3>
                <div className="flex flex-wrap gap-2 mb-2">
                  <KPIBadge label="Est. Reach" value={formatNumber(Math.round(influencer.estimated_reach))} />
                  <KPIBadge label="Est. Impressions" value={formatNumber(Math.round(influencer.estimated_impressions))} />
                  <KPIBadge label="Photos" value={String(influencer.photo_count)} />
                  <KPIBadge label="Videos / Reels" value={String(influencer.video_count)} />
                </div>
                <p className="text-[11px] text-gray-600 flex items-center gap-1">
                  <Info size={10} />
                  Reach and impressions are estimates (followers × 0.35 / 0.50). Actual figures require platform API access.
                </p>
              </div>

              {/* Creator Intelligence */}
              <div className="px-6 pb-6">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Creator Intelligence</h3>
                <div className="grid grid-cols-2 gap-3">
                  <HashtagMentionPanel
                    title="Popular Hashtags"
                    items={influencer.top_hashtags.map((h) => ({ label: h.tag, count: h.count }))}
                  />
                  <HashtagMentionPanel
                    title="Popular Mentions"
                    items={influencer.top_mentions.map((m) => ({ label: m.mention, count: m.count }))}
                  />
                  <div className="bg-gray-800/50 rounded-xl p-4">
                    <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Creator Interests</h4>
                    {influencer.inferred_niches.length > 0 ? (
                      <NicheTagList niches={influencer.inferred_niches} />
                    ) : (
                      <p className="text-xs text-gray-600">Could not infer niches</p>
                    )}
                  </div>
                  <SponsorshipPanel sponsorships={influencer.detected_sponsorships ?? []} />
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-500">
              Could not load influencer data
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
