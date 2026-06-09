import { Users } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description?: string
  action?: React.ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-6 gap-5 text-center">
      <div className="w-16 h-16 rounded-2xl bg-ealan-card border border-ealan-border flex items-center justify-center">
        <Users size={28} className="text-ealan-muted" />
      </div>
      <div className="max-w-xs">
        <p className="text-gray-200 font-semibold text-base">{title}</p>
        {description && <p className="text-ealan-muted text-sm mt-1.5 leading-relaxed">{description}</p>}
      </div>
      {action}
    </div>
  )
}
