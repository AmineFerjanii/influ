const NICHE_COLORS: Record<string, string> = {
  'Fashion': 'bg-pink-900/50 text-pink-300 border-pink-800',
  'Beauty': 'bg-purple-900/50 text-purple-300 border-purple-800',
  'Food & Beverage': 'bg-orange-900/50 text-orange-300 border-orange-800',
  'Travel': 'bg-sky-900/50 text-sky-300 border-sky-800',
  'Fitness': 'bg-green-900/50 text-green-300 border-green-800',
  'Lifestyle': 'bg-yellow-900/50 text-yellow-300 border-yellow-800',
  'Tech': 'bg-cyan-900/50 text-cyan-300 border-cyan-800',
  'Business': 'bg-blue-900/50 text-blue-300 border-blue-800',
  'Art & Culture': 'bg-rose-900/50 text-rose-300 border-rose-800',
  'Entertainment': 'bg-fuchsia-900/50 text-fuchsia-300 border-fuchsia-800',
  'Education': 'bg-teal-900/50 text-teal-300 border-teal-800',
  'Environment': 'bg-emerald-900/50 text-emerald-300 border-emerald-800',
}

const DEFAULT_COLOR = 'bg-gray-800 text-gray-300 border-gray-700'

interface NicheTagListProps {
  niches: string[]
  size?: 'sm' | 'xs'
}

export function NicheTagList({ niches, size = 'sm' }: NicheTagListProps) {
  if (niches.length === 0) return null
  const textSize = size === 'xs' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-1'

  return (
    <div className="flex flex-wrap gap-1">
      {niches.map((niche) => (
        <span
          key={niche}
          className={`${textSize} rounded-md border font-medium ${NICHE_COLORS[niche] ?? DEFAULT_COLOR}`}
        >
          {niche}
        </span>
      ))}
    </div>
  )
}
