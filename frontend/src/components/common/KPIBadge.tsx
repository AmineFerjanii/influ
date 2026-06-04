import { clsx } from 'clsx'

interface KPIBadgeProps {
  label: string
  value: string
  sub?: string
  colorClass?: string
}

export function KPIBadge({ label, value, sub, colorClass }: KPIBadgeProps) {
  return (
    <div className="flex flex-col gap-0.5 px-4 py-3 bg-gray-800/60 rounded-xl min-w-[90px]">
      <span className="text-xs text-gray-400 uppercase tracking-wide font-medium">{label}</span>
      <span className={clsx('text-xl font-bold', colorClass ?? 'text-white')}>{value}</span>
      {sub && <span className="text-xs text-gray-500">{sub}</span>}
    </div>
  )
}
