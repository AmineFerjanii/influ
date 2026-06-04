import { clsx } from 'clsx'
import { Instagram, Music2, BadgeCheck } from 'lucide-react'
import type { Platform } from '@/types'

export function PlatformBadge({ platform }: { platform: Platform }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
        platform === 'instagram'
          ? 'bg-pink-500/15 text-pink-400'
          : 'bg-cyan-500/15 text-cyan-400'
      )}
    >
      {platform === 'instagram' ? (
        <Instagram size={10} />
      ) : (
        <Music2 size={10} />
      )}
      {platform === 'instagram' ? 'Instagram' : 'TikTok'}
    </span>
  )
}

export function VerifiedBadge() {
  return <BadgeCheck size={14} className="text-blue-400 inline-block ml-0.5" />
}
