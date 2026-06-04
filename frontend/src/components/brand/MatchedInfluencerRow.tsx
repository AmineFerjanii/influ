import { User, Plus, Check } from 'lucide-react'
import { clsx } from 'clsx'
import type { MatchResult, CollabStatus } from '@/types'
import { formatNumber, formatEngagementRate, proxyImage } from '@/utils/formatters'
import { PlatformBadge } from '@/components/common/Badge'

const COLLAB_LABELS: Record<CollabStatus, string> = {
  potential: 'Potential',
  contacted: 'Contacted',
  in_progress: 'In Progress',
  done: 'Done',
}

const COLLAB_COLORS: Record<CollabStatus, string> = {
  potential: 'bg-gray-700 text-gray-300',
  contacted: 'bg-blue-500/20 text-blue-400',
  in_progress: 'bg-yellow-500/20 text-yellow-400',
  done: 'bg-green-500/20 text-green-400',
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 70 ? 'bg-green-500' :
    score >= 40 ? 'bg-yellow-500' :
    'bg-gray-600'

  return (
    <div className="flex items-center gap-2 min-w-0">
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all', color)} style={{ width: `${score}%` }} />
      </div>
      <span className={clsx('text-xs font-bold shrink-0',
        score >= 70 ? 'text-green-400' : score >= 40 ? 'text-yellow-400' : 'text-gray-500'
      )}>
        {score}
      </span>
    </div>
  )
}

interface MatchedInfluencerRowProps {
  match: MatchResult
  onAddToPipeline: (influencerId: number) => void
  isAdding: boolean
}

export function MatchedInfluencerRow({ match, onAddToPipeline, isAdding }: MatchedInfluencerRowProps) {
  const inPipeline = match.collaboration !== null

  return (
    <div className="flex items-center gap-3 py-3 border-b border-gray-800 last:border-0">
      {/* Avatar */}
      <div className="shrink-0">
        {match.profile_pic_url ? (
          <img
            src={proxyImage(match.profile_pic_url)}
            alt={match.username}
            className="w-9 h-9 rounded-full object-cover bg-gray-800"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        ) : (
          <div className="w-9 h-9 rounded-full bg-gray-800 flex items-center justify-center">
            <User size={16} className="text-gray-600" />
          </div>
        )}
      </div>

      {/* Name + platform + KPIs */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-sm font-semibold text-white truncate">
            {match.display_name || match.username}
          </span>
          <PlatformBadge platform={match.platform} />
        </div>
        <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-500">
          <span>{formatNumber(match.followers)} followers</span>
          <span>·</span>
          <span>ER {formatEngagementRate(match.engagement_rate)}</span>
        </div>
        {match.match_reasons.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {match.match_reasons.map((r) => (
              <span key={r} className="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">
                {r}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Score bar */}
      <div className="w-24 shrink-0">
        <ScoreBar score={match.match_score} />
      </div>

      {/* Pipeline status / add button */}
      <div className="shrink-0">
        {inPipeline ? (
          <span className={clsx(
            'text-xs px-2 py-1 rounded-full font-medium',
            COLLAB_COLORS[match.collaboration!.status as CollabStatus]
          )}>
            {COLLAB_LABELS[match.collaboration!.status as CollabStatus]}
          </span>
        ) : (
          <button
            onClick={() => onAddToPipeline(match.id)}
            disabled={isAdding}
            className="flex items-center gap-1 text-xs bg-gray-800 hover:bg-brand-500/20 hover:text-brand-400 text-gray-400 px-2 py-1 rounded-lg transition-colors disabled:opacity-40"
          >
            <Plus size={11} />
            Add
          </button>
        )}
      </div>
    </div>
  )
}
