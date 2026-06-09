import { clsx } from 'clsx'

interface KPIBadgeProps {
  label: string
  value: string
  sub?: string
  colorClass?: string
}

export function KPIBadge({ label, value, sub, colorClass }: KPIBadgeProps) {
  return (
    <div className="flex flex-col gap-0.5 px-4 py-3 bg-ealan-bg border border-ealan-border rounded-xl min-w-[88px]">
      <span className="section-label">{label}</span>
      <span className={clsx('text-xl font-bold tracking-tight', colorClass ?? 'text-white')}>{value}</span>
      {sub && <span className="text-[11px] text-ealan-muted">{sub}</span>}
    </div>
  )
}
